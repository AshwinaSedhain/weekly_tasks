# This file is implementing the Kafka consumer. It is reading messages from the
# raw-news and processed-news topics and passing each message to a handler callback.
# The caller decides what to do with the data by providing the handler function.
# The loop runs until the caller sets the running flag to False.

import json
import logging
import os
from typing import Callable

from kafka import KafkaConsumer
from kafka.errors import KafkaError

logger = logging.getLogger(__name__)

KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")


class NewsConsumer:

    def __init__(self, topics: list[str], group_id: str) -> None:
        # Storing the topics to subscribe to and the consumer group ID.
        # Setting running to True so the consume loop starts immediately.
        self.topics = topics
        self.group_id = group_id
        self.running = True
        self._consumer: KafkaConsumer | None = None

    def _get_consumer(self) -> KafkaConsumer:
        # Creating the KafkaConsumer on first use. Setting auto-offset-reset to
        # earliest so no messages are missed when the consumer group starts for
        # the first time.
        if self._consumer is None:
            self._consumer = KafkaConsumer(
                *self.topics,
                bootstrap_servers=KAFKA_BOOTSTRAP,
                group_id=self.group_id,
                value_deserializer=lambda v: json.loads(v.decode("utf-8")),
                auto_offset_reset="earliest",
                enable_auto_commit=True,
            )
        return self._consumer

    def consume(self, handler: Callable[[dict], None]) -> None:
        # Running the main consumption loop. Polling the Kafka broker for new
        # messages and calling the handler for each one. Any exception raised by
        # the handler is caught and logged so one bad message does not stop the
        # entire consumer.
        consumer = self._get_consumer()
        logger.info("Starting consumer for topics %s", self.topics)
        try:
            while self.running:
                for message in consumer:
                    if not self.running:
                        break
                    try:
                        handler(message.value)
                    except Exception as exc:
                        logger.error("Handler failing for message: %s", exc)
        except KafkaError as exc:
            logger.error("Kafka consumer error: %s", exc)
        finally:
            consumer.close()
            logger.info("Kafka consumer closing")

    def stop(self) -> None:
        # Signaling the consume loop to exit after the current poll completes.
        self.running = False
