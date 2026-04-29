#!/bin/bash
# Manual run script - prints commands to copy-paste into separate terminals

KAFKA_HOME=~/Downloads/kafka_2.13-3.7.0
PROJECT_DIR=~/Downloads/BIG_DATA_VITESSE

cat << 'EOF'
╔══════════════════════════════════════════════════════════════════════════╗
║  Real-Time User Activity Processing System - Manual Run Guide           ║
╚══════════════════════════════════════════════════════════════════════════╝

Open 5 SEPARATE TERMINALS and run these commands IN ORDER:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TERMINAL 1 — Zookeeper
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EOF

echo "$KAFKA_HOME/bin/zookeeper-server-start.sh $KAFKA_HOME/config/zookeeper.properties"

cat << 'EOF'

Wait for: "binding to port 0.0.0.0/0.0.0.0:2181"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TERMINAL 2 — Kafka Broker
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EOF

echo "$KAFKA_HOME/bin/kafka-server-start.sh $KAFKA_HOME/config/server.properties"

cat << 'EOF'

Wait for: "started (kafka.server.KafkaServer)"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TERMINAL 3 — Create Topic + Producer
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EOF

cat << EOF
$KAFKA_HOME/bin/kafka-topics.sh --create --topic user_events --bootstrap-server localhost:9092 --partitions 3 --replication-factor 1

cd $PROJECT_DIR
source venv/bin/activate
python producer.py
EOF

cat << 'EOF'

Wait until you see: "[1] Sent: user_007 | click | ..."

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TERMINAL 4 — Spark Streaming (let run 2-3 minutes)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EOF

cat << EOF
cd $PROJECT_DIR
source venv/bin/activate
rm -rf output/streaming_sink/* /tmp/spark_checkpoints/streaming
spark-submit --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0 spark_streaming.py
EOF

cat << 'EOF'

Wait ~30s until you see windowed tables printing every 10 seconds.
LET IT RUN FOR 2-3 MINUTES to accumulate parquet data.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TERMINAL 5 — Spark Batch (after 2-3 min of streaming)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EOF

cat << EOF
cd $PROJECT_DIR
source venv/bin/activate
spark-submit spark_batch.py
EOF

cat << 'EOF'

You should see:
  - User activity summary table
  - Event type breakdown
  - Top pages
  - CSV files written to output/batch_results/

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EOF
