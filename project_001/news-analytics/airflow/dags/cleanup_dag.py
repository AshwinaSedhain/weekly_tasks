# This file is defining the Airflow DAG that runs a daily cleanup job at 2am.
# It removes articles older than 30 days from both PostgreSQL and MongoDB so the
# databases do not grow indefinitely and query performance stays consistent over time.

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
    "retry_delay": timedelta(minutes=10),
    "email_on_failure": False,
}


def cleanup_postgres(**context) -> None:
    # Deleting articles from PostgreSQL whose published_at date is older than
    # 30 days. Logging the number of rows deleted so operators can monitor how
    # much data is being removed each day.
    import sys
    sys.path.insert(0, "/opt/airflow/project")

    from api.database.postgres import get_pool

    pool = get_pool()
    conn = pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                DELETE FROM articles
                WHERE published_at < NOW() - INTERVAL '30 days';
            """)
            deleted = cur.rowcount
        conn.commit()
        logger.info("Deleted %d old articles from PostgreSQL", deleted)
    finally:
        pool.putconn(conn)


def cleanup_mongo(**context) -> None:
    # Deleting raw article documents from MongoDB whose published_at field is
    # older than 30 days. Running after the PostgreSQL cleanup so both databases
    # stay in sync.
    import sys
    sys.path.insert(0, "/opt/airflow/project")

    from api.database.mongo import get_collection
    from datetime import datetime, timedelta

    cutoff = (datetime.utcnow() - timedelta(days=30)).isoformat()
    col = get_collection("raw_articles")
    result = col.delete_many({"published_at": {"$lt": cutoff}})
    logger.info("Deleted %d old documents from MongoDB", result.deleted_count)


with DAG(
    dag_id="daily_cleanup",
    default_args=DEFAULT_ARGS,
    description="Removing articles older than 30 days from all databases",
    schedule_interval="0 2 * * *",
    catchup=False,
    tags=["cleanup", "maintenance"],
) as dag:

    task_pg_cleanup = PythonOperator(
        task_id="cleanup_postgres",
        python_callable=cleanup_postgres,
    )

    task_mongo_cleanup = PythonOperator(
        task_id="cleanup_mongo",
        python_callable=cleanup_mongo,
    )

    # PostgreSQL cleanup runs first then MongoDB cleanup runs after.
    task_pg_cleanup >> task_mongo_cleanup
