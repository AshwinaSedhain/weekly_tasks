# This file is implementing the Kafka producer. It is serializing each article
# dictionary to JSON and publishing it to the raw-news topic so the Spark streaming
# job can pick it up for processing. The article ID is used as the Kafka message
# key so partitioning is consistent and consumers can identify each record easily.

import json
import logging
import os
from typing import Optional

from kafka import KafkaProducer
from kafka.errors import KafkaError

logger = logging.getLogger(__name__)

KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
RAW_NEWS_TOPIC = "raw-news"
ERROR_TOPIC = "error-events"


class NewsProducer:

    def __init__(self) -> None:
        # Starting with no producer so it is created lazily on first use.
        self._producer: Optional[KafkaProducer] = None

    def _get_producer(self) -> KafkaProducer:
        # Creating the KafkaProducer on first use. Lazy initialization means
        # the application can import this module without immediately requiring
        # a running Kafka broker.
        if self._producer is None:
            self._producer = KafkaProducer(
                bootstrap_servers=KAFKA_BOOTSTRAP,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                key_serializer=lambda k: k.encode("utf-8") if k else None,
                retries=3,
                acks="all",
            )
        return self._producer

    def publish(self, article: dict) -> None:
        # Publishing a single article to the raw-news Kafka topic. Using the
        # article ID as the message key. Logging any delivery errors to the
        # error-events topic so they can be investigated later.
        producer = self._get_producer()
        article_id = article.get("id", "")
        try:
            producer.send(RAW_NEWS_TOPIC, key=article_id, value=article)
            logger.debug("Publishing article %s to %s", article_id, RAW_NEWS_TOPIC)
        except KafkaError as exc:
            logger.error("Publishing article %s failing: %s", article_id, exc)
            self._publish_error(article_id, str(exc))

    def publish_batch(self, articles: list[dict]) -> None:
        # Publishing a list of articles to Kafka and flushing the producer buffer
        # after all messages have been sent. Flushing ensures no messages are lost
        # when the process exits.
        for article in articles:
            self.publish(article)
        self._get_producer().flush()
        logger.info("Published %d articles to Kafka", len(articles))

    def _publish_error(self, article_id: str, error_message: str) -> None:
        # Sending an error record to the error-events topic so failed deliveries
        # are visible to monitoring tools.
        try:
            producer = self._get_producer()
            producer.send(
                ERROR_TOPIC,
                key=article_id,
                value={"article_id": article_id, "error": error_message},
            )
        except KafkaError as exc:
            logger.error("Publishing error event failing: %s", exc)

    def close(self) -> None:
        # Closing the underlying KafkaProducer and releasing its network connections.
        if self._producer:
            self._producer.close()
            logger.info("Kafka producer closing")
