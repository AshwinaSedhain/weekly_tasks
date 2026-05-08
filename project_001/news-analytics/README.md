# Real-Time News Analytics and Intelligent Data Pipeline System

## What This Project Is

This project is a complete real-time news analytics system. It automatically collects news articles from two websites every 30 minutes, processes them using machine learning to understand their meaning and sentiment, stores them in databases, and displays everything on a live dashboard that updates itself automatically. The entire system runs inside Docker containers so you can start everything with a single command.

The goal of this project is to show how a modern big data pipeline works from start to finish. It covers data collection, message streaming, data processing, machine learning, REST APIs, live dashboards, workflow automation, containerization, cloud deployment, and automated testing all in one place.

## Where the Data Comes From

The system collects news from two sources.

The first source is NewsAPI, which is available at https://newsapi.org. NewsAPI is a service that gives access to news articles from thousands of newspapers and websites around the world through a simple HTTP API. We call two of its endpoints. The top-headlines endpoint gives us the most popular current stories in the technology category from the United States. The everything endpoint lets us search for articles matching keywords like technology, AI, and startup. Both calls return structured JSON data so no HTML parsing is needed.

The second source is Hacker News, which is available at https://news.ycombinator.com. Hacker News is a popular technology news community run by Y Combinator where programmers and tech enthusiasts share and discuss interesting articles. We use the official Hacker News Firebase REST API at https://hacker-news.firebaseio.com/v0 rather than scraping the HTML directly. We first fetch the list of top story IDs, then download each story's details in parallel using multiple threads so the collection finishes quickly.

Both sources return data in different formats. We normalize everything into the same standard article shape so the rest of the pipeline does not need to know which source an article came from.

## System Architecture and Data Flow

The diagram below shows how data moves through the entire system from collection to display.

```
NewsAPI  ──┐
           ├──> NewsCollector ──> Kafka (raw-news) ──> Spark Streaming ──> Kafka (processed-news)
HackerNews─┘                           │                                          │
                                       │                                          ├──> PostgreSQL
                                  MongoDB                                         └──> PostgreSQL
                                 (raw storage)
                                                                                  FastAPI Backend
                                                                                        │
                                                                                 Dash Dashboard
```

The collection layer fetches articles from both sources and stores raw documents in MongoDB. Kafka acts as the message bus carrying articles from the collector to the Spark job. Spark cleans the text and writes processed articles to PostgreSQL. The FastAPI backend reads from PostgreSQL and MongoDB to serve the dashboard. The dashboard polls the API every 30 seconds and renders live charts.

## How the System Works Step by Step

When the system is running, here is what happens every 30 minutes automatically.

Airflow triggers the collection pipeline. The collector fetches articles from both NewsAPI and Hacker News, removes any duplicates it has already seen, and stores the raw articles in MongoDB. Then the ML pipeline runs on each article to add sentiment scores and keywords. The enriched articles are stored in PostgreSQL. At the same time the articles are published to a Kafka topic so the Spark streaming job can pick them up. The FastAPI backend reads from PostgreSQL and MongoDB to serve data to the dashboard. The dashboard refreshes every 30 seconds so users always see the latest information.

## What Each Folder Does

The scraper folder contains all the code for collecting data. The newsapi_client.py file handles connecting to NewsAPI and fetching articles. The hackernews_scraper.py file handles fetching stories from Hacker News using their Firebase API. The deduplicator.py file keeps track of which articles have already been seen and filters out duplicates. The collector.py file combines all three into one simple collect method that the rest of the system calls.

The kafka folder contains the message streaming code. The producer.py file takes articles and publishes them to Kafka topics as JSON messages. The consumer.py file reads messages from Kafka topics and passes them to a handler function. The topics.py file creates the three Kafka topics the pipeline uses which are raw-news for incoming articles, processed-news for enriched articles, and error-events for failed messages.

The spark folder contains the Spark Structured Streaming job. The stream_processor.py file reads from the raw-news Kafka topic, cleans the article text by removing HTML tags and extra whitespace, adds a processing timestamp, and writes the results back to Kafka and to PostgreSQL. Spark handles this as a continuous stream so it processes new articles as soon as they arrive.

The ml folder contains all the machine learning code. The sentiment.py file uses the VADER lexicon from NLTK to label each article as positive, negative, or neutral based on the words in its title and description. The keywords.py file extracts the most important words from each article by removing common stop words and counting the remaining word frequencies. The clustering.py file groups similar articles together using K-Means on TF-IDF vectors so related stories are automatically categorized. The trends.py file detects which keywords are growing in popularity by comparing counts across two rolling time windows. The pipeline.py file combines all four components into one class so the rest of the system only needs to call one method to get fully enriched articles.

The api folder contains the FastAPI backend. The main.py file creates the application, registers all routes, and initializes the database connections on startup. The routers folder contains four files. The news.py file handles the /news/latest and /news/search endpoints for fetching and searching articles. The analytics.py file handles the /analytics/sentiment, /analytics/trends, and /analytics/sources endpoints for chart data. The scrape.py file handles the /scrape/run endpoint that triggers an on-demand collection and the /scrape/debug endpoint for troubleshooting. The metrics.py file handles the /metrics/live endpoint that returns system health statistics. The database folder contains postgres.py which manages the PostgreSQL connection pool and all insert and query functions, and mongo.py which manages the MongoDB connection and raw document storage.

The dashboard folder contains the Dash web application. The app.py file defines the entire dashboard layout and all the callbacks that fetch data from the API every 30 seconds. It shows three metric cards at the top for total articles, articles today, and API uptime. Below that is a sentiment pie chart showing the proportion of positive, negative, and neutral news. Next to it is a trending keywords bar chart showing the most frequent keywords across all articles. Below that is a source distribution bar chart showing how many articles came from each data source. At the bottom is a live news feed table where positive articles are highlighted green and negative articles are highlighted red.

The airflow folder contains the workflow automation code. The dags folder has two files. The news_collection_dag.py file defines the DAG that runs every 30 minutes and has three tasks in sequence: collect_news fetches from both sources and stores in MongoDB, run_ml_pipeline loads the articles and runs sentiment and keyword analysis and stores in PostgreSQL, and publish_to_kafka sends the articles to the Kafka topic. The cleanup_dag.py file defines the DAG that runs every night at 2am and deletes articles older than 30 days from both PostgreSQL and MongoDB to keep the databases lean.

The docker folder contains the Dockerfiles for building each service image. Dockerfile.api builds the FastAPI service image. Dockerfile.dashboard builds the Dash dashboard image. Dockerfile.spark builds the Spark streaming job image. Dockerfile.airflow builds the Airflow scheduler and webserver image.

The kubernetes folder contains the Kubernetes deployment manifests for running the system on a cloud cluster. It has separate files for each service including deployments, services, persistent volume claims, a configmap for environment variables, and a secrets file for sensitive values. The api-deployment.yaml also includes a HorizontalPodAutoscaler that automatically scales the API pods up to 6 replicas when CPU usage exceeds 70 percent.

The tests folder contains all the automated tests. The unit folder has test_scraper.py which tests the NewsAPI client and Hacker News scraper normalization logic and the deduplicator filtering. The test_ml.py file tests all ML components including sentiment analysis, keyword extraction, clustering, trend detection, and the full pipeline. The test_api.py file tests all FastAPI endpoints using a test client with mocked database calls. The test_data_validation.py file verifies that both data sources produce articles with the same schema and correct field types. The integration folder has test_pipeline.py which tests the full data flow from collection through ML to database storage using real database connections.

The requirements folder contains separate dependency files for each service so each Docker image only installs what it actually needs. The api.txt file lists dependencies for the FastAPI service. The dashboard.txt file lists dependencies for the Dash dashboard. The airflow.txt file lists dependencies for the Airflow containers. The test.txt file lists dependencies for running the test suite.

The .github/workflows folder contains the CI/CD pipeline definition in ci.yml. This file tells GitHub Actions to run automatically on every push to the main branch. It first runs flake8 to check code style and pytest to run all tests. If the tests pass it builds all four Docker images and pushes them to DockerHub. Then it applies the Kubernetes manifests to deploy the updated images to the cluster and waits for the rollout to complete.

## How to Run the Project

Before starting you need to copy the environment file and add your NewsAPI key.

```bash
cp .env.example .env
```

Open the .env file and replace the placeholder with your actual NewsAPI key from https://newsapi.org/register. The free tier gives 100 requests per day which is enough for development.

Start all services with one command.

```bash
docker compose up --build
```

This will download all the base images and build the custom ones. The first time takes about 10 minutes. After that it uses cached layers and starts in under a minute.

Once everything is running you can access the services at these addresses.

The FastAPI documentation is at http://localhost:8000/docs where you can see and test all endpoints interactively.

The live dashboard is at http://localhost:8050 where you can see all the charts and the news feed.

The Airflow scheduler UI is at http://localhost:8080 where you can monitor and trigger the DAGs. The username is admin and the password is admin. If the login fails run this command to create the user manually.

```bash
docker exec news-analytics-airflow-webserver-1 airflow users create \
  --username admin --password admin \
  --firstname Admin --lastname User \
  --role Admin --email admin@example.com
```

To trigger an immediate data collection without waiting for the 30 minute schedule run this command.

```bash
curl -X POST http://localhost:8000/scrape/run
```

To check how many articles have been collected run this command.

```bash
curl http://localhost:8000/metrics/live
```

To stop everything run this command.

```bash
docker compose down
```

To stop and also delete all stored data run this command.

```bash
docker compose down -v
```

## How to Run the Tests

Install the test dependencies and run the unit tests.

```bash
pip install -r requirements/test.txt
pytest tests/unit/ -v
```

To run the integration tests you need the databases running. Start them first with docker compose then run.

```bash
pytest tests/integration/ -v
```

## Environment Variables

The .env file controls how all services connect to each other. The NEWSAPI_KEY variable is your API key from newsapi.org and is the only value you need to get from outside. The KAFKA_BOOTSTRAP_SERVERS variable tells services where to find the Kafka broker. The POSTGRES variables control the database connection. The MONGO_URI variable is the MongoDB connection string. The API_BASE_URL variable tells the dashboard where to find the FastAPI backend.

## Technologies Used

Python 3.11 is the main programming language used across all services. FastAPI is the web framework for the REST API. Apache Kafka handles message streaming between the collection layer and the processing layer. Apache Spark handles the streaming data processing job. PostgreSQL stores the structured analytics data. MongoDB stores the raw article documents. Dash and Plotly build the live dashboard. Apache Airflow schedules and orchestrates the pipeline. Docker packages every service into containers. Kubernetes deploys the containers to a cloud cluster with autoscaling. GitHub Actions runs the CI/CD pipeline automatically. NLTK with the VADER lexicon performs sentiment analysis. scikit-learn provides the TF-IDF vectorizer and K-Means clustering. psycopg2 connects Python to PostgreSQL. pymongo connects Python to MongoDB. kafka-python connects Python to Kafka. requests handles all HTTP calls to the news APIs.
