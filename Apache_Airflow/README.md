# Apache Airflow Data Pipeline Demo

## What is this project

This project is a real-world data pipeline built using Apache Airflow. It fetches live weather data from a public API, processes it, saves it, and generates a daily report. The goal is to show how Airflow works in a simple and practical way that anyone can follow and learn from.

## Why this project exists

Apache Airflow is one of the most widely used tools for automating and scheduling data pipelines in the industry. Understanding how it works is important for anyone getting into data engineering or backend automation. This project demonstrates the core concepts of Airflow including DAGs, operators, task dependencies, scheduling, retries, and monitoring through the UI, all in one working example.

## How it works

The pipeline runs once every day and follows a simple step by step flow. First it calls the Open-Meteo weather API to get hourly temperature data for New York City and saves the raw response to a file. Then it reads that file, calculates the minimum, maximum, and average temperature for the day, and saves the cleaned data to a new file. After that it appends the processed record to a local data store to simulate saving to a database. Finally it generates a human-readable report and prints it to the Airflow logs. A bonus task at the end simulates sending a success notification using a Bash command.

## What it demonstrates

The project covers all the key Airflow concepts in one place. It shows how a DAG is defined and scheduled, how different operators like PythonOperator and BashOperator are used, how tasks pass data to each other using XCom, how retries and error handling are configured, and how the entire pipeline can be monitored visually through the Airflow web UI.

## Project structure

```
Apache_Airflow/
├── dags/
│   └── data_pipeline_demo.py   # the full pipeline with all 5 tasks
├── install_and_run.sh           # automated setup and start script
├── stop_airflow.sh              # script to stop all Airflow processes
├── requirements.txt             # Python dependencies
├── README.md                    # this file
└── .gitignore                   # excludes runtime and cache files
```

## How to run

Make the script executable and run it once. It handles everything automatically including installing Airflow, setting up the database, creating the admin user, and starting the scheduler and webserver in the background.

```bash
chmod +x install_and_run.sh
./install_and_run.sh
```

Once it finishes, open the Airflow UI in your browser and log in with the credentials below.

```
URL   : http://localhost:8080
Login : admin
Password : admin
```

Go to DAGs, click on data_pipeline_demo, then open the Graph tab to watch all five tasks run and turn green one by one.

## How to check the output

After the pipeline finishes running, you can read the generated report directly from the terminal.

```bash
cat /tmp/airflow_demo/report.txt
```

You can also check the other files the pipeline creates along the way.

```bash
cat /tmp/airflow_demo/raw_weather.json        # raw API response
cat /tmp/airflow_demo/processed_weather.json  # cleaned data with statistics
cat /tmp/airflow_demo/weather_db.ndjson       # all daily records stored so far
```

## How to stop

When you are done, run the stop script to shut down the scheduler and webserver cleanly.

```bash
./stop_airflow.sh
```
