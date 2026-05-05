#!/usr/bin/env bash
# install_and_run.sh
# Fully automated: installs Airflow, inits DB, creates user,
# then starts scheduler + webserver in the background.
#
# Usage:
#   chmod +x install_and_run.sh
#   ./install_and_run.sh

set -euo pipefail

info()  { echo "[INFO]  $*"; }
warn()  { echo "[WARN]  $*"; }
error() { echo "[ERROR] $*"; exit 1; }

# Detect Python version 
PY_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
info "Detected Python $PY_VERSION"

# Airflow 2.9.1 supports Python 3.8 – 3.11
case "$PY_VERSION" in
  3.8|3.9|3.10|3.11) ;;
  *) warn "Python $PY_VERSION may not be fully supported by Airflow 2.9.1. Proceeding anyway." ;;
esac

CONSTRAINT_URL="https://raw.githubusercontent.com/apache/airflow/constraints-2.9.1/constraints-${PY_VERSION}.txt"

#  Paths 
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export AIRFLOW_HOME="$PROJECT_DIR/airflow_home"
export AIRFLOW__CORE__DAGS_FOLDER="$PROJECT_DIR/dags"
export AIRFLOW__CORE__LOAD_EXAMPLES=False
export AIRFLOW__CORE__EXECUTOR=SequentialExecutor

mkdir -p "$AIRFLOW_HOME"
mkdir -p /tmp/airflow_demo

#  Step 1: Install Airflow 
info "Installing Apache Airflow 2.9.1 (this may take a few minutes)..."
pip install --quiet \
  "apache-airflow==2.9.1" \
  "requests==2.31.0" \
  --constraint "$CONSTRAINT_URL"
info "Airflow installed successfully."

# Step 2: Initialise the metadata database 
info "Initialising Airflow database..."
airflow db migrate
info "Database ready."

#  Step 3: Create admin user 
info "Creating admin user (admin/admin)..."
airflow users create \
  --username admin \
  --password admin \
  --firstname Admin \
  --lastname User \
  --role Admin \
  --email admin@example.com 2>/dev/null || warn "User already exists, skipping."

#  Step 4: Kill any stale Airflow processes 
info "Cleaning up any previous Airflow processes..."
pkill -f "airflow scheduler" 2>/dev/null || true
pkill -f "airflow webserver" 2>/dev/null || true
sleep 2

# Step 5: Start scheduler in background 
info "Starting Airflow scheduler in background..."
nohup airflow scheduler \
  > "$AIRFLOW_HOME/scheduler.log" 2>&1 &
SCHEDULER_PID=$!
echo $SCHEDULER_PID > "$AIRFLOW_HOME/scheduler.pid"
info "Scheduler started (PID $SCHEDULER_PID) → logs: $AIRFLOW_HOME/scheduler.log"

#  Step 6: Start webserver in background 
info "Starting Airflow webserver on port 8080..."
nohup airflow webserver --port 8080 \
  > "$AIRFLOW_HOME/webserver.log" 2>&1 &
WEBSERVER_PID=$!
echo $WEBSERVER_PID > "$AIRFLOW_HOME/webserver.pid"
info "Webserver started (PID $WEBSERVER_PID) → logs: $AIRFLOW_HOME/webserver.log"

#  Step 7: Wait for webserver to be ready
info "Waiting for webserver to become ready..."
for i in $(seq 1 30); do
  if curl -s http://localhost:8080/health | grep -q "healthy" 2>/dev/null; then
    break
  fi
  sleep 3
  echo -n "."
done
echo ""

# Step 8: Trigger the DAG once
info "Unpausing and triggering the DAG..."
sleep 5
airflow dags unpause data_pipeline_demo 2>/dev/null || true
airflow dags trigger data_pipeline_demo 2>/dev/null || true

echo ""
echo "Airflow is running!"
echo "  UI    : http://localhost:8080"
echo "  Login : admin / admin"
echo ""
echo "DAG 'data_pipeline_demo' has been triggered."
echo "Watch it run: DAGs -> data_pipeline_demo -> Graph"
echo ""
echo "Output files after the run:"
echo "  cat /tmp/airflow_demo/report.txt"
echo "  cat /tmp/airflow_demo/processed_weather.json"
echo ""
echo "To stop Airflow: ./stop_airflow.sh"
echo ""
