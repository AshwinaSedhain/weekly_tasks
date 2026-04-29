"""
Kafka Producer - Simulates real-time user activity events
Sends JSON events to topic: user_events
"""

import json
import random
import time
from datetime import datetime, timezone
from kafka import KafkaProducer

KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"
TOPIC = "user_events"

EVENT_TYPES = ["login", "click", "purchase"]
USER_IDS = [f"user_{i:03d}" for i in range(1, 21)]  # user_001 to user_020


def create_producer():
    return KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        key_serializer=lambda k: k.encode("utf-8"),
        acks="all",
        retries=3,
    )


def generate_event():
    return {
        "user_id": random.choice(USER_IDS),
        "event_type": random.choices(
            EVENT_TYPES, weights=[0.3, 0.5, 0.2]  # login:30%, click:50%, purchase:20%
        )[0],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "session_id": f"sess_{random.randint(1000, 9999)}",
        "page": random.choice(["/home", "/product", "/cart", "/checkout", "/profile"]),
    }


def main():
    producer = create_producer()
    print(f"[Producer] Connected to Kafka. Sending events to topic: {TOPIC}")

    sent_count = 0
    try:
        while True:
            event = generate_event()
            producer.send(
                topic=TOPIC,
                key=event["user_id"],
                value=event,
            )
            sent_count += 1
            print(f"[{sent_count}] Sent: {event['user_id']} | {event['event_type']} | {event['timestamp']}")
            time.sleep(random.uniform(0.2, 1.0))  # simulate variable event rate
    except KeyboardInterrupt:
        print(f"\n[Producer] Stopped. Total events sent: {sent_count}")
    finally:
        producer.flush()
        producer.close()


if __name__ == "__main__":
    main()
