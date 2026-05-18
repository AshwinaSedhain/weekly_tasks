# Seed PostgreSQL with patients, hospitals, and 90 days of historical claims.
import logging
import time

import psycopg2
from psycopg2.extras import execute_values
from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
from generator import generate_patients, generate_hospitals, generate_historical_claims

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def get_connection(retries: int = 10, delay: int = 5):
    # Wait for the database to be ready before connecting.
    for attempt in range(retries):
        try:
            conn = psycopg2.connect(
                host=DB_HOST, port=DB_PORT, dbname=DB_NAME,
                user=DB_USER, password=DB_PASSWORD,
            )
            logger.info("Connected to PostgreSQL")
            return conn
        except psycopg2.OperationalError as exc:
            logger.warning("DB not ready (attempt %d/%d): %s", attempt + 1, retries, exc)
            time.sleep(delay)
    raise RuntimeError("Could not connect to PostgreSQL after retries")


def seed_patients(conn, patients):
    with conn.cursor() as cur:
        execute_values(
            cur,
            """
            INSERT INTO patients
                (patient_id, first_name, last_name, date_of_birth,
                 gender, state, insurance_type, risk_score)
            VALUES %s
            ON CONFLICT (patient_id) DO NOTHING
            """,
            [
                (
                    p["patient_id"], p["first_name"], p["last_name"],
                    p["date_of_birth"], p["gender"], p["state"],
                    p["insurance_type"], p["risk_score"],
                )
                for p in patients
            ],
        )
    conn.commit()
    logger.info("Seeded %d patients", len(patients))


def seed_hospitals(conn, hospitals):
    with conn.cursor() as cur:
        execute_values(
            cur,
            """
            INSERT INTO hospitals
                (hospital_id, hospital_name, state, hospital_type,
                 bed_count, accreditation, performance_score)
            VALUES %s
            ON CONFLICT (hospital_id) DO NOTHING
            """,
            [
                (
                    h["hospital_id"], h["hospital_name"], h["state"],
                    h["hospital_type"], h["bed_count"],
                    h["accreditation"], h["performance_score"],
                )
                for h in hospitals
            ],
        )
    conn.commit()
    logger.info("Seeded %d hospitals", len(hospitals))


def seed_claims(conn, claims):
    with conn.cursor() as cur:
        execute_values(
            cur,
            """
            INSERT INTO claims
                (claim_id, patient_id, hospital_id, treatment_code,
                 diagnosis_code, claim_amount, approved_amount,
                 insurance_status, claim_date, is_fraud, fraud_score, status)
            VALUES %s
            ON CONFLICT (claim_id) DO NOTHING
            """,
            [
                (
                    c["claim_id"], c["patient_id"], c["hospital_id"],
                    c["treatment_code"], c["diagnosis_code"],
                    c["claim_amount"], c["approved_amount"],
                    c["insurance_status"], c["claim_date"],
                    c["is_fraud"], c["fraud_score"], c["status"],
                )
                for c in claims
            ],
            page_size=500,
        )
    conn.commit()
    logger.info("Seeded %d claims", len(claims))


def seed_fraud_alerts(conn, claims):
    fraud_claims = [c for c in claims if c["is_fraud"]]
    if not fraud_claims:
        return
    with conn.cursor() as cur:
        execute_values(
            cur,
            """
            INSERT INTO fraud_alerts
                (claim_id, patient_id, hospital_id, fraud_score,
                 alert_reason, alert_type, severity)
            VALUES %s
            ON CONFLICT DO NOTHING
            """,
            [
                (
                    c["claim_id"], c["patient_id"], c["hospital_id"],
                    c["fraud_score"],
                    "Anomalous claim amount detected during historical seeding",
                    "HIGH_AMOUNT",
                    "HIGH" if c["fraud_score"] > 0.8 else "MEDIUM",
                )
                for c in fraud_claims
            ],
            page_size=500,
        )
    conn.commit()
    logger.info("Seeded %d fraud alerts", len(fraud_claims))


def refresh_analytics_summary(conn):
    # Aggregate claims by day and write to the analytics_summary table.
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO analytics_summary
                (summary_date, total_claims, total_amount, approved_claims,
                 denied_claims, fraud_detected, avg_claim_amount)
            SELECT
                DATE(claim_date),
                COUNT(*),
                SUM(claim_amount),
                SUM(CASE WHEN insurance_status = 'APPROVED' THEN 1 ELSE 0 END),
                SUM(CASE WHEN insurance_status = 'DENIED'   THEN 1 ELSE 0 END),
                SUM(CASE WHEN is_fraud THEN 1 ELSE 0 END),
                AVG(claim_amount)
            FROM claims
            GROUP BY DATE(claim_date)
            ON CONFLICT (summary_date) DO UPDATE SET
                total_claims     = EXCLUDED.total_claims,
                total_amount     = EXCLUDED.total_amount,
                approved_claims  = EXCLUDED.approved_claims,
                denied_claims    = EXCLUDED.denied_claims,
                fraud_detected   = EXCLUDED.fraud_detected,
                avg_claim_amount = EXCLUDED.avg_claim_amount
        """)
    conn.commit()
    logger.info("Analytics summary refreshed")


def main():
    conn = get_connection()
    try:
        patients  = generate_patients()
        hospitals = generate_hospitals()
        seed_patients(conn, patients)
        seed_hospitals(conn, hospitals)
        claims = generate_historical_claims(patients, hospitals, days=30, claims_per_day=100)
        seed_claims(conn, claims)
        seed_fraud_alerts(conn, claims)
        refresh_analytics_summary(conn)
        logger.info("Database seeding complete")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
