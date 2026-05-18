# Read from raw-claims, validate each record, and route to the correct topic.
import json
import logging
import os
import signal
import time
from typing import Dict, Any

from kafka import KafkaConsumer, KafkaProducer
from kafka.errors import NoBrokersAvailable

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
TOPIC_RAW       = os.getenv("KAFKA_TOPIC_RAW_CLAIMS",       "raw-claims")
TOPIC_VALIDATED = os.getenv("KAFKA_TOPIC_VALIDATED_CLAIMS",  "validated-claims")
TOPIC_FRAUD     = os.getenv("KAFKA_TOPIC_FRAUD_ALERTS",      "fraud-alerts")
FRAUD_THRESHOLD = float(os.getenv("FRAUD_THRESHOLD", "0.7"))

_running = True


def _signal_handler(sig, frame):
    global _running
    _running = False


signal.signal(signal.SIGINT,  _signal_handler)
signal.signal(signal.SIGTERM, _signal_handler)


def _connect(retries: int = 15, delay: int = 5):
    # Retry until Kafka is available, then return a consumer and producer pair.
    for attempt in range(retries):
        try:
            consumer = KafkaConsumer(
                TOPIC_RAW,
                bootstrap_servers=KAFKA_BOOTSTRAP,
                group_id="healthstream-validator",
                value_deserializer=lambda m: json.loads(m.decode("utf-8")),
                auto_offset_reset="earliest",
                enable_auto_commit=True,
            )
            producer = KafkaProducer(
                bootstrap_servers=KAFKA_BOOTSTRAP,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                key_serializer=lambda k: k.encode("utf-8") if k else None,
            )
            logger.info("Kafka consumer/producer connected")
            return consumer, producer
        except NoBrokersAvailable:
            logger.warning("Kafka not ready (attempt %d/%d)", attempt + 1, retries)
            time.sleep(delay)
    raise RuntimeError("Could not connect to Kafka")


def validate_claim(claim: Dict[str, Any]) -> tuple[bool, str]:
    # Check that required fields are present and the amount is within range.
    required = ["claim_id", "patient_id", "hospital_id", "claim_amount", "claim_date"]
    for field in required:
        if not claim.get(field):
            return False, f"Missing required field: {field}"
    if claim["claim_amount"] <= 0:
        return False, "claim_amount must be positive"
    if claim["claim_amount"] > 1_000_000:
        return False, "claim_amount exceeds maximum threshold"
    return True, "OK"


def run_consumer():
    consumer, producer = _connect()
    processed = 0
    fraud_count = 0

    logger.info("Listening on topic: %s", TOPIC_RAW)

    for message in consumer:
        if not _running:
            break

        claim = message.value
        is_valid, reason = validate_claim(claim)

        if not is_valid:
            logger.warning("Invalid claim %s: %s", claim.get("claim_id"), reason)
            continue

        if claim.get("fraud_score", 0) >= FRAUD_THRESHOLD or claim.get("is_fraud"):
            claim["alert_reason"] = "High fraud score detected by consumer"
            claim["severity"]     = "HIGH" if claim.get("fraud_score", 0) > 0.85 else "MEDIUM"
            producer.send(TOPIC_FRAUD, key=claim["claim_id"], value=claim)
            fraud_count += 1
        else:
            producer.send(TOPIC_VALIDATED, key=claim["claim_id"], value=claim)

        processed += 1
        if processed % 100 == 0:
            logger.info("Processed %d claims (%d fraud alerts)", processed, fraud_count)

    consumer.close()
    producer.close()
    logger.info("Consumer stopped. Processed: %d, Fraud: %d", processed, fraud_count)


if __name__ == "__main__":
    run_consumer()
