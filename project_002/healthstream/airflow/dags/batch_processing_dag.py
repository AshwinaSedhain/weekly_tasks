# Run every 6 hours to process pending claims and flag fraudulent ones.
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook

default_args = {
    "owner":            "healthstream",
    "depends_on_past":  False,
    "email_on_failure": False,
    "retries":          1,
    "retry_delay":      timedelta(minutes=3),
}

dag = DAG(
    dag_id="healthstream_batch_processing",
    default_args=default_args,
    description="Batch claim processing and fraud detection",
    schedule_interval="0 */6 * * *",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["healthstream", "batch", "fraud"],
)

process_pending = SQLExecuteQueryOperator(
    task_id="process_pending_claims",
    conn_id="healthstream_postgres",
    sql="""
        UPDATE claims
        SET status         = 'PROCESSED',
            processed_date = NOW()
        WHERE status = 'PENDING'
          AND claim_date < NOW() - INTERVAL '1 hour';
    """,
    dag=dag,
)


def batch_fraud_detection(**context):
    # Apply two rules: high-amount anomalies and patient velocity checks.
    hook = PostgresHook(postgres_conn_id="healthstream_postgres")
    conn = hook.get_conn()
    cur  = conn.cursor()

    cur.execute("""
        INSERT INTO fraud_alerts
            (claim_id, patient_id, hospital_id, fraud_score,
             alert_reason, alert_type, severity)
        SELECT
            c.claim_id, c.patient_id, c.hospital_id,
            LEAST(0.99, c.claim_amount / NULLIF(t.avg_cost, 0) * 0.1),
            'Claim amount exceeds 3x treatment average',
            'HIGH_AMOUNT',
            CASE WHEN c.claim_amount > t.avg_cost * 5 THEN 'CRITICAL' ELSE 'HIGH' END
        FROM claims c
        JOIN treatments t ON c.treatment_code = t.treatment_code
        WHERE c.claim_amount > t.avg_cost * 3
          AND c.claim_date >= NOW() - INTERVAL '6 hours'
          AND NOT EXISTS (
              SELECT 1 FROM fraud_alerts fa WHERE fa.claim_id = c.claim_id
          )
        ON CONFLICT DO NOTHING;
    """)
    high_amount = cur.rowcount

    cur.execute("""
        INSERT INTO fraud_alerts
            (claim_id, patient_id, hospital_id, fraud_score,
             alert_reason, alert_type, severity)
        SELECT DISTINCT ON (c.claim_id)
            c.claim_id, c.patient_id, c.hospital_id,
            0.85,
            'Patient submitted more than 5 claims in 24 hours',
            'UNUSUAL_PATTERN',
            'HIGH'
        FROM claims c
        WHERE c.patient_id IN (
            SELECT patient_id
            FROM claims
            WHERE claim_date >= NOW() - INTERVAL '24 hours'
            GROUP BY patient_id
            HAVING COUNT(*) > 5
        )
        AND c.claim_date >= NOW() - INTERVAL '6 hours'
        AND NOT EXISTS (
            SELECT 1 FROM fraud_alerts fa WHERE fa.claim_id = c.claim_id
        )
        ON CONFLICT DO NOTHING;
    """)
    velocity = cur.rowcount

    conn.commit()
    cur.close()
    conn.close()
    print(f"Fraud detection: {high_amount} high-amount, {velocity} velocity alerts")
    return {"high_amount": high_amount, "velocity": velocity}


fraud_detection = PythonOperator(
    task_id="batch_fraud_detection",
    python_callable=batch_fraud_detection,
    dag=dag,
)

mark_fraud_claims = SQLExecuteQueryOperator(
    task_id="mark_fraud_claims",
    conn_id="healthstream_postgres",
    sql="""
        UPDATE claims c
        SET is_fraud = TRUE
        FROM fraud_alerts fa
        WHERE fa.claim_id = c.claim_id
          AND fa.severity IN ('HIGH', 'CRITICAL')
          AND fa.resolved = FALSE;
    """,
    dag=dag,
)

process_pending >> fraud_detection >> mark_fraud_claims
