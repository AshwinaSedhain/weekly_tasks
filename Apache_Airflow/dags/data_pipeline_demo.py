# Importing all the necessary libraries for building the pipeline.
# json handles reading and writing JSON files, logging helps us print
# messages during each task, os lets us work with file paths and folders,
# datetime helps us set dates and time delays, requests is used for
# calling the weather API, and the airflow imports bring in the DAG
# and operator tools we need to build the pipeline.

import json
import logging
import os
from datetime import datetime, timedelta

import requests

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator

# Defining the file paths where we are storing the data at each stage
# of the pipeline. The raw file holds the original API response, the
# processed file holds the cleaned and summarised data, and the report
# file holds the final human-readable summary.
RAW_DATA_PATH = "/tmp/airflow_demo/raw_weather.json"
PROCESSED_DATA_PATH = "/tmp/airflow_demo/processed_weather.json"
REPORT_PATH = "/tmp/airflow_demo/report.txt"

# Setting up the URL for the Open-Meteo weather API. This URL is
# pointing to New York City coordinates and asking for hourly
# temperature readings for today. No API key is needed for this service.
WEATHER_API_URL = (
    "https://api.open-meteo.com/v1/forecast"
    "?latitude=40.7128&longitude=-74.0060"
    "&hourly=temperature_2m"
    "&temperature_unit=celsius"
    "&forecast_days=1"
)

# Defining the default arguments that apply to every task in the DAG.
# These settings are controlling things like who owns the DAG, how many
# times a failing task should retry, how long to wait between retries,
# and whether to send emails on failure. Setting retries to 3 means
# Airflow is automatically trying again up to 3 times before marking
# a task as failed.
default_args = {
    "owner": "airflow_demo",
    "depends_on_past": False,
    "email": ["admin@example.com"],
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 3,
    "retry_delay": timedelta(minutes=2),
    "retry_exponential_backoff": True,
    "execution_timeout": timedelta(minutes=10),
}

# Creating the DAG object and giving it a name, description, and schedule.
# Setting schedule_interval to @daily means Airflow is running this
# pipeline once every day at midnight UTC. Setting catchup to False means
# Airflow is not going back and running all the missed days since the
# start date. The tags are helping us filter and find this DAG easily
# in the Airflow UI.
with DAG(
    dag_id="data_pipeline_demo",
    description="Real-world weather data pipeline – fetch, process, save, report",
    default_args=default_args,
    schedule_interval="@daily",
    start_date=datetime(2025, 1, 1),
    catchup=False,
    max_active_runs=1,
    tags=["demo", "weather", "pipeline"],
) as dag:

    # -------------------------------------------------------------------
    # TASK 1 — fetch_data (PythonOperator)
    # -------------------------------------------------------------------

    # Defining the function that is fetching live weather data from the
    # Open-Meteo API. This function is making an HTTP GET request to the
    # API URL, checking that the response is valid, and then saving the
    # raw JSON data to a file in the /tmp folder. It is also pushing the
    # file path into XCom so the next task can find and read the file
    # without needing to hard-code the path again.
    def fetch_data(**context):

        log = logging.getLogger(__name__)
        log.info("Starting fetch_data task")
        log.info("Calling weather API at URL: %s", WEATHER_API_URL)

        # Creating the output directory if it does not already exist
        # so we have a place to save the raw data file.
        os.makedirs(os.path.dirname(RAW_DATA_PATH), exist_ok=True)

        # Sending the API request and catching specific errors so we
        # can log a clear message explaining what went wrong instead
        # of showing a confusing traceback.
        try:
            response = requests.get(WEATHER_API_URL, timeout=30)
            response.raise_for_status()
        except requests.exceptions.Timeout:
            log.error("The API request timed out after waiting 30 seconds")
            raise
        except requests.exceptions.HTTPError as exc:
            log.error("The API returned an HTTP error: %s", exc)
            raise
        except requests.exceptions.RequestException as exc:
            log.error("A network error occurred while calling the API: %s", exc)
            raise

        data = response.json()
        log.info(
            "Successfully received %d hourly temperature readings from the API",
            len(data.get("hourly", {}).get("temperature_2m", [])),
        )

        # Writing the raw API response to a JSON file so the next task
        # can read it. Using indent=2 makes the file easy to read.
        with open(RAW_DATA_PATH, "w") as f:
            json.dump(data, f, indent=2)

        log.info("Saving raw data to file: %s", RAW_DATA_PATH)

        # Pushing the file path into XCom so the process_data task can
        # pull it and know exactly where to find the raw data file.
        context["ti"].xcom_push(key="raw_data_path", value=RAW_DATA_PATH)
        return RAW_DATA_PATH

    task_fetch_data = PythonOperator(
        task_id="fetch_data",
        python_callable=fetch_data,
    )

    # -------------------------------------------------------------------
    # TASK 2 — process_data (PythonOperator)
    # -------------------------------------------------------------------

    # Defining the function that is reading the raw weather data and
    # transforming it into something more useful. This function is pulling
    # the file path from XCom, loading the raw JSON, calculating the
    # minimum, maximum, and average temperature for the day, and then
    # saving the cleaned and summarised data to a new file. It is also
    # pushing the statistics into XCom so the report task can use them.
    def process_data(**context):

        log = logging.getLogger(__name__)
        log.info("Starting process_data task")

        # Pulling the raw data file path that fetch_data pushed into XCom
        # so we know where to read the data from.
        raw_path = context["ti"].xcom_pull(
            task_ids="fetch_data", key="raw_data_path"
        )
        log.info("Reading raw data from: %s", raw_path)

        # Checking that the file actually exists before trying to open it
        # so we get a clear error message if something went wrong earlier.
        if not os.path.exists(raw_path):
            raise FileNotFoundError(f"Raw data file not found at path: {raw_path}")

        with open(raw_path) as f:
            raw = json.load(f)

        hourly = raw.get("hourly", {})
        times = hourly.get("time", [])
        temps = hourly.get("temperature_2m", [])

        if not temps:
            raise ValueError("No temperature readings found in the API response")

        # Filtering out any None values that the API sometimes returns
        # for future hours that have not happened yet.
        valid_temps = [t for t in temps if t is not None]

        # Building the processed data dictionary that holds the location
        # info, all hourly readings, and the computed statistics.
        processed = {
            "location": {
                "latitude": raw.get("latitude"),
                "longitude": raw.get("longitude"),
                "timezone": raw.get("timezone"),
            },
            "date": times[0][:10] if times else "unknown",
            "unit": raw.get("hourly_units", {}).get("temperature_2m", "°C"),
            "hourly_readings": [
                {"time": t, "temperature": v} for t, v in zip(times, temps)
            ],
            "statistics": {
                "min_temp": round(min(valid_temps), 2),
                "max_temp": round(max(valid_temps), 2),
                "avg_temp": round(sum(valid_temps) / len(valid_temps), 2),
                "total_readings": len(valid_temps),
            },
            "processed_at": datetime.utcnow().isoformat(),
        }

        log.info(
            "Computed statistics — min: %.1f°C, max: %.1f°C, avg: %.1f°C",
            processed["statistics"]["min_temp"],
            processed["statistics"]["max_temp"],
            processed["statistics"]["avg_temp"],
        )

        # Saving the processed data to a new file so the save_data task
        # can pick it up and store it in the database.
        os.makedirs(os.path.dirname(PROCESSED_DATA_PATH), exist_ok=True)
        with open(PROCESSED_DATA_PATH, "w") as f:
            json.dump(processed, f, indent=2)

        log.info("Saving processed data to file: %s", PROCESSED_DATA_PATH)

        # Pushing both the file path and the statistics dictionary into
        # XCom so the downstream tasks can access them without re-reading
        # the file.
        context["ti"].xcom_push(key="processed_data_path", value=PROCESSED_DATA_PATH)
        context["ti"].xcom_push(key="statistics", value=processed["statistics"])
        return PROCESSED_DATA_PATH

    task_process_data = PythonOperator(
        task_id="process_data",
        python_callable=process_data,
    )

    # -------------------------------------------------------------------
    # TASK 3 — save_data (PythonOperator)
    # -------------------------------------------------------------------

    # Defining the function that is simulating saving data to a database.
    # Instead of a real database, we are appending each processed record
    # as a new line in a .ndjson file (newline-delimited JSON). This is a
    # simple and readable way to show how data accumulates over multiple
    # daily runs. In a real project this could be replaced with a
    # PostgresOperator or SQLAlchemy insert.
    def save_data(**context):

        log = logging.getLogger(__name__)
        log.info("Starting save_data task")

        # Pulling the processed data file path from XCom so we know
        # which file to read and store.
        processed_path = context["ti"].xcom_pull(
            task_ids="process_data", key="processed_data_path"
        )
        log.info("Loading processed data from: %s", processed_path)

        if not os.path.exists(processed_path):
            raise FileNotFoundError(f"Processed data file not found at: {processed_path}")

        with open(processed_path) as f:
            record = json.load(f)

        # Appending the record as a new line in the NDJSON file. Each
        # daily run is adding one line so we can track all historical runs.
        db_path = "/tmp/airflow_demo/weather_db.ndjson"
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

        with open(db_path, "a") as db:
            db.write(json.dumps(record) + "\n")

        log.info("Appending record to data store: %s", db_path)

        # Counting how many records are now in the file so we can log
        # the total and pass it to the report task.
        with open(db_path) as db:
            total = sum(1 for _ in db)
        log.info("Total records now stored in the data file: %d", total)

        context["ti"].xcom_push(key="db_path", value=db_path)
        context["ti"].xcom_push(key="total_records", value=total)
        return db_path

    task_save_data = PythonOperator(
        task_id="save_data",
        python_callable=save_data,
    )

    # -------------------------------------------------------------------
    # TASK 4 — generate_report (PythonOperator)
    # -------------------------------------------------------------------

    # Defining the function that is building the final human-readable
    # report. This function is pulling the statistics and total record
    # count from XCom and formatting them into a clean text file. The
    # report is also printed to the Airflow task log so it is visible
    # directly in the UI without needing to open the file manually.
    def generate_report(**context):

        log = logging.getLogger(__name__)
        log.info("Starting generate_report task")

        # Pulling the statistics dictionary and total record count that
        # were pushed into XCom by the earlier tasks.
        stats = context["ti"].xcom_pull(task_ids="process_data", key="statistics")
        total_records = context["ti"].xcom_pull(task_ids="save_data", key="total_records")

        # Getting the logical execution date from the Airflow context so
        # we can include it in the report header.
        execution_date = context.get("ds", "unknown")

        if not stats:
            raise ValueError("No statistics found in XCom — process_data may have failed")

        # Building the report as a list of lines and then joining them
        # into a single string for writing to the file.
        report_lines = [
            "=" * 60,
            "  WEATHER DATA PIPELINE – DAILY REPORT",
            "=" * 60,
            f"  Execution date  : {execution_date}",
            f"  Generated at    : {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC",
            "-" * 60,
            "  TEMPERATURE SUMMARY (New York City, °C)",
            f"    Minimum  : {stats['min_temp']} °C",
            f"    Maximum  : {stats['max_temp']} °C",
            f"    Average  : {stats['avg_temp']} °C",
            f"    Readings : {stats['total_readings']}",
            "-" * 60,
            f"  Total records in store : {total_records}",
            "=" * 60,
            "",
        ]

        report_text = "\n".join(report_lines)

        # Printing the full report to the Airflow task log so it shows
        # up in the UI when clicking on this task's logs.
        log.info("\n%s", report_text)

        # Writing the report to a text file so it can be read from the
        # terminal or shared with others after the pipeline finishes.
        os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)
        with open(REPORT_PATH, "w") as f:
            f.write(report_text)

        log.info("Writing report to file: %s", REPORT_PATH)
        return REPORT_PATH

    task_generate_report = PythonOperator(
        task_id="generate_report",
        python_callable=generate_report,
    )

    # -------------------------------------------------------------------
    # BONUS TASK 5 — notify_success (BashOperator)
    # -------------------------------------------------------------------

    # Using a BashOperator to simulate sending a success notification
    # after the pipeline finishes. This task is reading the report file
    # using the cat command and printing it to the Airflow log along with
    # a timestamp. In a real project this could be replaced with a curl
    # command posting to a Slack webhook or sending an email alert.
    task_notify_success = BashOperator(
        task_id="notify_success",
        bash_command=(
            "echo '--- Pipeline completed successfully ---' && "
            "cat /tmp/airflow_demo/report.txt && "
            "echo 'Notification sent at: ' $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
        ),
        retries=1,
        retry_delay=timedelta(seconds=30),
    )

    # Defining the order in which the tasks are running. The >> operator
    # is telling Airflow that each task must finish successfully before
    # the next one starts. This creates the linear pipeline flow:
    # fetch the data, then process it, then save it, then generate the
    # report, and finally send the success notification.
    task_fetch_data >> task_process_data >> task_save_data >> task_generate_report >> task_notify_success
