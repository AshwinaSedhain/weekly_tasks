# This file is defining and creating the Kafka topics used by the pipeline.
# Running this script once before starting the pipeline ensures all required
# topics exist with the correct partition and replication settings.

import logging
import os

from kafka.admin import KafkaAdminClient, NewTopic
from kafka.errors import TopicAlreadyExistsError

logger = logging.getLogger(__name__)

KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")

# Defining the three topics the pipeline uses. raw-news receives every new article,
# processed-news receives enriched articles from Spark, and error-events receives
# records for any messages that failed to deliver.
TOPICS = [
    NewTopic(name="raw-news", num_partitions=3, replication_factor=1),
    NewTopic(name="processed-news", num_partitions=3, replication_factor=1),
    NewTopic(name="error-events", num_partitions=1, replication_factor=1),
]


def create_topics() -> None:
    # Connecting to the Kafka broker and creating all required topics. Ignoring
    # TopicAlreadyExistsError so this function is safe to call multiple times
    # without any side effects.
    admin = KafkaAdminClient(bootstrap_servers=KAFKA_BOOTSTRAP)
    try:
        admin.create_topics(new_topics=TOPICS, validate_only=False)
        logger.info("Kafka topics created successfully")
    except TopicAlreadyExistsError:
        logger.info("Kafka topics already existing, skipping creation")
    finally:
        admin.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    create_topics()
