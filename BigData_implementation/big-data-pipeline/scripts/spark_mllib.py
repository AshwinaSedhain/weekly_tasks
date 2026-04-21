#!/usr/bin/env python3

#This script builds a simple customer churn prediction model

from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
from pyspark.ml.feature import VectorAssembler, StringIndexer, StandardScaler
from pyspark.ml.classification import LogisticRegression, RandomForestClassifier
from pyspark.ml.evaluation import BinaryClassificationEvaluator
from pyspark.ml import Pipeline
import sys

def create_spark_session():
    """
    Create and configure Spark session for ML
    """
    print("Creating Spark session for ML...")
    
    spark = SparkSession.builder \
        .appName("CustomerChurnPrediction") \
        .config("spark.master", "local[*]") \
        .config("spark.sql.warehouse.dir", "/user/hive/warehouse") \
        .getOrCreate()
    
    spark.sparkContext.setLogLevel("WARN")
    
    print("Spark session created successfully!")
    return spark

def load_and_prepare_data(spark, hdfs_path):
    """
    Load data and prepare for ML
    We'll create a synthetic churn scenario based on customer behavior
    """
    print("Loading and preparing data for ML...")
    
    # Load the processed customer segmentation data from our ETL pipeline
    customers_path = f"{hdfs_path}/processed/customer_segmentation"
    
    try:
        customers_df = spark.read.parquet(customers_path)
    except:
        print("Processed data not found, loading from raw files...")
        # If processed data doesn't exist, load from raw files
        orders_path = f"{hdfs_path}/raw/olist_orders_dataset.csv"
        items_path = f"{hdfs_path}/raw/olist_order_items_dataset.csv"
        customers_path_raw = f"{hdfs_path}/raw/olist_customers_dataset.csv"
        
        orders_df = spark.read.option("header", "true").option("inferSchema", "true").csv(orders_path)
        items_df = spark.read.option("header", "true").option("inferSchema", "true").csv(items_path)
        customers_raw_df = spark.read.option("header", "true").option("inferSchema", "true").csv(customers_path_raw)
        
        # Create customer features
        order_items = orders_df.join(items_df, "order_id", "inner")
        customers_df = order_items.groupBy("customer_id") \
            .agg(
                countDistinct("order_id").alias("total_orders"),
                sum("price").alias("total_spent"),
                avg("price").alias("avg_order_value"),
                min("order_purchase_timestamp").alias("first_order_date"),
                max("order_purchase_timestamp").alias("last_order_date")
            )
        
        # Add customer demographic info
        customers_df = customers_df.join(customers_raw_df, "customer_id", "left")
    
    # Create churn label (synthetic - based on customer behavior)
    print("Creating churn labels...")
    
    # Define churn as customers with:
    # - Less than 2 orders OR
    # - Total spent less than 100 OR  
    # - Haven't ordered in last 6 months (simplified)
    customers_df = customers_df.withColumn(
        "is_churn",
        when((col("total_orders") < 2) | (col("total_spent") < 100), 1).otherwise(0)
    )
    
    # Show churn distribution
    print("Churn distribution:")
    customers_df.groupBy("is_churn").count().show()
    
    return customers_df

def feature_engineering(customers_df):
    """
    Perform feature engineering for ML
    This creates numerical features from categorical data
    """
    print("Performing feature engineering...")
    
    # Select relevant features for ML
    feature_df = customers_df.select(
        "customer_id",
        "total_orders",
        "total_spent", 
        "avg_order_value",
        "customer_state",
        "is_churn"
    ).filter(col("total_orders").isNotNull() & col("total_spent").isNotNull())
    
    # Handle missing values
    feature_df = feature_df.fillna({
        'total_orders': 0,
        'total_spent': 0.0,
        'avg_order_value': 0.0,
        'customer_state': 'Unknown'
    })
    
    # Convert categorical state to numerical using StringIndexer
    print("Indexing categorical features...")
    state_indexer = StringIndexer(inputCol="customer_state", outputCol="state_index", handleInvalid="keep")
    state_indexer_model = state_indexer.fit(feature_df)
    feature_df = state_indexer_model.transform(feature_df)
    
    # Create feature vector
    print("Creating feature vectors...")
    feature_cols = ["total_orders", "total_spent", "avg_order_value", "state_index"]
    assembler = VectorAssembler(inputCols=feature_cols, outputCol="features")
    feature_df = assembler.transform(feature_df)
    
    # Scale features
    print("Scaling features...")
    scaler = StandardScaler(inputCol="features", outputCol="scaled_features")
    scaler_model = scaler.fit(feature_df)
    feature_df = scaler_model.transform(feature_df)
    
    print("Feature engineering completed!")
    return feature_df, state_indexer_model, scaler_model

def split_data(feature_df):
    """
    Split data into training and testing sets
    """
    print("Splitting data into train and test sets...")
    
    # Split data: 80% training, 20% testing
    train_data, test_data = feature_df.randomSplit([0.8, 0.2], seed=42)
    
    print(f"Training set size: {train_data.count()}")
    print(f"Test set size: {test_data.count()}")
    
    return train_data, test_data

def train_logistic_regression(train_data):
    """
    Train a Logistic Regression model
    This is a simple baseline model for churn prediction
    """
    print("Training Logistic Regression model...")
    
    # Create and configure Logistic Regression
    lr = LogisticRegression(
        featuresCol="scaled_features",
        labelCol="is_churn",
        maxIter=10,
        regParam=0.3,
        elasticNetParam=0.8
    )
    
    # Train the model
    lr_model = lr.fit(train_data)
    
    print("Logistic Regression model trained!")
    return lr_model

def train_random_forest(train_data):
    """
    Train a Random Forest model
    This is typically more accurate than Logistic Regression
    """
    print("Training Random Forest model...")
    
    # Create and configure Random Forest
    rf = RandomForestClassifier(
        featuresCol="scaled_features",
        labelCol="is_churn",
        numTrees=10,
        maxDepth=5,
        seed=42
    )
    
    # Train the model
    rf_model = rf.fit(train_data)
    
    print("Random Forest model trained!")
    return rf_model

def evaluate_model(model, test_data, model_name):
    """
    Evaluate model performance
    This calculates accuracy and AUC metrics
    """
    print(f"Evaluating {model_name}...")
    
    # Make predictions
    predictions = model.transform(test_data)
    
    # Calculate accuracy
    correct_predictions = predictions.filter(
        (predictions.prediction == predictions.is_churn)
    ).count()
    total_predictions = predictions.count()
    accuracy = correct_predictions / total_predictions
    
    # Calculate AUC using BinaryClassificationEvaluator
    evaluator = BinaryClassificationEvaluator(
        labelCol="is_churn",
        rawPredictionCol="rawPrediction",
        metricName="areaUnderROC"
    )
    auc = evaluator.evaluate(predictions)
    
    print(f"{model_name} Results:")
    print(f"  Accuracy: {accuracy:.4f}")
    print(f"  AUC: {auc:.4f}")
    
    # Show confusion matrix
    print(f"  Confusion Matrix:")
    predictions.groupBy("is_churn", "prediction").count().show()
    
    return predictions, accuracy, auc

def feature_importance_analysis(rf_model, feature_cols):
    """
    Analyze feature importance from Random Forest model
    """
    print("Analyzing feature importance...")
    
    # Get feature importances
    importances = rf_model.featureImportances.toArray()
    
    # Create a list of (feature, importance) pairs
    feature_importance_list = list(zip(feature_cols, importances))
    
    # Sort by importance
    feature_importance_list.sort(key=lambda x: x[1], reverse=True)
    
    print("Feature Importance Ranking:")
    for feature, importance in feature_importance_list:
        print(f"  {feature}: {importance:.4f}")
    
    return feature_importance_list

def save_predictions(predictions, hdfs_path, model_name):
    """
    Save model predictions to HDFS
    """
    print(f"Saving {model_name} predictions...")
    
    # Select relevant columns for output
    output_df = predictions.select(
        "customer_id",
        "total_orders",
        "total_spent",
        "customer_state",
        "is_churn",
        "prediction",
        "probability"
    )
    
    # Save to HDFS
    output_path = f"{hdfs_path}/results/{model_name}_predictions"
    output_df.write.mode("overwrite").parquet(output_path)
    
    print(f"Predictions saved to: {output_path}")
    
    # Show sample predictions
    print("Sample predictions:")
    output_df.show(10)

def main():
    """
    Main function to orchestrate the ML pipeline
    """
    try:
        # Initialize Spark session
        spark = create_spark_session()
        
        # Set HDFS path
        hdfs_path = "/user/ashwini/ecommerce"
        
        # Load and prepare data
        customers_df = load_and_prepare_data(spark, hdfs_path)
        
        # Feature engineering
        feature_df, state_indexer_model, scaler_model = feature_engineering(customers_df)
        
        # Show sample of engineered features
        print("Sample of engineered features:")
        feature_df.select("customer_id", "total_orders", "total_spent", "is_churn", "features").show(5)
        
        # Split data
        train_data, test_data = split_data(feature_df)
        
        # Train models
        lr_model = train_logistic_regression(train_data)
        rf_model = train_random_forest(train_data)
        
        # Evaluate models
        lr_predictions, lr_accuracy, lr_auc = evaluate_model(lr_model, test_data, "Logistic Regression")
        rf_predictions, rf_accuracy, rf_auc = evaluate_model(rf_model, test_data, "Random Forest")
        
        # Feature importance analysis
        feature_cols = ["total_orders", "total_spent", "avg_order_value", "state_index"]
        feature_importance_analysis(rf_model, feature_cols)
        
        # Save predictions
        save_predictions(lr_predictions, hdfs_path, "logistic_regression")
        save_predictions(rf_predictions, hdfs_path, "random_forest")
        
        # Model comparison
        print("\n=== Model Comparison ===")
        print(f"Logistic Regression - Accuracy: {lr_accuracy:.4f}, AUC: {lr_auc:.4f}")
        print(f"Random Forest - Accuracy: {rf_accuracy:.4f}, AUC: {rf_auc:.4f}")
        
        if rf_auc > lr_auc:
            print("Random Forest performs better!")
        else:
            print("Logistic Regression performs better!")
        
        print("\nML Pipeline completed successfully!")
        
    except Exception as e:
        print(f"Error in ML pipeline: {str(e)}")
        sys.exit(1)
    
    finally:
        # Stop Spark session
        if 'spark' in locals():
            spark.stop()
            print("Spark session stopped.")

if __name__ == "__main__":
    main()
