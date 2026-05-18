# Healthstream

Healthstream is a production-style data engineering project that simulates how large healthcare companies process medical insurance claims data every day. The idea behind this project is to build a complete end-to-end data pipeline that mirrors what companies like Cedar Gate Technologies actually do in the real world. Instead of using real patient data, which is protected by privacy laws, the system generates realistic fake data using Python and processes it through a full enterprise-grade technology stack.

The project demonstrates real data engineering skills including real-time streaming, batch processing, data warehousing, REST API development, dashboard visualization, machine learning for fraud detection, and containerized deployment using Docker. Every component in this system is a technology used by actual companies in production environments.

## What problem does this project solve

In healthcare, insurance companies receive millions of claims every day from hospitals and doctors. Each claim says a patient received a certain treatment and the insurance company should pay a certain amount. Processing these claims involves validating the data, detecting fraud, storing records in a warehouse, running daily reports, and showing analytics to business teams. This project builds all of those pieces as one working system.

## How the data flows through the system

The journey of a single claim starts in the data generator. A Python script uses the Faker library to create fake but realistic patient records, hospital records, and insurance claims. Each claim has a patient ID, hospital ID, treatment code, diagnosis code using real ICD-10 medical codes, a claim amount, an approved amount, an insurance status, a timestamp, and a fraud score. About 5 percent of claims are intentionally made fraudulent by inflating the claim amount to 3 to 10 times the normal price. The generator runs continuously and sends 30 new claims every 3 seconds.

These claims go into Apache Kafka, which acts as a message broker. Kafka is like a post office that holds messages safely and delivers them to whoever needs them. The claims land in a topic called raw-claims. A consumer service reads every message from that topic, checks that all required fields are present and the amount is within valid range, and then routes the claim to one of two places. If the fraud score is 0.7 or higher the claim goes to the fraud-alerts topic. If it is clean it goes to the validated-claims topic. This routing happens in real time within milliseconds of the claim arriving.

Apache Spark reads the raw-claims stream continuously. It parses the JSON data, drops any records with missing fields or invalid amounts, adds calculated columns like the approval ratio and a risk flag, and writes the cleaned data to PostgreSQL every 10 seconds. Spark also writes fraud alerts directly to the database for any claim that crosses the fraud threshold. This is the stream processing layer that keeps the database updated in near real time.

PostgreSQL is the data warehouse where everything is stored permanently. It has tables for patients, hospitals, claims, treatments, fraud alerts, and a daily analytics summary. The schema uses proper foreign keys and indexes so queries run fast even with large amounts of data. The database is seeded on first startup with 30 days of historical fake claims so the dashboard has data to show immediately.

Apache Airflow runs four scheduled jobs that keep the warehouse clean and up to date. The daily ETL job runs every morning at 1am and calculates totals for the previous day, updates patient risk scores based on their recent claim history, updates hospital performance scores based on their fraud and denial rates, and resolves old low-severity fraud alerts. The batch processing job runs every 6 hours and applies rule-based fraud detection, flagging claims that are more than 3 times the average cost for their treatment type and flagging patients who submitted more than 5 claims in 24 hours. The reporting job runs every Monday and prints a weekly summary to the logs. The cleanup job runs every Sunday and removes old resolved alerts to keep the database lean.

The FastAPI backend exposes the stored data through REST API endpoints. There are endpoints for fetching the latest claims, getting daily cost trends, viewing fraud alerts and statistics, finding high-risk patients, and comparing hospital performance. The API connects directly to PostgreSQL and returns JSON responses. It also has automatic interactive documentation at the /docs URL where you can test every endpoint in the browser.

The Streamlit dashboard reads from the FastAPI endpoints and shows everything as charts and tables. It has six pages. The overview page shows total claims, total amount, fraud rate, and a 30-day cost trend chart. The cost trends page shows daily claim volumes and amounts over any date range. The fraud detection page shows alerts by severity and type with a filterable table. The hospital performance page ranks hospitals by their performance score. The patient risk page shows patients above a chosen risk threshold. The live claims feed shows the most recent claims coming through the pipeline with fraudulent ones highlighted in red. The dashboard auto-refreshes every 30 seconds so you can watch new data arrive in real time.

## Technologies used and why

Python is the main language because it has the best libraries for data work and is the standard language in data engineering teams.

Apache Kafka is used for streaming because it can handle millions of messages per second, never loses data even if a consumer goes down, and lets multiple services read the same data independently. It is used by companies like LinkedIn, Uber, and Netflix for exactly this purpose.

Apache Spark is used for stream processing because it can process large volumes of data very fast using distributed computing. It handles cleaning, transformation, and enrichment of data before it reaches the database.

Apache Airflow is used for scheduling because it provides a visual interface to monitor jobs, handles retries automatically, and keeps a full history of every run. It is the most widely used workflow orchestration tool in data engineering.

PostgreSQL is used as the data warehouse because it is reliable, supports complex analytical queries, and handles the kind of aggregations and joins this project needs efficiently.

FastAPI is used for the backend because it is fast, automatically generates documentation, and uses Python type hints to validate request and response data automatically.

Streamlit is used for the dashboard because it lets you build interactive web applications in pure Python without needing to know HTML, CSS, or JavaScript.

Docker and Docker Compose are used to package every service into its own container so the entire system starts with one command on any machine. This is how real companies deploy applications so they run the same way in development, testing, and production.

scikit-learn is used to build a Random Forest machine learning model that predicts the probability that a claim is fraudulent based on features like claim amount, approval ratio, insurance type, and hospital type.

## Project structure

    healthstream/
    data-generator    generates fake patients, hospitals, and claims using Faker
                      seeds the database on first startup with 30 days of history
                      streams new claims to Kafka every 3 seconds continuously

    kafka             creates the three Kafka topics on startup
                      consumer validates incoming claims and routes them by fraud score

    spark             streaming job reads raw-claims and writes cleaned data to PostgreSQL
                      batch aggregation job summarizes daily claim totals

    airflow/dags      daily_etl runs every morning to refresh analytics and risk scores
                      batch_processing runs every 6 hours for rule-based fraud detection
                      reporting runs every Monday for weekly KPI summary
                      cleanup runs every Sunday to remove old data

    api               FastAPI application with endpoints for claims, analytics, fraud,
                      patients, and hospitals
                      ML layer with fraud detection model and patient risk scorer

    dashboard         Streamlit app with 6 pages showing live charts and tables

    database          PostgreSQL schema with 6 tables and proper indexes

    kubernetes        deployment manifests for running on a Kubernetes cluster

    tests             unit tests for data generator, ML models, API schemas,
                      and end-to-end integration tests

    docker-compose    wires all 11 services together with health checks and dependencies

## How to run the project

You need Docker and Docker Compose installed on your machine.

    docker-compose up --build

Or using the Makefile:

    make build

The first time this runs it will pull all base images, build the custom service images, start everything in the correct order, seed the database with historical data, and begin streaming new claims. This takes about 5 to 10 minutes on the first run.

After startup open these URLs in your browser:

    Dashboard       http://localhost:8501
    API docs        http://localhost:8000/docs
    Airflow         http://localhost:8080    login: admin / admin123
    Kafka UI        http://localhost:8090

After Airflow starts, add the database connection once:

    make airflow-connection

Or manually:

    docker exec healthstream-airflow-web airflow connections add healthstream_postgres \
      --conn-type postgres --conn-host postgres --conn-login healthstream \
      --conn-password healthstream123 --conn-schema healthstream --conn-port 5432

Then trigger the DAGs:

    make trigger-dags

## How to run tests

    pip install -r tests/requirements.txt
    pytest tests/ -v

## Services and ports

| Service | Port |
|---|---|
| PostgreSQL | 5432 |
| Kafka | 9092 internal, 29092 host |
| Airflow | 8080 |
| FastAPI | 8000 |
| Streamlit | 8501 |
| Kafka UI | 8090 |
