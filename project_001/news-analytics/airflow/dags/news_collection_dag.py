# This file is defining the Airflow DAG that runs the news collection pipeline
# every 30 minutes. It has three tasks that run in order. The first task fetches
# articles from NewsAPI and Hacker News and stores them in MongoDB. The second task
# loads those articles, runs ML on them, and stores the results in PostgreSQL. The
# third task publishes the articles to Kafka for the Spark streaming job to process.

import logging
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator

logger = logging.getLogger(__name__)

DEFAULT_ARGS = {
    "owner": "data-engineering",
    "depends_on_past": False,
    "start_date": datetime(2024, 1, 1),
    "retries": 1,
    "retry_delay": timedelta(minutes=2),
    "email_on_failure": False,
}


def _safe_str(value) -> str:
    # Converting any value to a string safely so None fields in articles never
    # cause a TypeError during text processing in the ML components.
    if value is None:
        return ""
    return str(value)


def collect_news(**context) -> None:
    # Fetching articles from NewsAPI and Hacker News using the NewsCollector.
    # Storing each raw article in MongoDB and pushing only the article IDs to
    # XCom so the payload stays small and within Airflow's size limit.
    import sys
    sys.path.insert(0, "/opt/airflow/project")

    from scraper.collector import NewsCollector
    from api.database.mongo import insert_raw_article

    collector = NewsCollector()
    articles = collector.collect()
    logger.info("Collection task fetched %d articles", len(articles))

    for article in articles:
        insert_raw_article(article)

    article_ids = [a["id"] for a in articles if a.get("id")]
    context["ti"].xcom_push(key="article_ids", value=article_ids)
    logger.info("Pushed %d article IDs to XCom", len(article_ids))


def run_ml_pipeline(**context) -> None:
    # Pulling article IDs from XCom, loading the full article documents from
    # MongoDB, sanitizing all text fields so None values do not crash the ML
    # components, running sentiment analysis and keyword extraction on each
    # article, and storing the enriched results in PostgreSQL.
    import sys
    sys.path.insert(0, "/opt/airflow/project")

    from ml.sentiment import SentimentAnalyzer
    from ml.keywords import KeywordExtractor
    from ml.clustering import ArticleClusterer
    from ml.trends import TrendDetector
    from api.database.postgres import insert_article, init_schema
    from api.database.mongo import get_collection

    article_ids = context["ti"].xcom_pull(key="article_ids", task_ids="collect_news")
    if not article_ids:
        logger.warning("No article IDs received from XCom, skipping ML pipeline")
        return

    col = get_collection("raw_articles")
    articles = list(col.find({"id": {"$in": article_ids}}, {"_id": 0}))
    logger.info("Loaded %d articles from MongoDB for ML processing", len(articles))

    if not articles:
        logger.warning("No articles found in MongoDB, skipping ML pipeline")
        return

    # Sanitizing all text fields before passing to ML components so None values
    # never cause a TypeError in string join or regex operations.
    for article in articles:
        article["title"] = _safe_str(article.get("title"))
        article["description"] = _safe_str(article.get("description"))
        article["content"] = _safe_str(article.get("content"))
        article["author"] = _safe_str(article.get("author"))
        article["source_name"] = _safe_str(article.get("source_name"))

    sentiment_analyzer = SentimentAnalyzer()
    keyword_extractor = KeywordExtractor(top_n=10)
    clusterer = ArticleClusterer(n_clusters=min(8, len(articles)))
    trend_detector = TrendDetector(window_minutes=60)

    enriched = []
    for article in articles:
        try:
            article = sentiment_analyzer.analyze_article(article)
            article = keyword_extractor.extract_from_article(article)
            trend_detector.ingest(article.get("keywords", []))
            enriched.append(article)
        except Exception as exc:
            logger.error("ML processing failing for article %s: %s", article.get("id"), exc)
            enriched.append(article)

    # Fitting the clusterer only when we have enough articles to fill all clusters.
    if len(enriched) >= 8:
        try:
            clusterer.fit(enriched)
            labels = clusterer.predict(enriched)
            for i, label in enumerate(labels):
                enriched[i]["cluster"] = label
        except Exception as exc:
            logger.error("Clustering failing: %s", exc)

    init_schema()
    inserted = 0
    for article in enriched:
        try:
            insert_article(article)
            inserted += 1
        except Exception as exc:
            logger.error("Inserting article %s failing: %s", article.get("id"), exc)

    logger.info("ML pipeline stored %d/%d articles in PostgreSQL", inserted, len(enriched))


def publish_to_kafka(**context) -> None:
    # Pulling article IDs from XCom, loading the full articles from MongoDB,
    # and publishing them to the Kafka raw-news topic so the Spark streaming
    # job can process them in near real time.
    import sys
    import json
    sys.path.insert(0, "/opt/airflow/project")

    from api.database.mongo import get_collection

    article_ids = context["ti"].xcom_pull(key="article_ids", task_ids="collect_news")
    if not article_ids:
        logger.warning("No article IDs received from XCom, skipping Kafka publish")
        return

    col = get_collection("raw_articles")
    articles = list(col.find({"id": {"$in": article_ids}}, {"_id": 0}))

    try:
        from kafka import KafkaProducer as _KafkaProducer
        producer = _KafkaProducer(
            bootstrap_servers="kafka:9092",
            value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
            key_serializer=lambda k: k.encode("utf-8") if k else None,
            retries=3,
        )
        for article in articles:
            producer.send("raw-news", key=article.get("id", ""), value=article)
        producer.flush()
        producer.close()
        logger.info("Published %d articles to Kafka", len(articles))
    except Exception as exc:
        logger.error("Kafka publish failing: %s", exc)
        raise


with DAG(
    dag_id="news_collection_pipeline",
    default_args=DEFAULT_ARGS,
    description="Collecting news from NewsAPI and Hacker News every 30 minutes",
    schedule_interval="*/30 * * * *",
    catchup=False,
    tags=["news", "collection"],
) as dag:

    task_collect = PythonOperator(
        task_id="collect_news",
        python_callable=collect_news,
    )

    task_ml = PythonOperator(
        task_id="run_ml_pipeline",
        python_callable=run_ml_pipeline,
    )

    task_kafka = PythonOperator(
        task_id="publish_to_kafka",
        python_callable=publish_to_kafka,
    )

    # collect_news runs first, then run_ml_pipeline and publish_to_kafka run
    # in parallel since they are independent of each other.
    task_collect >> [task_ml, task_kafka]
