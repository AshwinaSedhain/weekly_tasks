#!/usr/bin/env python3

#PySpark ETL Pipeline for E-Commerce Data Processing


from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
import sys
import os

def create_spark_session():
    """
    Create and configure Spark session
    This sets up the Spark context with proper configuration
    """
    print("Creating Spark session...")
    
    spark = SparkSession.builder \
        .appName("EcommerceETLPipeline") \
        .config("spark.master", "local[*]") \
        .config("spark.sql.warehouse.dir", "/user/hive/warehouse") \
        .config("hive.metastore.uris", "thrift://localhost:9083") \
        .enableHiveSupport() \
        .getOrCreate()
    
    # Set log level to reduce noise
    spark.sparkContext.setLogLevel("WARN")
    
    print("Spark session created successfully!")
    return spark

def load_data(spark, hdfs_path):
    """
    Load CSV data from HDFS into Spark DataFrames
    This function reads the raw CSV files and creates DataFrames
    """
    print("Loading data from HDFS...")
    
    # Define the paths to our CSV files in HDFS
    orders_path = f"{hdfs_path}/raw/olist_orders_dataset.csv"
    items_path = f"{hdfs_path}/raw/olist_order_items_dataset.csv"
    customers_path = f"{hdfs_path}/raw/olist_customers_dataset.csv"
    products_path = f"{hdfs_path}/raw/olist_products_dataset.csv"
    
    # Load orders data
    print("Loading orders data...")
    orders_df = spark.read \
        .option("header", "true") \
        .option("inferSchema", "true") \
        .csv(orders_path)
    
    # Load order items data
    print("Loading order items data...")
    items_df = spark.read \
        .option("header", "true") \
        .option("inferSchema", "true") \
        .csv(items_path)
    
    # Load customers data
    print("Loading customers data...")
    customers_df = spark.read \
        .option("header", "true") \
        .option("inferSchema", "true") \
        .csv(customers_path)
    
    # Load products data
    print("Loading products data...")
    products_df = spark.read \
        .option("header", "true") \
        .option("inferSchema", "true") \
        .csv(products_path)
    
    print("Data loading completed!")
    return orders_df, items_df, customers_df, products_df

def data_quality_checks(orders_df, items_df, customers_df, products_df):
    """
    Perform data quality checks
    This function checks for null values and data consistency
    """
    print("Performing data quality checks...")
    
    # Check for null values in each DataFrame
    print("Orders null counts:")
    orders_df.select([count(when(col(c).isNull(), c)).alias(c) for c in orders_df.columns]).show()
    
    print("Items null counts:")
    items_df.select([count(when(col(c).isNull(), c)).alias(c) for c in items_df.columns]).show()
    
    print("Customers null counts:")
    customers_df.select([count(when(col(c).isNull(), c)).alias(c) for c in customers_df.columns]).show()
    
    print("Products null counts:")
    products_df.select([count(when(col(c).isNull(), c)).alias(c) for c in products_df.columns]).show()
    
    # Show basic statistics
    print("Orders dataset shape:", (orders_df.count(), len(orders_df.columns)))
    print("Items dataset shape:", (items_df.count(), len(items_df.columns)))
    print("Customers dataset shape:", (customers_df.count(), len(customers_df.columns)))
    print("Products dataset shape:", (products_df.count(), len(products_df.columns)))

def etl_transformations(orders_df, items_df, customers_df, products_df):
    """
    Perform ETL transformations using Spark DataFrames
    This function demonstrates various DataFrame operations
    """
    print("Starting ETL transformations...")
    
    # 1. Clean and filter orders data - only keep delivered orders
    print("Filtering delivered orders...")
    delivered_orders = orders_df.filter(col("order_status") == "delivered")
    
    # 2. Join orders with items to get complete order information
    print("Joining orders with items...")
    order_items_full = delivered_orders.join(items_df, "order_id", "inner")
    
    # 3. Join with products to get product categories
    print("Joining with products...")
    complete_orders = order_items_full.join(products_df, "product_id", "left")
    
    # 4. Join with customers to get customer information
    print("Joining with customers...")
    final_dataset = complete_orders.join(customers_df, "customer_id", "left")
    
    # 5. Create derived columns
    print("Creating derived columns...")
    final_dataset = final_dataset.withColumn(
        "total_order_value", 
        col("price") + col("freight_value")
    )
    
    # 6. Extract date parts for time-based analysis
    final_dataset = final_dataset.withColumn(
        "order_year",
        year("order_purchase_timestamp")
    ).withColumn(
        "order_month",
        month("order_purchase_timestamp")
    ).withColumn(
        "order_day_of_week",
        dayofweek("order_purchase_timestamp")
    )
    
    # 7. Calculate delivery time in days
    final_dataset = final_dataset.withColumn(
        "delivery_days",
        datediff("order_delivered_customer_date", "order_purchase_timestamp")
    )
    
    print("ETL transformations completed!")
    return final_dataset

def rdd_example(spark, final_dataset):
    """
    Demonstrate RDD operations
    This function shows how to work with RDDs for custom processing
    """
    print("Starting RDD example...")
    
    # Convert DataFrame to RDD for custom processing
    orders_rdd = final_dataset.rdd
    
    # Example 1: Calculate average order value by state using RDD
    print("Calculating average order value by state using RDD...")
    
    state_order_values = orders_rdd \
        .filter(lambda row: row.customer_state is not None) \
        .map(lambda row: (row.customer_state, (row.total_order_value, 1))) \
        .reduceByKey(lambda a, b: (a[0] + b[0], a[1] + b[1])) \
        .map(lambda x: (x[0], x[1][0] / x[1][1])) \
        .sortBy(lambda x: x[1], ascending=False)
    
    print("Top 10 states by average order value:")
    for state, avg_value in state_order_values.take(10):
        print(f"{state}: ${avg_value:.2f}")
    
    # Example 2: Find products with highest freight ratio using RDD
    print("\nFinding products with highest freight ratio...")
    
    freight_ratio = orders_rdd \
        .filter(lambda row: row.price > 0) \
        .map(lambda row: (row.product_id, row.freight_value / row.price)) \
        .groupByKey() \
        .mapValues(lambda values: sum(list(values)) / len(list(values))) \
        .sortBy(lambda x: x[1], ascending=False)
    
    print("Top 5 products with highest freight ratio:")
    for product_id, ratio in freight_ratio.take(5):
        print(f"Product {product_id}: {ratio:.2%}")
    
    print("RDD example completed!")

def create_analytics_tables(spark, final_dataset, hdfs_path):
    """
    Create analytical tables and save results
    This function creates aggregated views and saves them
    """
    print("Creating analytical tables...")
    
    # 1. Monthly sales summary
    print("Creating monthly sales summary...")
    monthly_sales = final_dataset \
        .groupBy("order_year", "order_month") \
        .agg(
            countDistinct("order_id").alias("total_orders"),
            sum("total_order_value").alias("total_revenue"),
            avg("total_order_value").alias("avg_order_value")
        ) \
        .orderBy("order_year", "order_month")
    
    # Save monthly sales to HDFS
    monthly_sales_path = f"{hdfs_path}/processed/monthly_sales"
    monthly_sales.write.mode("overwrite").parquet(monthly_sales_path)
    print(f"Monthly sales saved to: {monthly_sales_path}")
    
    # 2. Product category performance
    print("Creating product category performance...")
    category_performance = final_dataset \
        .filter(col("product_category_name").isNotNull()) \
        .groupBy("product_category_name") \
        .agg(
            countDistinct("product_id").alias("unique_products"),
            countDistinct("order_id").alias("total_orders"),
            sum("total_order_value").alias("total_revenue"),
            avg("price").alias("avg_product_price"),
            avg("delivery_days").alias("avg_delivery_days")
        ) \
        .orderBy(col("total_revenue").desc())
    
    # Save category performance
    category_path = f"{hdfs_path}/processed/category_performance"
    category_performance.write.mode("overwrite").parquet(category_path)
    print(f"Category performance saved to: {category_path}")
    
    # 3. Customer segmentation
    print("Creating customer segmentation...")
    customer_segmentation = final_dataset \
        .groupBy("customer_id", "customer_city", "customer_state") \
        .agg(
            countDistinct("order_id").alias("total_orders"),
            sum("total_order_value").alias("total_spent"),
            avg("total_order_value").alias("avg_order_value"),
            min("order_purchase_timestamp").alias("first_order_date"),
            max("order_purchase_timestamp").alias("last_order_date")
        ) \
        .withColumn(
            "customer_segment",
            when(col("total_spent") > 1000, "High Value")
            .when(col("total_spent") > 500, "Medium Value")
            .otherwise("Low Value")
        ) \
        .orderBy(col("total_spent").desc())
    
    # Save customer segmentation
    customers_path = f"{hdfs_path}/processed/customer_segmentation"
    customer_segmentation.write.mode("overwrite").parquet(customers_path)
    print(f"Customer segmentation saved to: {customers_path}")
    
    # Show sample results
    print("\nSample results:")
    print("Monthly Sales Summary:")
    monthly_sales.show(5)
    
    print("\nTop 5 Product Categories:")
    category_performance.show(5)
    
    print("\nTop 5 Customers:")
    customer_segmentation.show(5)

def main():
    """
    Main function to orchestrate the ETL pipeline
    """
    try:
        # Initialize Spark session
        spark = create_spark_session()
        
        # Set HDFS path
        hdfs_path = "/user/ashwini/ecommerce"
        
        # Load data
        orders_df, items_df, customers_df, products_df = load_data(spark, hdfs_path)
        
        # Perform data quality checks
        data_quality_checks(orders_df, items_df, customers_df, products_df)
        
        # Perform ETL transformations
        final_dataset = etl_transformations(orders_df, items_df, customers_df, products_df)
        
        # Show sample of transformed data
        print("Sample of transformed data:")
        final_dataset.select(
            "order_id", "customer_id", "product_id", 
            "total_order_value", "customer_state", "product_category_name"
        ).show(5)
        
        # Demonstrate RDD operations
        rdd_example(spark, final_dataset)
        
        # Create analytical tables
        create_analytics_tables(spark, final_dataset, hdfs_path)
        
        print("\nETL Pipeline completed successfully!")
        
    except Exception as e:
        print(f"Error in ETL pipeline: {str(e)}")
        sys.exit(1)
    
    finally:
        # Stop Spark session
        if 'spark' in locals():
            spark.stop()
            print("Spark session stopped.")

if __name__ == "__main__":
    main()
