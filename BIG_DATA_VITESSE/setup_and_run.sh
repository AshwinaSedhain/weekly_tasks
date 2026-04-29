#!/bin/bash
# Full setup script: creates venv, installs deps, validates environment

set -e  # exit on any error

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$PROJECT_DIR/venv"

echo "============================================"
echo " Real-Time User Activity Processing System"
echo " Setup Script"
echo "============================================"

# --- Step 1: Check prerequisites ---
echo ""
echo "[1/5] Checking prerequisites..."

if ! command -v python3 &>/dev/null; then
    echo "ERROR: python3 not found. Install Python 3.8+"
    exit 1
fi
PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "  Python: $PYTHON_VERSION"

if ! command -v java &>/dev/null; then
    echo "ERROR: Java not found. Spark requires Java 8 or 11."
    echo "  Install: sudo pacman -S jdk11-openjdk"
    exit 1
fi
JAVA_VERSION=$(java -version 2>&1 | head -1)
echo "  Java: $JAVA_VERSION"

# --- Step 2: Create virtual environment ---
echo ""
echo "[2/5] Creating virtual environment at: $VENV_DIR"

if [ -d "$VENV_DIR" ]; then
    echo "  venv already exists, skipping creation."
else
    python3 -m venv "$VENV_DIR"
    echo "  venv created."
fi

# Activate venv
source "$VENV_DIR/bin/activate"
echo "  Activated: $(which python)"

# --- Step 3: Install requirements ---
echo ""
echo "[3/5] Installing requirements..."
pip install --upgrade pip --quiet
pip install -r "$PROJECT_DIR/requirements.txt"
echo "  Installed: kafka-python, pyspark"

# Verify installs
python -c "import kafka; print(f'  kafka-python: {kafka.__version__}')"
python -c "import pyspark; print(f'  pyspark: {pyspark.__version__}')"

# --- Step 4: Create output directories ---
echo ""
echo "[4/5] Creating output directories..."
mkdir -p "$PROJECT_DIR/output/streaming_sink"
mkdir -p "$PROJECT_DIR/output/batch_results"
mkdir -p /tmp/spark_checkpoints/streaming
echo "  Directories ready."

# --- Step 5: Check Kafka ---
echo ""
echo "[5/5] Checking Kafka availability..."
if nc -z localhost 9092 2>/dev/null; then
    echo "  Kafka is RUNNING on localhost:9092"
    KAFKA_RUNNING=true
else
    echo "  Kafka is NOT running on localhost:9092"
    echo "  Start Kafka before running producer/streaming jobs."
    KAFKA_RUNNING=false
fi

# --- Summary ---
echo ""
echo "============================================"
echo " Setup Complete!"
echo "============================================"
echo ""
echo "To activate the venv in your terminal:"
echo "  source $VENV_DIR/bin/activate"
echo ""
echo "Run order:"
echo ""
echo "  # Terminal 1 — Zookeeper"
echo "  \$KAFKA_HOME/bin/zookeeper-server-start.sh \$KAFKA_HOME/config/zookeeper.properties"
echo ""
echo "  # Terminal 2 — Kafka Broker"
echo "  \$KAFKA_HOME/bin/kafka-server-start.sh \$KAFKA_HOME/config/server.properties"
echo ""
echo "  # Terminal 3 — Create topic (run once)"
echo "  \$KAFKA_HOME/bin/kafka-topics.sh --create --topic user_events \\"
echo "    --bootstrap-server localhost:9092 --partitions 3 --replication-factor 1"
echo ""
echo "  # Terminal 4 — Producer"
echo "  source $VENV_DIR/bin/activate"
echo "  python producer.py"
echo ""
echo "  # Terminal 5 — Spark Streaming (Speed Layer)"
echo "  source $VENV_DIR/bin/activate"
echo "  spark-submit --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0 spark_streaming.py"
echo ""
echo "  # Terminal 6 — Spark Batch (after 2-3 min of streaming)"
echo "  source $VENV_DIR/bin/activate"
echo "  spark-submit spark_batch.py"
echo ""

deactivate
