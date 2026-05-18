# Continuously stream synthetic claims to the raw-claims Kafka topic.
import json
import logging
import time
import signal

from kafka import KafkaProducer
from kafka.errors import NoBrokersAvailable
from config import (
    KAFKA_BOOTSTRAP_SERVERS, KAFKA_TOPIC_RAW_CLAIMS,
    BATCH_SIZE, GENERATION_INTERVAL,
)
from generator import generate_patients, generate_hospitals, generate_batch

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

_running = True


def _signal_handler(sig, frame):
    global _running
    logger.info("Shutdown signal received, stopping producer")
    _running = False


signal.signal(signal.SIGINT,  _signal_handler)
signal.signal(signal.SIGTERM, _signal_handler)


def create_producer(retries: int = 15, delay: int = 5) -> KafkaProducer:
    # Retry connecting to Kafka until the broker is ready.
    for attempt in range(retries):
        try:
            producer = KafkaProducer(
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                key_serializer=lambda k: k.encode("utf-8") if k else None,
                acks="all",
                retries=3,
                max_block_ms=30_000,
            )
            logger.info("Kafka producer connected to %s", KAFKA_BOOTSTRAP_SERVERS)
            return producer
        except NoBrokersAvailable:
            logger.warning("Kafka not ready (attempt %d/%d)", attempt + 1, retries)
            time.sleep(delay)
    raise RuntimeError("Could not connect to Kafka after retries")


def run_producer():
    patients  = generate_patients()
    hospitals = generate_hospitals()
    producer  = create_producer()
    total_sent = 0

    logger.info("Streaming claims to topic: %s", KAFKA_TOPIC_RAW_CLAIMS)

    while _running:
        batch = generate_batch(patients, hospitals, batch_size=BATCH_SIZE)
        for claim in batch:
            producer.send(
                KAFKA_TOPIC_RAW_CLAIMS,
                key=claim["patient_id"],
                value=claim,
            )
        producer.flush()
        total_sent += len(batch)
        logger.info("Sent %d claims (total: %d)", len(batch), total_sent)
        time.sleep(GENERATION_INTERVAL)

    producer.close()
    logger.info("Producer stopped. Total claims sent: %d", total_sent)


if __name__ == "__main__":
    run_producer()
