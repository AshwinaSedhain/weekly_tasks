# Create the three Kafka topics the pipeline depends on.
import logging
import os
import time

from kafka import KafkaAdminClient
from kafka.admin import NewTopic
from kafka.errors import TopicAlreadyExistsError, NoBrokersAvailable

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")

TOPICS = [
    NewTopic(name="raw-claims",       num_partitions=3, replication_factor=1),
    NewTopic(name="validated-claims", num_partitions=3, replication_factor=1),
    NewTopic(name="fraud-alerts",     num_partitions=1, replication_factor=1),
]


def create_topics(retries: int = 15, delay: int = 5):
    # Retry until Kafka is ready, then create each topic if it does not exist.
    for attempt in range(retries):
        try:
            admin = KafkaAdminClient(bootstrap_servers=KAFKA_BOOTSTRAP)
            for topic in TOPICS:
                try:
                    admin.create_topics([topic])
                    logger.info("Created topic: %s", topic.name)
                except TopicAlreadyExistsError:
                    logger.info("Topic already exists: %s", topic.name)
            admin.close()
            return
        except NoBrokersAvailable:
            logger.warning("Kafka not ready (attempt %d/%d)", attempt + 1, retries)
            time.sleep(delay)
    raise RuntimeError("Could not connect to Kafka to create topics")


if __name__ == "__main__":
    create_topics()
    logger.info("All topics ready")
