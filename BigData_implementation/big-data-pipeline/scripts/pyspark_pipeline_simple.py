#!/usr/bin/env python3

#Simplified PySpark ETL Pipeline for E-Commerce Data Processing


from pyspark.sql import SparkSession
from pyspark.sql.functions import *
import sys

def create_spark_session():
    """Create and configure Spark session"""
    print("Creating Spark session...")
    
    spark = SparkSession.builder \
        .appName("EcommerceETLPipeline") \
        .config("spark.master", "local[*]") \
        .getOrCreate()
    
    spark.sparkContext.setLogLevel("WARN")
    print("Spark session created successfully!")
    return spark

def load_data(spark, hdfs_path):
    """Load CSV data from HDFS into Spark DataFrames"""
    print("Loading data from HDFS...")
    
    # Load data files
    orders_path = f"{hdfs_path}/raw/olist_orders_dataset.csv"
    items_path = f"{hdfs_path}/raw/olist_order_items_dataset.csv"
    customers_path = f"{hdfs_path}/raw/olist_customers_dataset.csv"
    products_path = f"{hdfs_path}/raw/olist_products_dataset.csv"
    
    orders_df = spark.read.option("header", "true").option("inferSchema", "true").csv(orders_path)
    items_df = spark.read.option("header", "true").option("inferSchema", "true").csv(items_path)
    customers_df = spark.read.option("header", "true").option("inferSchema", "true").csv(customers_path)
    products_df = spark.read.option("header", "true").option("inferSchema", "true").csv(products_path)
    
    print("Data loading completed!")
    return orders_df, items_df, customers_df, products_df

def etl_transformations(orders_df, items_df, customers_df, products_df):
    """Perform ETL transformations using Spark DataFrames"""
    print("Starting ETL transformations...")
    
    # Filter delivered orders
    delivered_orders = orders_df.filter(col("order_status") == "delivered")
    
    # Join datasets
    order_items = delivered_orders.join(items_df, "order_id", "inner")
    complete_orders = order_items.join(products_df, "product_id", "left")
    final_dataset = complete_orders.join(customers_df, "customer_id", "left")
    
    # Create derived columns
    final_dataset = final_dataset.withColumn(
        "total_order_value", 
        col("price") + col("freight_value")
    ).withColumn(
        "order_year",
        year("order_purchase_timestamp")
    ).withColumn(
        "order_month",
        month("order_purchase_timestamp")
    )
    
    print("ETL transformations completed!")
    return final_dataset

def create_analytics_tables(spark, final_dataset, hdfs_path):
    """Create analytical tables and save results"""
    print("Creating analytical tables...")
    
    # Monthly sales summary
    monthly_sales = final_dataset \
        .groupBy("order_year", "order_month") \
        .agg(
            countDistinct("order_id").alias("total_orders"),
            sum("total_order_value").alias("total_revenue"),
            avg("total_order_value").alias("avg_order_value")
        ) \
        .orderBy("order_year", "order_month")
    
    # Save monthly sales
    monthly_sales_path = f"{hdfs_path}/processed/monthly_sales"
    monthly_sales.write.mode("overwrite").parquet(monthly_sales_path)
    print(f"Monthly sales saved to: {monthly_sales_path}")
    
    # Product category performance
    category_performance = final_dataset \
        .filter(col("product_category_name").isNotNull()) \
        .groupBy("product_category_name") \
        .agg(
            countDistinct("product_id").alias("unique_products"),
            countDistinct("order_id").alias("total_orders"),
            sum("total_order_value").alias("total_revenue"),
            avg("price").alias("avg_product_price")
        ) \
        .orderBy(col("total_revenue").desc())
    
    # Save category performance
    category_path = f"{hdfs_path}/processed/category_performance"
    category_performance.write.mode("overwrite").parquet(category_path)
    print(f"Category performance saved to: {category_path}")
    
    # Show sample results
    print("\nSample results:")
    print("Monthly Sales Summary:")
    monthly_sales.show(5)
    
    print("\nTop 5 Product Categories:")
    category_performance.show(5)

def main():
    """Main function to orchestrate the ETL pipeline"""
    try:
        # Initialize Spark session
        spark = create_spark_session()
        
        # Set HDFS path
        hdfs_path = "/user/ashwini/ecommerce"
        
        # Load data
        orders_df, items_df, customers_df, products_df = load_data(spark, hdfs_path)
        
        # Show data shapes
        print(f"Orders: {orders_df.count()} rows")
        print(f"Items: {items_df.count()} rows")
        print(f"Customers: {customers_df.count()} rows")
        print(f"Products: {products_df.count()} rows")
        
        # Perform ETL transformations
        final_dataset = etl_transformations(orders_df, items_df, customers_df, products_df)
        
        # Show sample of transformed data
        print("Sample of transformed data:")
        final_dataset.select(
            "order_id", "customer_id", "product_id", 
            "total_order_value", "customer_state", "product_category_name"
        ).show(5)
        
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
