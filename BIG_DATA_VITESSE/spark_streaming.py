"""
Spark Structured Streaming - Speed Layer
Reads from Kafka, parses JSON, shows:
  - 10-second windowed event counts per user
  - Real-time purchase events filter
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json, window, count, to_timestamp
from pyspark.sql.types import StructType, StructField, StringType

KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"
TOPIC = "user_events"

EVENT_SCHEMA = StructType([
    StructField("user_id",    StringType(), True),
    StructField("event_type", StringType(), True),
    StructField("timestamp",  StringType(), True),
    StructField("session_id", StringType(), True),
    StructField("page",       StringType(), True),
])

spark = (
    SparkSession.builder
    .appName("UserActivity-SpeedLayer")
    .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0")
    .config("spark.sql.shuffle.partitions", "4")
    .getOrCreate()
)
spark.sparkContext.setLogLevel("WARN")

raw = (
    spark.readStream
    .format("kafka")
    .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVERS)
    .option("subscribe", TOPIC)
    .option("startingOffsets", "latest")
    .option("failOnDataLoss", "false")
    .load()
)

parsed = (
    raw
    .select(from_json(col("value").cast("string"), EVENT_SCHEMA).alias("d"))
    .select("d.*")
    .withColumn("event_time", to_timestamp(col("timestamp")))
    .filter(col("user_id").isNotNull())
)

# Query 1: 10-second windowed counts
windowed = (
    parsed
    .withWatermark("event_time", "10 seconds")
    .groupBy(window(col("event_time"), "10 seconds"), col("user_id"), col("event_type"))
    .agg(count("*").alias("event_count"))
)

q1 = (
    windowed.writeStream
    .outputMode("append")
    .format("console")
    .option("truncate", False)
    .option("numRows", 20)
    .trigger(processingTime="10 seconds")
    .start()
)

# Query 2: purchase events only
q2 = (
    parsed
    .filter(col("event_type") == "purchase")
    .writeStream
    .outputMode("append")
    .format("console")
    .option("truncate", False)
    .trigger(processingTime="10 seconds")
    .start()
)

print("\n[Streaming] Running. Ctrl+C to stop.\n")
spark.streams.awaitAnyTermination()
