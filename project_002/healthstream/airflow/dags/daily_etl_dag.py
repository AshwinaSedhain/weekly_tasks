# Run every day at 01:00 UTC to refresh analytics, update risk scores, and resolve old alerts.
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook

default_args = {
    "owner":            "healthstream",
    "depends_on_past":  False,
    "email_on_failure": False,
    "email_on_retry":   False,
    "retries":          2,
    "retry_delay":      timedelta(minutes=5),
}

dag = DAG(
    dag_id="healthstream_daily_etl",
    default_args=default_args,
    description="Daily ETL pipeline for Healthstream",
    schedule_interval="0 1 * * *",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["healthstream", "etl", "daily"],
)

refresh_analytics = SQLExecuteQueryOperator(
    task_id="refresh_analytics_summary",
    conn_id="healthstream_postgres",
    sql="""
        INSERT INTO analytics_summary
            (summary_date, total_claims, total_amount, approved_claims,
             denied_claims, fraud_detected, avg_claim_amount)
        SELECT
            DATE(claim_date),
            COUNT(*),
            COALESCE(SUM(claim_amount), 0),
            SUM(CASE WHEN insurance_status = 'APPROVED' THEN 1 ELSE 0 END),
            SUM(CASE WHEN insurance_status = 'DENIED'   THEN 1 ELSE 0 END),
            SUM(CASE WHEN is_fraud THEN 1 ELSE 0 END),
            COALESCE(AVG(claim_amount), 0)
        FROM claims
        WHERE DATE(claim_date) = CURRENT_DATE - INTERVAL '1 day'
        GROUP BY DATE(claim_date)
        ON CONFLICT (summary_date) DO UPDATE SET
            total_claims     = EXCLUDED.total_claims,
            total_amount     = EXCLUDED.total_amount,
            approved_claims  = EXCLUDED.approved_claims,
            denied_claims    = EXCLUDED.denied_claims,
            fraud_detected   = EXCLUDED.fraud_detected,
            avg_claim_amount = EXCLUDED.avg_claim_amount;
    """,
    dag=dag,
)


def update_patient_risk_scores(**context):
    # Recalculate risk scores using claim frequency, fraud history, and claim size.
    hook = PostgresHook(postgres_conn_id="healthstream_postgres")
    conn = hook.get_conn()
    cur  = conn.cursor()
    cur.execute("""
        UPDATE patients p
        SET risk_score = sub.new_risk,
            updated_at = NOW()
        FROM (
            SELECT
                patient_id,
                LEAST(1.0,
                    (COUNT(*) * 0.01)
                    + (AVG(fraud_score) * 0.6)
                    + (CASE WHEN AVG(claim_amount) > 50000 THEN 0.3 ELSE 0 END)
                ) AS new_risk
            FROM claims
            WHERE claim_date >= NOW() - INTERVAL '30 days'
            GROUP BY patient_id
        ) sub
        WHERE p.patient_id = sub.patient_id;
    """)
    updated = cur.rowcount
    conn.commit()
    cur.close()
    conn.close()
    print(f"Updated risk scores for {updated} patients")
    return updated


update_risk = PythonOperator(
    task_id="update_patient_risk_scores",
    python_callable=update_patient_risk_scores,
    dag=dag,
)

update_hospital_perf = SQLExecuteQueryOperator(
    task_id="update_hospital_performance",
    conn_id="healthstream_postgres",
    sql="""
        UPDATE hospitals h
        SET performance_score = sub.perf_score
        FROM (
            SELECT
                hospital_id,
                LEAST(99.0, GREATEST(0.0,
                    100.0
                    - (SUM(CASE WHEN is_fraud THEN 1 ELSE 0 END)::FLOAT
                       / NULLIF(COUNT(*), 0) * 100)
                    - (SUM(CASE WHEN insurance_status = 'DENIED' THEN 1 ELSE 0 END)::FLOAT
                       / NULLIF(COUNT(*), 0) * 20)
                )) AS perf_score
            FROM claims
            WHERE claim_date >= NOW() - INTERVAL '30 days'
            GROUP BY hospital_id
        ) sub
        WHERE h.hospital_id = sub.hospital_id;
    """,
    dag=dag,
)

resolve_old_alerts = SQLExecuteQueryOperator(
    task_id="resolve_old_fraud_alerts",
    conn_id="healthstream_postgres",
    sql="""
        UPDATE fraud_alerts
        SET resolved    = TRUE,
            resolved_at = NOW()
        WHERE resolved = FALSE
          AND created_at < NOW() - INTERVAL '7 days'
          AND severity IN ('LOW', 'MEDIUM');
    """,
    dag=dag,
)


def log_daily_summary(**context):
    hook = PostgresHook(postgres_conn_id="healthstream_postgres")
    rows = hook.get_records("""
        SELECT summary_date, total_claims, total_amount, fraud_detected
        FROM analytics_summary
        ORDER BY summary_date DESC
        LIMIT 1;
    """)
    if rows:
        row = rows[0]
        print(f"Daily Summary [{row[0]}]: Claims={row[1]}, Amount=${row[2]:,.2f}, Fraud={row[3]}")
    return rows


log_summary = PythonOperator(
    task_id="log_daily_summary",
    python_callable=log_daily_summary,
    dag=dag,
)

refresh_analytics >> update_risk >> update_hospital_perf >> resolve_old_alerts >> log_summary
