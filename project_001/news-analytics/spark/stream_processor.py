# This file is implementing the Spark Structured Streaming job. It is reading raw
# news articles from the Kafka raw-news topic, cleaning the text by removing HTML
# tags and extra whitespace, adding a processed timestamp, and writing the enriched
# records back to the processed-news Kafka topic and to PostgreSQL.

import json
import logging
import os

from pyspark.sql import SparkSession, DataFrame
from pyspark.sql import functions as F
from pyspark.sql.types import (
    StructType, StructField, StringType, IntegerType, FloatType
)

logger = logging.getLogger(__name__)

KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
POSTGRES_URL = os.getenv("POSTGRES_URL", "jdbc:postgresql://localhost:5432/newsdb")
POSTGRES_USER = os.getenv("POSTGRES_USER", "newsuser")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "newspass")

# Defining the schema that matches the article format produced by the scrapers.
# Spark needs this to parse the JSON payload from each Kafka message.
ARTICLE_SCHEMA = StructType([
    StructField("id", StringType(), True),
    StructField("title", StringType(), True),
    StructField("description", StringType(), True),
    StructField("content", StringType(), True),
    StructField("url", StringType(), True),
    StructField("author", StringType(), True),
    StructField("source_name", StringType(), True),
    StructField("published_at", StringType(), True),
    StructField("collected_at", StringType(), True),
    StructField("source", StringType(), True),
    StructField("category", StringType(), True),
    StructField("score", IntegerType(), True),
    StructField("comments", IntegerType(), True),
])


def build_spark_session() -> SparkSession:
    # Creating and returning a SparkSession configured for Kafka integration.
    # Setting the Kafka and PostgreSQL connector packages so Spark can read
    # from and write to those systems.
    return (
        SparkSession.builder
        .appName("NewsStreamProcessor")
        .config(
            "spark.jars.packages",
            "org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.1,"
            "org.postgresql:postgresql:42.6.0",
        )
        .config("spark.sql.shuffle.partitions", "4")
        .getOrCreate()
    )


def read_kafka_stream(spark: SparkSession) -> DataFrame:
    # Creating a streaming DataFrame that reads from the raw-news Kafka topic.
    # Parsing the JSON value of each Kafka message using the predefined schema.
    raw_df = (
        spark.readStream
        .format("kafka")
        .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP)
        .option("subscribe", "raw-news")
        .option("startingOffsets", "latest")
        .load()
    )

    parsed_df = raw_df.select(
        F.from_json(
            F.col("value").cast("string"), ARTICLE_SCHEMA
        ).alias("data")
    ).select("data.*")

    return parsed_df


def clean_text(df: DataFrame) -> DataFrame:
    # Cleaning the title and content columns by removing HTML tags and extra
    # whitespace. Clean text produces better keyword extraction and sentiment
    # scores downstream.
    df = df.withColumn(
        "title_clean",
        F.regexp_replace(F.col("title"), r"<[^>]+>", "")
    )
    df = df.withColumn(
        "title_clean",
        F.regexp_replace(F.col("title_clean"), r"\s+", " ")
    )
    df = df.withColumn(
        "content_clean",
        F.regexp_replace(F.col("content"), r"<[^>]+>", "")
    )
    df = df.withColumn(
        "content_clean",
        F.regexp_replace(F.col("content_clean"), r"\s+", " ")
    )
    return df


def add_processing_timestamp(df: DataFrame) -> DataFrame:
    # Adding a processed_at column with the current UTC timestamp so we can
    # measure pipeline latency later.
    return df.withColumn("processed_at", F.current_timestamp())


def write_to_kafka(df: DataFrame) -> None:
    # Writing the processed DataFrame back to the processed-news Kafka topic.
    # Serializing each row as JSON so downstream consumers receive the same
    # format as the raw topic.
    kafka_df = df.select(
        F.col("id").alias("key"),
        F.to_json(F.struct("*")).alias("value"),
    )
    (
        kafka_df.writeStream
        .format("kafka")
        .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP)
        .option("topic", "processed-news")
        .option("checkpointLocation", "/tmp/spark-checkpoints/processed-news")
        .start()
    )


def write_to_postgres(df: DataFrame) -> None:
    # Writing each micro-batch of processed articles to the PostgreSQL articles
    # table using the foreachBatch pattern. Using append mode so existing rows
    # are never overwritten.
    def write_batch(batch_df: DataFrame, batch_id: int) -> None:
        (
            batch_df.write
            .format("jdbc")
            .option("url", POSTGRES_URL)
            .option("dbtable", "articles")
            .option("user", POSTGRES_USER)
            .option("password", POSTGRES_PASSWORD)
            .option("driver", "org.postgresql.Driver")
            .mode("append")
            .save()
        )
        logger.info("Writing batch %d to PostgreSQL", batch_id)

    (
        df.writeStream
        .foreachBatch(write_batch)
        .option("checkpointLocation", "/tmp/spark-checkpoints/postgres")
        .start()
    )


def run() -> None:
    # Main entry point for the Spark streaming job. Building the session, reading
    # from Kafka, applying all transformations, writing outputs, and waiting for
    # the streams to terminate.
    spark = build_spark_session()
    spark.sparkContext.setLogLevel("WARN")

    raw_df = read_kafka_stream(spark)
    cleaned_df = clean_text(raw_df)
    final_df = add_processing_timestamp(cleaned_df)

    write_to_kafka(final_df)
    write_to_postgres(final_df)

    spark.streams.awaitAnyTermination()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
