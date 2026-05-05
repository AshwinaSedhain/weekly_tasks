#!/usr/bin/env bash
# stop_airflow.sh
# ---------------
# Stops the Airflow scheduler and webserver started by install_and_run.sh

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AIRFLOW_HOME="$PROJECT_DIR/airflow_home"

echo "[INFO] Stopping Airflow processes..."

# Stop via saved PID files
for service in scheduler webserver; do
  PID_FILE="$AIRFLOW_HOME/${service}.pid"
  if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if kill -0 "$PID" 2>/dev/null; then
      kill "$PID"
      echo "[INFO] Stopped $service (PID $PID)"
    fi
    rm -f "$PID_FILE"
  fi
done

# Belt-and-suspenders: kill any remaining airflow processes
pkill -f "airflow scheduler" 2>/dev/null || true
pkill -f "airflow webserver" 2>/dev/null || true

echo "[INFO] Airflow stopped."
