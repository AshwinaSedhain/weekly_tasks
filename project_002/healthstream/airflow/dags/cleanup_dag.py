# Run every Sunday at 03:00 UTC to remove old resolved alerts and vacuum tables.
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook

default_args = {
    "owner":            "healthstream",
    "depends_on_past":  False,
    "email_on_failure": False,
    "retries":          1,
    "retry_delay":      timedelta(minutes=5),
}

dag = DAG(
    dag_id="healthstream_cleanup",
    default_args=default_args,
    description="Weekly cleanup of old resolved alerts and stale data",
    schedule_interval="0 3 * * 0",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["healthstream", "cleanup", "maintenance"],
)


def cleanup_old_fraud_alerts(**context):
    hook = PostgresHook(postgres_conn_id="healthstream_postgres")
    conn = hook.get_conn()
    cur  = conn.cursor()
    cur.execute("""
        DELETE FROM fraud_alerts
        WHERE resolved = TRUE
          AND resolved_at < NOW() - INTERVAL '90 days';
    """)
    deleted = cur.rowcount
    conn.commit()
    cur.close()
    conn.close()
    print(f"Deleted {deleted} old resolved fraud alerts")


def log_old_summaries(**context):
    hook = PostgresHook(postgres_conn_id="healthstream_postgres")
    rows = hook.get_records("""
        SELECT COUNT(*) FROM analytics_summary
        WHERE summary_date < CURRENT_DATE - INTERVAL '365 days';
    """)
    count = rows[0][0] if rows else 0
    print(f"Analytics summaries older than 1 year: {count}")


def vacuum_tables(**context):
    # VACUUM must run outside a transaction so we use autocommit directly.
    hook = PostgresHook(postgres_conn_id="healthstream_postgres")
    conn = hook.get_conn()
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute("VACUUM ANALYZE claims;")
    cur.execute("VACUUM ANALYZE fraud_alerts;")
    cur.close()
    conn.close()
    print("VACUUM ANALYZE complete")


cleanup_task = PythonOperator(
    task_id="cleanup_old_fraud_alerts",
    python_callable=cleanup_old_fraud_alerts,
    dag=dag,
)

log_task = PythonOperator(
    task_id="log_old_analytics_summaries",
    python_callable=log_old_summaries,
    dag=dag,
)

vacuum_task = PythonOperator(
    task_id="vacuum_analyze",
    python_callable=vacuum_tables,
    dag=dag,
)

cleanup_task >> log_task >> vacuum_task
