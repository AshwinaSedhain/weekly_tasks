# Aggregate yesterday's claims and write a summary row to analytics_summary.
import os
import logging
from datetime import datetime, timedelta

from pyspark.sql import SparkSession
from pyspark.sql import functions as F

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

DB_URL      = os.getenv("DB_URL",      "jdbc:postgresql://postgres:5432/healthstream")
DB_USER     = os.getenv("DB_USER",     "healthstream")
DB_PASSWORD = os.getenv("DB_PASSWORD", "healthstream123")
DB_DRIVER   = "org.postgresql.Driver"


def create_spark_session() -> SparkSession:
    return (
        SparkSession.builder
        .appName("Healthstream-BatchAggregation")
        .config("spark.jars.packages", "org.postgresql:postgresql:42.7.1")
        .getOrCreate()
    )


def read_claims(spark: SparkSession, target_date: str):
    return (
        spark.read
        .format("jdbc")
        .option("url",      DB_URL)
        .option("dbtable",  "claims")
        .option("user",     DB_USER)
        .option("password", DB_PASSWORD)
        .option("driver",   DB_DRIVER)
        .load()
        .filter(F.to_date("claim_date") == target_date)
    )


def aggregate_daily(claims_df, target_date: str):
    return (
        claims_df.agg(
            F.count("*").alias("total_claims"),
            F.sum("claim_amount").alias("total_amount"),
            F.sum(F.when(F.col("insurance_status") == "APPROVED", 1).otherwise(0)).alias("approved_claims"),
            F.sum(F.when(F.col("insurance_status") == "DENIED",   1).otherwise(0)).alias("denied_claims"),
            F.sum(F.when(F.col("is_fraud"), 1).otherwise(0)).alias("fraud_detected"),
            F.avg("claim_amount").alias("avg_claim_amount"),
        )
        .withColumn("summary_date", F.lit(target_date))
    )


def write_summary(summary_df):
    (
        summary_df.write
        .format("jdbc")
        .option("url",      DB_URL)
        .option("dbtable",  "analytics_summary")
        .option("user",     DB_USER)
        .option("password", DB_PASSWORD)
        .option("driver",   DB_DRIVER)
        .mode("append")
        .save()
    )
    logger.info("Analytics summary written")


def run(target_date: str = None):
    if not target_date:
        target_date = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")

    spark = create_spark_session()
    spark.sparkContext.setLogLevel("WARN")

    logger.info("Running batch aggregation for date: %s", target_date)
    claims_df  = read_claims(spark, target_date)
    summary_df = aggregate_daily(claims_df, target_date)
    write_summary(summary_df)

    spark.stop()
    logger.info("Batch aggregation complete for %s", target_date)


if __name__ == "__main__":
    import sys
    date_arg = sys.argv[1] if len(sys.argv) > 1 else None
    run(date_arg)
