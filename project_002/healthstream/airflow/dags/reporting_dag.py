# Run every Monday at 06:00 UTC to print a weekly summary to the Airflow logs.
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
    dag_id="healthstream_reporting",
    default_args=default_args,
    description="Weekly KPI reporting for Healthstream",
    schedule_interval="0 6 * * 1",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["healthstream", "reporting"],
)


def generate_weekly_report(**context):
    hook = PostgresHook(postgres_conn_id="healthstream_postgres")

    totals = hook.get_records("""
        SELECT
            SUM(total_claims),
            SUM(total_amount),
            SUM(fraud_detected),
            AVG(avg_claim_amount)
        FROM analytics_summary
        WHERE summary_date >= CURRENT_DATE - INTERVAL '7 days';
    """)

    top_hospitals = hook.get_records("""
        SELECT h.hospital_name, COUNT(*) AS claim_count, SUM(c.claim_amount) AS total
        FROM claims c
        JOIN hospitals h ON c.hospital_id = h.hospital_id
        WHERE c.claim_date >= NOW() - INTERVAL '7 days'
        GROUP BY h.hospital_name
        ORDER BY claim_count DESC
        LIMIT 5;
    """)

    high_risk = hook.get_records("""
        SELECT COUNT(*) FROM patients WHERE risk_score > 0.7;
    """)

    print("=" * 60)
    print("HEALTHSTREAM WEEKLY REPORT")
    print("=" * 60)
    if totals and totals[0][0]:
        t = totals[0]
        print(f"Total Claims:   {t[0]:,}")
        print(f"Total Amount:   ${t[1]:,.2f}")
        print(f"Fraud Detected: {t[2]:,}")
        print(f"Avg Claim:      ${t[3]:,.2f}")
    print("\nTop 5 Hospitals:")
    for h in top_hospitals:
        print(f"  {h[0]}: {h[1]} claims, ${h[2]:,.2f}")
    print(f"\nHigh-Risk Patients: {high_risk[0][0] if high_risk else 0}")
    print("=" * 60)


weekly_report = PythonOperator(
    task_id="generate_weekly_report",
    python_callable=generate_weekly_report,
    dag=dag,
)
