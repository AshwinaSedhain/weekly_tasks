# Load settings from environment variables with sensible defaults.
import os
from dotenv import load_dotenv

load_dotenv()

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
KAFKA_TOPIC_RAW_CLAIMS  = os.getenv("KAFKA_TOPIC_RAW_CLAIMS", "raw-claims")

DB_HOST     = os.getenv("DB_HOST",     "postgres")
DB_PORT     = int(os.getenv("DB_PORT", "5432"))
DB_NAME     = os.getenv("DB_NAME",     "healthstream")
DB_USER     = os.getenv("DB_USER",     "healthstream")
DB_PASSWORD = os.getenv("DB_PASSWORD", "healthstream123")

BATCH_SIZE          = int(os.getenv("BATCH_SIZE",           "50"))
GENERATION_INTERVAL = float(os.getenv("GENERATION_INTERVAL", "2.0"))
NUM_PATIENTS        = int(os.getenv("NUM_PATIENTS",         "500"))
NUM_HOSPITALS       = int(os.getenv("NUM_HOSPITALS",        "30"))
FRAUD_RATE          = float(os.getenv("FRAUD_RATE",         "0.05"))

# ICD-10 diagnosis codes used to label claims
DIAGNOSIS_CODES = [
    "I21.0",   # acute MI
    "J18.9",   # pneumonia
    "E11.9",   # type 2 diabetes
    "I10",     # hypertension
    "M54.5",   # low back pain
    "J44.1",   # COPD
    "N18.3",   # chronic kidney disease
    "F32.1",   # major depressive disorder
    "C34.10",  # lung cancer
    "K92.1",   # GI bleed
    "I63.9",   # cerebral infarction
    "G30.9",   # Alzheimer's
    "Z23",     # immunization
    "O80",     # normal delivery
    "S72.001", # hip fracture
]

INSURANCE_STATUSES = ["APPROVED", "DENIED", "PENDING", "PARTIAL"]
INSURANCE_TYPES    = ["MEDICARE", "MEDICAID", "PRIVATE", "UNINSURED"]
HOSPITAL_TYPES     = ["GENERAL", "SPECIALTY", "TEACHING", "CRITICAL_ACCESS"]
TREATMENT_CODES    = [f"T{str(i).zfill(3)}" for i in range(1, 16)]
US_STATES = [
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
    "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
    "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
    "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
    "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY",
]
