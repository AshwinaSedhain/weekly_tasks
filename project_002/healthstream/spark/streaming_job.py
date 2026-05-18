# Read claims from Kafka, clean the data, and write to PostgreSQL and output topics.
import os
import logging
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import (
    StructType, StructField, StringType, DoubleType, BooleanType,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
TOPIC_RAW       = os.getenv("KAFKA_TOPIC_RAW_CLAIMS",       "raw-claims")
TOPIC_VALIDATED = os.getenv("KAFKA_TOPIC_VALIDATED_CLAIMS",  "validated-claims")
TOPIC_FRAUD     = os.getenv("KAFKA_TOPIC_FRAUD_ALERTS",      "fraud-alerts")

DB_URL      = os.getenv("DB_URL",      "jdbc:postgresql://postgres:5432/healthstream")
DB_USER     = os.getenv("DB_USER",     "healthstream")
DB_PASSWORD = os.getenv("DB_PASSWORD", "healthstream123")
DB_DRIVER   = "org.postgresql.Driver"

FRAUD_THRESHOLD = float(os.getenv("FRAUD_THRESHOLD", "0.7"))
CHECKPOINT_DIR  = os.getenv("CHECKPOINT_DIR", "/tmp/spark-checkpoints")

CLAIM_SCHEMA = StructType([
    StructField("claim_id",         StringType(),  True),
    StructField("patient_id",       StringType(),  True),
    StructField("hospital_id",      StringType(),  True),
    StructField("treatment_code",   StringType(),  True),
    StructField("diagnosis_code",   StringType(),  True),
    StructField("claim_amount",     DoubleType(),  True),
    StructField("approved_amount",  DoubleType(),  True),
    StructField("insurance_status", StringType(),  True),
    StructField("claim_date",       StringType(),  True),
    StructField("is_fraud",         BooleanType(), True),
    StructField("fraud_score",      DoubleType(),  True),
    StructField("status",           StringType(),  True),
    StructField("patient_state",    StringType(),  True),
    StructField("insurance_type",   StringType(),  True),
    StructField("hospital_state",   StringType(),  True),
    StructField("hospital_type",    StringType(),  True),
])


def create_spark_session() -> SparkSession:
    return (
        SparkSession.builder
        .appName("Healthstream-Streaming")
        .config(
            "spark.jars.packages",
            "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1,"
            "org.postgresql:postgresql:42.7.1",
        )
        .config("spark.sql.streaming.checkpointLocation", CHECKPOINT_DIR)
        .config("spark.sql.shuffle.partitions", "4")
        .getOrCreate()
    )


def read_kafka_stream(spark: SparkSession):
    return (
        spark.readStream
        .format("kafka")
        .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP)
        .option("subscribe", TOPIC_RAW)
        .option("startingOffsets", "latest")
        .option("failOnDataLoss", "false")
        .load()
    )


def parse_and_clean(raw_df):
    # Parse JSON payload, drop invalid rows, and add derived columns.
    parsed = (
        raw_df
        .select(F.from_json(F.col("value").cast("string"), CLAIM_SCHEMA).alias("data"))
        .select("data.*")
    )

    cleaned = parsed.filter(
        F.col("claim_id").isNotNull()
        & F.col("patient_id").isNotNull()
        & F.col("hospital_id").isNotNull()
        & F.col("claim_amount").isNotNull()
        & (F.col("claim_amount") > 0)
        & (F.col("claim_amount") < 1_000_000)
    )

    enriched = (
        cleaned
        .withColumn("processed_at", F.current_timestamp())
        .withColumn("claim_date_ts", F.to_timestamp("claim_date"))
        .withColumn(
            "approval_ratio",
            F.when(F.col("claim_amount") > 0,
                   F.col("approved_amount") / F.col("claim_amount"))
            .otherwise(0.0),
        )
        .withColumn(
            "risk_flag",
            F.when(F.col("fraud_score") >= FRAUD_THRESHOLD, "HIGH")
             .when(F.col("fraud_score") >= 0.4, "MEDIUM")
             .otherwise("LOW"),
        )
    )

    return enriched


def write_to_postgres(batch_df, batch_id: int):
    # Write each micro-batch to the claims table and insert fraud alerts.
    if batch_df.isEmpty():
        return

    pg_df = (
        batch_df
        .select(
            "claim_id", "patient_id", "hospital_id", "treatment_code",
            "diagnosis_code", "claim_amount", "approved_amount",
            "insurance_status", "claim_date_ts", "is_fraud", "fraud_score", "status",
        )
        .withColumnRenamed("claim_date_ts", "claim_date")
    )

    (
        pg_df.write
        .format("jdbc")
        .option("url",      DB_URL)
        .option("dbtable",  "claims")
        .option("user",     DB_USER)
        .option("password", DB_PASSWORD)
        .option("driver",   DB_DRIVER)
        .mode("append")
        .save()
    )

    fraud_df = (
        batch_df
        .filter(F.col("fraud_score") >= FRAUD_THRESHOLD)
        .select("claim_id", "patient_id", "hospital_id", "fraud_score", "risk_flag")
        .withColumn("alert_reason", F.lit("Fraud score exceeded threshold in Spark job"))
        .withColumn("alert_type",   F.lit("ML_DETECTED"))
        .withColumn("severity",     F.col("risk_flag"))
    )

    if not fraud_df.isEmpty():
        (
            fraud_df
            .select("claim_id", "patient_id", "hospital_id",
                    "fraud_score", "alert_reason", "alert_type", "severity")
            .write
            .format("jdbc")
            .option("url",      DB_URL)
            .option("dbtable",  "fraud_alerts")
            .option("user",     DB_USER)
            .option("password", DB_PASSWORD)
            .option("driver",   DB_DRIVER)
            .mode("append")
            .save()
        )

    logger.info("Batch %d: wrote %d records to PostgreSQL", batch_id, batch_df.count())


def write_to_kafka_validated(df):
    # Forward clean, non-fraudulent claims to the validated-claims topic.
    return (
        df.filter(F.col("fraud_score") < FRAUD_THRESHOLD)
        .select(
            F.col("claim_id").alias("key"),
            F.to_json(F.struct("*")).alias("value"),
        )
        .writeStream
        .format("kafka")
        .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP)
        .option("topic", TOPIC_VALIDATED)
        .option("checkpointLocation", f"{CHECKPOINT_DIR}/validated")
        .start()
    )


def write_to_kafka_fraud(df):
    # Forward high-score claims to the fraud-alerts topic.
    return (
        df.filter(F.col("fraud_score") >= FRAUD_THRESHOLD)
        .select(
            F.col("claim_id").alias("key"),
            F.to_json(F.struct("*")).alias("value"),
        )
        .writeStream
        .format("kafka")
        .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP)
        .option("topic", TOPIC_FRAUD)
        .option("checkpointLocation", f"{CHECKPOINT_DIR}/fraud")
        .start()
    )


def run():
    spark = create_spark_session()
    spark.sparkContext.setLogLevel("WARN")

    logger.info("Starting Spark Structured Streaming job")

    raw_df     = read_kafka_stream(spark)
    cleaned_df = parse_and_clean(raw_df)

    pg_query = (
        cleaned_df.writeStream
        .foreachBatch(write_to_postgres)
        .option("checkpointLocation", f"{CHECKPOINT_DIR}/postgres")
        .trigger(processingTime="10 seconds")
        .start()
    )

    validated_query = write_to_kafka_validated(cleaned_df)
    fraud_query     = write_to_kafka_fraud(cleaned_df)

    logger.info("Streaming queries started, awaiting termination")
    spark.streams.awaitAnyTermination()


if __name__ == "__main__":
    run()
