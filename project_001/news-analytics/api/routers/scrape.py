# This file is defining the /scrape endpoints. It is providing a route that triggers
# an on-demand collection cycle so operators can refresh the news feed without waiting
# for the next scheduled Airflow run. A debug endpoint is also provided that runs
# everything synchronously and returns detailed results for troubleshooting.

import json
import logging
import os

from fastapi import APIRouter, BackgroundTasks, HTTPException

logger = logging.getLogger(__name__)
router = APIRouter()

KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")


def _run_collection() -> None:
    # Running the full collection and ML pipeline in the background. Fetching
    # articles from both sources, storing raw documents in MongoDB, enriching
    # them with ML, storing results in PostgreSQL, and publishing to Kafka.
    try:
        from scraper.collector import NewsCollector
        from ml.pipeline import MLPipeline
        from api.database.postgres import insert_articles_batch, init_schema
        from api.database.mongo import insert_raw_article

        collector = NewsCollector()
        ml_pipeline = MLPipeline()

        articles = collector.collect()
        logger.info("On-demand collection fetched %d articles", len(articles))

        for article in articles:
            insert_raw_article(article)

        enriched = ml_pipeline.process(articles)
        logger.info("ML pipeline enriched %d articles", len(enriched))

        init_schema()
        inserted = insert_articles_batch(enriched)
        logger.info("Inserted %d articles into PostgreSQL", inserted)

        _publish_to_kafka(enriched)
        logger.info("On-demand collection completed successfully")

    except Exception as exc:
        logger.error("On-demand collection failing: %s", exc, exc_info=True)


def _publish_to_kafka(articles: list[dict]) -> None:
    # Publishing enriched articles to the Kafka raw-news topic. Importing
    # KafkaProducer directly from the installed package to avoid any local
    # module name conflicts with our kafka/ folder.
    try:
        from kafka import KafkaProducer as _KafkaProducer
        producer = _KafkaProducer(
            bootstrap_servers=KAFKA_BOOTSTRAP,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
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


@router.post("/run")
async def trigger_scrape(background_tasks: BackgroundTasks) -> dict:
    # Triggering an on-demand scraping and processing cycle in the background.
    # Returns immediately so the HTTP client does not have to wait for the
    # collection to finish.
    background_tasks.add_task(_run_collection)
    return {"status": "ok", "message": "Scraping job started in background"}


@router.post("/debug")
async def debug_scrape() -> dict:
    # Running the full pipeline synchronously and returning a detailed result
    # so errors are visible immediately in the HTTP response rather than being
    # hidden in background task logs. Useful for troubleshooting.
    result: dict = {
        "collection": 0,
        "mongo_inserted": 0,
        "ml_processed": 0,
        "postgres_inserted": 0,
        "errors": [],
    }

    try:
        from scraper.collector import NewsCollector
        collector = NewsCollector()
        articles = collector.collect()
        result["collection"] = len(articles)
    except Exception as exc:
        result["errors"].append(f"Collection failed: {exc}")
        raise HTTPException(status_code=500, detail=result)

    try:
        from api.database.mongo import insert_raw_article
        for article in articles:
            insert_raw_article(article)
        result["mongo_inserted"] = len(articles)
    except Exception as exc:
        result["errors"].append(f"MongoDB insert failed: {exc}")

    try:
        from ml.pipeline import MLPipeline
        pipeline = MLPipeline()
        enriched = pipeline.process(articles)
        result["ml_processed"] = len(enriched)
    except Exception as exc:
        result["errors"].append(f"ML pipeline failed: {exc}")
        enriched = articles

    try:
        from api.database.postgres import init_schema, insert_article
        init_schema()
        for article in enriched:
            try:
                insert_article(article)
                result["postgres_inserted"] += 1
            except Exception as exc:
                result["errors"].append(f"Insert failed for {article.get('id')}: {exc}")
    except Exception as exc:
        result["errors"].append(f"PostgreSQL insert failed: {str(exc)}")

    return result
