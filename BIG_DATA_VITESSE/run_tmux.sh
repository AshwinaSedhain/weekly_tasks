#!/bin/bash
# Runs the full pipeline inside a tmux session with 5 panes
# Usage: bash run_tmux.sh
# To watch: tmux attach -t bigdata

KAFKA_HOME=~/Downloads/kafka_2.13-3.7.0
PROJECT_DIR=~/Downloads/BIG_DATA_VITESSE
SESSION="bigdata"

# Check tmux
if ! command -v tmux &>/dev/null; then
    echo "tmux not found. Install it: sudo pacman -S tmux"
    exit 1
fi

# Kill existing session if any
tmux kill-session -t $SESSION 2>/dev/null

# Clean previous run
echo "[CLEAN] Removing old output and checkpoints..."
rm -rf $PROJECT_DIR/output/streaming_sink/*
rm -rf /tmp/spark_checkpoints/streaming
mkdir -p $PROJECT_DIR/output/streaming_sink
mkdir -p $PROJECT_DIR/output/batch_results
mkdir -p /tmp/spark_checkpoints/streaming

# Create tmux session with 5 windows
echo "[TMUX] Creating session: $SESSION"

# Window 0: Zookeeper
tmux new-session -d -s $SESSION -n "zookeeper" \
    "$KAFKA_HOME/bin/zookeeper-server-start.sh $KAFKA_HOME/config/zookeeper.properties"

echo "[WAIT] Waiting 15s for Zookeeper..."
sleep 15

# Window 1: Kafka Broker
tmux new-window -t $SESSION -n "kafka" \
    "$KAFKA_HOME/bin/kafka-server-start.sh $KAFKA_HOME/config/server.properties"

echo "[WAIT] Waiting 15s for Kafka broker..."
sleep 15

# Window 2: Producer (create topic first, then run producer)
tmux new-window -t $SESSION -n "producer" \
    "bash -c '$KAFKA_HOME/bin/kafka-topics.sh --create --topic user_events --bootstrap-server localhost:9092 --partitions 3 --replication-factor 1 2>&1; source $PROJECT_DIR/venv/bin/activate && cd $PROJECT_DIR && python producer.py'"

echo "[WAIT] Waiting 10s for producer to start..."
sleep 10

# Window 3: Spark Streaming
tmux new-window -t $SESSION -n "streaming" \
    "bash -c 'source $PROJECT_DIR/venv/bin/activate && cd $PROJECT_DIR && spark-submit --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0 spark_streaming.py'"

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║  Pipeline is running inside tmux session: bigdata        ║"
echo "╠══════════════════════════════════════════════════════════╣"
echo "║  NOW open a new terminal and run:                        ║"
echo "║      tmux attach -t bigdata                              ║"
echo "║                                                          ║"
echo "║  Switch windows with: Ctrl+B then number                 ║"
echo "║    0 = Zookeeper                                         ║"
echo "║    1 = Kafka Broker                                      ║"
echo "║    2 = Producer (events printing)                        ║"
echo "║    3 = Spark Streaming (tables every 10s)                ║"
echo "╠══════════════════════════════════════════════════════════╣"
echo "║  Waiting 120s for streaming to accumulate parquet data...║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# Count down visibly
for i in $(seq 120 -10 10); do
    echo "[WAIT] $i seconds remaining..."
    sleep 10
done

# Window 4: Spark Batch
echo ""
echo "[RUN] Starting Spark Batch job now..."
tmux new-window -t $SESSION -n "batch" \
    "bash -c 'source $PROJECT_DIR/venv/bin/activate && cd $PROJECT_DIR && spark-submit spark_batch.py; echo \"=== DONE ===\"; read'"

echo ""
echo "[DONE] Batch job running in tmux window 4."
echo "Run:  tmux attach -t bigdata  then press Ctrl+B 4 to see results"
