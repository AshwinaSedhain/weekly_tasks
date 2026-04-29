# Real-Time User Activity Processing System
### Simplified Lambda Architecture — Kafka + Spark Structured Streaming

---

## Architecture Overview

```
[producer.py]
     │
     ▼  (JSON events)
[Kafka Topic: user_events]
     │
     ├──► [spark_streaming.py]  ← Speed Layer
     │         │
     │         ├── windowed event counts (console)
     │         ├── purchase filter (console)
     │         └── parquet sink → ./output/streaming_sink/
     │
     └──► [spark_batch.py]      ← Batch Layer
               │
               └── reads parquet sink → aggregations → CSV + console
                                                         ▲
                                                   Serving Layer
```

**Lambda Architecture mapping:**
| Layer | Component |
|---|---|
| Ingestion | Apache Kafka (`user_events` topic) |
| Speed Layer | Spark Structured Streaming (10s windows) |
| Batch Layer | Spark Batch Job (full historical aggregation) |
| Serving Layer | Console output + CSV files in `./output/batch_results/` |

---

## Prerequisites

- Java 8 or 11 (required by Kafka and Spark)
- Python 3.8+
- Apache Kafka 3.x ([download](https://kafka.apache.org/downloads))
- Apache Spark 3.5.x ([download](https://spark.apache.org/downloads.html))

```bash
pip install -r requirements.txt
```

---

## Step-by-Step Setup

### 1. Start Zookeeper and Kafka

Open two separate terminals:

```bash
# Terminal 1 — Zookeeper
$KAFKA_HOME/bin/zookeeper-server-start.sh $KAFKA_HOME/config/zookeeper.properties

# Terminal 2 — Kafka Broker
$KAFKA_HOME/bin/kafka-server-start.sh $KAFKA_HOME/config/server.properties
```

### 2. Create the Kafka Topic

```bash
$KAFKA_HOME/bin/kafka-topics.sh \
  --create \
  --topic user_events \
  --bootstrap-server localhost:9092 \
  --partitions 3 \
  --replication-factor 1
```

**Why 3 partitions?**  
Partitions allow parallel consumption. With 3 partitions, up to 3 consumers in the same consumer group can read simultaneously — each consumer owns one partition. If you add a 4th consumer, it sits idle. Spark Streaming internally maps each partition to a task, so 3 partitions = 3 parallel Spark tasks reading from Kafka.

Verify topic creation:
```bash
$KAFKA_HOME/bin/kafka-topics.sh --describe --topic user_events --bootstrap-server localhost:9092
```

### 3. Run the Producer

```bash
# Terminal 3
python producer.py
```

You'll see continuous output like:
```
[1] Sent: user_007 | click | 2024-01-15T10:23:45.123456+00:00
[2] Sent: user_012 | purchase | 2024-01-15T10:23:45.891234+00:00
```

### 4. Run Spark Streaming (Speed Layer)

```bash
# Terminal 4
spark-submit \
  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0 \
  spark_streaming.py
```

Every 10 seconds you'll see windowed aggregations in the console:
```

|window                                    |user_id |event_type|event_count|
+------------------------------------------+--------+----------+-----------+
|{2024-01-15 10:23:40, 2024-01-15 10:23:50}|user_007|click     |3          |
|{2024-01-15 10:23:40, 2024-01-15 10:23:50}|user_012|purchase  |1          |

```

Let this run for at least **2-3 minutes** to accumulate enough parquet data for the batch job.

### 5. Run Spark Batch Job (Batch Layer)

After stopping or while streaming is running (parquet files are being written):

```bash
# Terminal 5
spark-submit spark_batch.py
```

Output:
```
============================================================
SERVING LAYER: User Activity Summary
============================================================
+--------+------------+---------------+-------------+------------+-------------------+
|user_id |total_events|total_purchases|total_logins |total_clicks|last_seen          |
+--------+------------+---------------+-------------+------------+-------------------+
|user_003|47          |9              |14           |24          |2024-01-15 10:25:11|
|user_017|43          |8              |13           |22          |2024-01-15 10:25:09|
...
```

CSV results are written to `./output/batch_results/`.

---

## Output Files

```
output/
├── streaming_sink/       ← Parquet files written by Spark Streaming
│   └── *.parquet
└── batch_results/
    ├── user_summary/     ← Total events, purchases, logins, clicks per user
    ├── event_breakdown/  ← Distribution across event types
    └── top_pages/        ← Most visited pages
```

---

## Consumer Group Note

When Spark Streaming reads from Kafka, it acts as a consumer group (default group ID is auto-assigned by Spark). You can inspect active consumer groups:

```bash
$KAFKA_HOME/bin/kafka-consumer-groups.sh \
  --bootstrap-server localhost:9092 \
  --list
```

Each consumer group maintains its own offset per partition — meaning two different Spark jobs (streaming + a separate reader) can independently consume the same topic without interfering with each other.

---

## Troubleshooting

| Issue                            | Fix |
|---|---|
| `NoBrokersAvailable` | Kafka not running or wrong bootstrap server |
| `No parquet data found` | Run streaming job first for 2+ minutes |
| Spark package download slow | Pre-download jar or use `--jars` with local path |
| `WARN TaskSchedulerImpl` | Normal in local mode, not an error |
| Empty streaming output | Check watermark — events need `event_time` within 30s of processing time |
