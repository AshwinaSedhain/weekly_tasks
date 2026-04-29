"""
Spark Batch Job - Batch Layer
Reads ALL historical events directly from Kafka (no file sink needed).
Produces serving layer summary: total events, purchases, logins per user.
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, count, when, max as spark_max
from pyspark.sql.types import StructType, StructField, StringType

KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"
TOPIC = "user_events"
BATCH_OUTPUT_DIR = "/home/ashwini/Downloads/BIG_DATA_VITESSE/output/batch_results"

EVENT_SCHEMA = StructType([
    StructField("user_id",    StringType(), True),
    StructField("event_type", StringType(), True),
    StructField("timestamp",  StringType(), True),
    StructField("session_id", StringType(), True),
    StructField("page",       StringType(), True),
])

spark = (
    SparkSession.builder
    .appName("UserActivity-BatchLayer")
    .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0")
    .config("spark.sql.shuffle.partitions", "4")
    .getOrCreate()
)
spark.sparkContext.setLogLevel("WARN")

# Read entire Kafka topic as a batch (not streaming)
raw = (
    spark.read
    .format("kafka")
    .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVERS)
    .option("subscribe", TOPIC)
    .option("startingOffsets", "earliest")
    .option("endingOffsets", "latest")
    .load()
)

df = (
    raw
    .select(col("value").cast("string").alias("json"))
    .select(col("json"))
)

from pyspark.sql.functions import from_json
df = (
    raw
    .select(from_json(col("value").cast("string"), EVENT_SCHEMA).alias("d"))
    .select("d.*")
    .filter(col("user_id").isNotNull())
)

total = df.count()
print(f"\n[Batch] Total events loaded from Kafka: {total}\n")

# --- Serving Layer Output 1: User Summary ---
user_summary = (
    df.groupBy("user_id")
    .agg(
        count("*").alias("total_events"),
        count(when(col("event_type") == "purchase", True)).alias("total_purchases"),
        count(when(col("event_type") == "login",    True)).alias("total_logins"),
        count(when(col("event_type") == "click",    True)).alias("total_clicks"),
    )
    .orderBy(col("total_events").desc())
)

print("=" * 60)
print("SERVING LAYER — User Activity Summary")
print("=" * 60)
user_summary.show(truncate=False)

# --- Serving Layer Output 2: Event Type Breakdown ---
event_breakdown = (
    df.groupBy("event_type")
    .agg(count("*").alias("total_count"))
    .orderBy(col("total_count").desc())
)

print("=" * 60)
print("SERVING LAYER — Event Type Breakdown")
print("=" * 60)
event_breakdown.show(truncate=False)

# --- Serving Layer Output 3: Top Pages ---
top_pages = (
    df.groupBy("page")
    .agg(count("*").alias("visit_count"))
    .orderBy(col("visit_count").desc())
)

print("=" * 60)
print("SERVING LAYER — Top Pages")
print("=" * 60)
top_pages.show(truncate=False)

# --- Write CSV results ---
user_summary.coalesce(1).write.mode("overwrite").option("header", True).csv(f"file:///{BATCH_OUTPUT_DIR}/user_summary")
event_breakdown.coalesce(1).write.mode("overwrite").option("header", True).csv(f"file:///{BATCH_OUTPUT_DIR}/event_breakdown")
top_pages.coalesce(1).write.mode("overwrite").option("header", True).csv(f"file:///{BATCH_OUTPUT_DIR}/top_pages")

print(f"\n[Batch] CSV results saved to: {BATCH_OUTPUT_DIR}")
spark.stop()
