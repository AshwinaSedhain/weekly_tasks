# Generate synthetic healthcare claims data using Faker.
import uuid
import random
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any

from faker import Faker
from config import (
    NUM_PATIENTS, NUM_HOSPITALS, FRAUD_RATE,
    DIAGNOSIS_CODES, INSURANCE_STATUSES, INSURANCE_TYPES,
    HOSPITAL_TYPES, TREATMENT_CODES, US_STATES,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

fake = Faker()
Faker.seed(42)
random.seed(42)


def generate_patients(n: int = NUM_PATIENTS) -> List[Dict[str, Any]]:
    # Build a pool of fake patients to reference when creating claims.
    patients = []
    for _ in range(n):
        dob = fake.date_of_birth(minimum_age=18, maximum_age=90)
        patients.append({
            "patient_id":     str(uuid.uuid4()),
            "first_name":     fake.first_name(),
            "last_name":      fake.last_name(),
            "date_of_birth":  dob.isoformat(),
            "gender":         random.choice(["MALE", "FEMALE", "OTHER"]),
            "state":          random.choice(US_STATES),
            "insurance_type": random.choice(INSURANCE_TYPES),
            "risk_score":     round(random.uniform(0.0, 1.0), 4),
        })
    logger.info("Generated %d patients", n)
    return patients


def generate_hospitals(n: int = NUM_HOSPITALS) -> List[Dict[str, Any]]:
    # Build a pool of fake hospitals to reference when creating claims.
    hospitals = []
    for _ in range(n):
        hospitals.append({
            "hospital_id":       str(uuid.uuid4()),
            "hospital_name":     fake.company() + " Medical Center",
            "state":             random.choice(US_STATES),
            "hospital_type":     random.choice(HOSPITAL_TYPES),
            "bed_count":         random.randint(50, 800),
            "accreditation":     random.choice(["JCI", "DNV", "ACHC", "NONE"]),
            "performance_score": round(random.uniform(60.0, 99.0), 2),
        })
    logger.info("Generated %d hospitals", n)
    return hospitals


def _fraud_score(is_fraud: bool, claim_amount: float) -> float:
    # Assign a higher base score to fraudulent claims and bump it for large amounts.
    base = random.uniform(0.6, 0.99) if is_fraud else random.uniform(0.0, 0.25)
    if claim_amount > 50_000:
        base = min(base + 0.15, 0.99)
    return round(base, 4)


def generate_claim(
    patients: List[Dict],
    hospitals: List[Dict],
    timestamp: datetime = None,
) -> Dict[str, Any]:
    # Pick random patient and hospital, then build a single claim record.
    patient  = random.choice(patients)
    hospital = random.choice(hospitals)
    treatment_code = random.choice(TREATMENT_CODES)

    base_amount = random.uniform(200, 30_000)
    if random.random() < FRAUD_RATE:
        # Inflate the amount to simulate a fraudulent claim.
        base_amount *= random.uniform(3, 10)
    claim_amount = round(base_amount, 2)

    is_fraud = random.random() < FRAUD_RATE
    ts = timestamp or datetime.utcnow()

    return {
        "claim_id":         str(uuid.uuid4()),
        "patient_id":       patient["patient_id"],
        "hospital_id":      hospital["hospital_id"],
        "treatment_code":   treatment_code,
        "diagnosis_code":   random.choice(DIAGNOSIS_CODES),
        "claim_amount":     claim_amount,
        "approved_amount":  round(claim_amount * random.uniform(0.5, 1.0), 2),
        "insurance_status": random.choice(INSURANCE_STATUSES),
        "claim_date":       ts.isoformat(),
        "is_fraud":         is_fraud,
        "fraud_score":      _fraud_score(is_fraud, claim_amount),
        "status":           "PENDING",
        "patient_state":    patient["state"],
        "insurance_type":   patient["insurance_type"],
        "hospital_state":   hospital["state"],
        "hospital_type":    hospital["hospital_type"],
    }


def generate_batch(
    patients: List[Dict],
    hospitals: List[Dict],
    batch_size: int = 50,
) -> List[Dict[str, Any]]:
    # Generate a batch of claims with timestamps spread over the last few seconds.
    now = datetime.utcnow()
    return [
        generate_claim(patients, hospitals, now - timedelta(seconds=i))
        for i in range(batch_size)
    ]


def generate_historical_claims(
    patients: List[Dict],
    hospitals: List[Dict],
    days: int = 90,
    claims_per_day: int = 200,
) -> List[Dict[str, Any]]:
    # Generate past claims spread across multiple days to seed the warehouse.
    claims = []
    base_date = datetime.utcnow() - timedelta(days=days)
    for day in range(days):
        day_ts = base_date + timedelta(days=day)
        for _ in range(claims_per_day):
            ts = day_ts + timedelta(
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59),
            )
            claims.append(generate_claim(patients, hospitals, ts))
    logger.info("Generated %d historical claims (%d days)", len(claims), days)
    return claims


if __name__ == "__main__":
    patients  = generate_patients()
    hospitals = generate_hospitals()
    batch     = generate_batch(patients, hospitals, batch_size=5)
    print(json.dumps(batch[0], indent=2))
