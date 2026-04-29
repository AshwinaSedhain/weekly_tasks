#!/bin/bash
# Launches the full pipeline in separate terminal tabs/windows
# Usage: bash run_pipeline.sh

KAFKA_HOME=~/Downloads/kafka_2.13-3.7.0
PROJECT_DIR=~/Downloads/BIG_DATA_VITESSE
VENV=$PROJECT_DIR/venv/bin/activate
BOOTSTRAP=localhost:9092
TOPIC=user_events

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log()  { echo -e "${GREEN}[RUN]${NC} $1"; }
warn() { echo -e "${YELLOW}[WAIT]${NC} $1"; }
err()  { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

# --- Preflight checks ---
[ -d "$KAFKA_HOME" ] || err "Kafka not found at $KAFKA_HOME"
[ -f "$VENV" ]       || err "venv not found. Run: python3 -m venv $PROJECT_DIR/venv && $PROJECT_DIR/venv/bin/pip install -r $PROJECT_DIR/requirements.txt"
command -v java &>/dev/null || err "Java not found. Install: sudo pacman -S jdk11-openjdk"

# --- Clean previous run ---
log "Cleaning previous output and checkpoints..."
rm -rf $PROJECT_DIR/output/streaming_sink/*
rm -rf /tmp/spark_checkpoints/streaming
mkdir -p $PROJECT_DIR/output/streaming_sink
mkdir -p $PROJECT_DIR/output/batch_results
mkdir -p /tmp/spark_checkpoints/streaming

# --- Step 1: Start Zookeeper ---
log "Starting Zookeeper..."
gnome-terminal --title="Zookeeper" -- bash -c "$KAFKA_HOME/bin/zookeeper-server-start.sh $KAFKA_HOME/config/zookeeper.properties; exec bash" 2>/dev/null \
|| xterm -title "Zookeeper" -e "$KAFKA_HOME/bin/zookeeper-server-start.sh $KAFKA_HOME/config/zookeeper.properties" &

warn "Waiting 8s for Zookeeper to start..."
sleep 8

# --- Step 2: Start Kafka Broker ---
log "Starting Kafka Broker..."
gnome-terminal --title="Kafka Broker" -- bash -c "$KAFKA_HOME/bin/kafka-server-start.sh $KAFKA_HOME/config/server.properties; exec bash" 2>/dev/null \
|| xterm -title "Kafka Broker" -e "$KAFKA_HOME/bin/kafka-server-start.sh $KAFKA_HOME/config/server.properties" &

warn "Waiting 10s for Kafka to start..."
sleep 10

# --- Step 3: Create topic (idempotent) ---
log "Creating Kafka topic: $TOPIC..."
$KAFKA_HOME/bin/kafka-topics.sh --create \
  --topic $TOPIC \
  --bootstrap-server $BOOTSTRAP \
  --partitions 3 \
  --replication-factor 1 2>&1 | grep -v "already exists" || true

$KAFKA_HOME/bin/kafka-topics.sh --describe --topic $TOPIC --bootstrap-server $BOOTSTRAP

# --- Step 4: Start Producer ---
log "Starting Kafka Producer..."
gnome-terminal --title="Producer" -- bash -c "source $VENV && cd $PROJECT_DIR && python producer.py; exec bash" 2>/dev/null \
|| xterm -title "Producer" -e "bash -c 'source $VENV && cd $PROJECT_DIR && python producer.py'" &

warn "Waiting 5s for producer to start sending events..."
sleep 5

# --- Step 5: Start Spark Streaming ---
log "Starting Spark Streaming (Speed Layer)..."
gnome-terminal --title="Spark Streaming" -- bash -c "source $VENV && cd $PROJECT_DIR && spark-submit --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0 spark_streaming.py; exec bash" 2>/dev/null \
|| xterm -title "Spark Streaming" -e "bash -c 'source $VENV && cd $PROJECT_DIR && spark-submit --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0 spark_streaming.py'" &

warn "Waiting 90s for streaming to accumulate parquet data..."
sleep 90

# --- Step 6: Run Spark Batch ---
log "Running Spark Batch Job (Batch Layer)..."
cd $PROJECT_DIR
source $VENV
spark-submit spark_batch.py

log "Pipeline complete. Results in: $PROJECT_DIR/output/batch_results/"
