#!/bin/bash

# HDFS Data Loading Script
# This script uploads the Olist e-commerce datasets to HDFS

echo "=== HDFS Data Loading Script ==="
echo "Starting data upload to HDFS..."

# Set base directory for our project
BASE_DIR="/home/ashwini/Documents/BigData_implementation/big-data-pipeline"
DATASET_DIR="$BASE_DIR/datasets"
HDFS_BASE_PATH="/user/$USER/ecommerce"

# Check if local dataset directory exists
if [ ! -d "$DATASET_DIR" ]; then
    echo "ERROR: Dataset directory not found at $DATASET_DIR"
    echo "Please make sure the CSV files are copied to the datasets folder"
    exit 1
fi

# Check if HDFS is running
echo "Checking HDFS status..."
if ! hdfs dfsadmin -report > /dev/null 2>&1; then
    echo "ERROR: HDFS is not running"
    echo "Please start HDFS using: start-dfs.sh"
    exit 1
fi

# Create HDFS directory structure
echo "Creating HDFS directory structure..."
hdfs dfs -mkdir -p $HDFS_BASE_PATH
hdfs dfs -mkdir -p $HDFS_BASE_PATH/raw
hdfs dfs -mkdir -p $HDFS_BASE_PATH/processed
hdfs dfs -mkdir -p $HDFS_BASE_PATH/results

# List of CSV files to upload
declare -a files=(
    "olist_orders_dataset.csv"
    "olist_order_items_dataset.csv"
    "olist_customers_dataset.csv"
    "olist_products_dataset.csv"
)

# Upload each file to HDFS
echo "Uploading CSV files to HDFS..."
for file in "${files[@]}"; do
    local_path="$DATASET_DIR/$file"
    hdfs_path="$HDFS_BASE_PATH/raw/$file"
    
    # Check if local file exists
    if [ ! -f "$local_path" ]; then
        echo "WARNING: File $file not found locally, skipping..."
        continue
    fi
    
    # Check if file already exists in HDFS
    if hdfs dfs -test -e "$hdfs_path"; then
        echo "File $file already exists in HDFS, removing old version..."
        hdfs dfs -rm "$hdfs_path"
    fi
    
    # Upload file
    echo "Uploading $file to HDFS..."
    hdfs dfs -put "$local_path" "$hdfs_path"
    
    # Verify upload
    if hdfs dfs -test -e "$hdfs_path"; then
        echo "SUCCESS: $file uploaded to HDFS"
        # Show file size
        size=$(hdfs dfs -du -h "$hdfs_path" | awk '{print $1}')
        echo "  File size: $size"
    else
        echo "ERROR: Failed to upload $file"
    fi
done

# Show HDFS directory structure
echo ""
echo "=== HDFS Directory Structure ==="
hdfs dfs -ls -R $HDFS_BASE_PATH

# Show HDFS space usage
echo ""
echo "=== HDFS Space Usage ==="
hdfs dfs -du -h $HDFS_BASE_PATH

echo ""
echo "=== Data Loading Complete ==="
echo "Data is now available in HDFS at: $HDFS_BASE_PATH/raw"
echo ""
echo "Next steps:"
echo "1. Run MapReduce job: hadoop jar ... mapper.py reducer.py"
echo "2. Create Hive tables: hive -f hive_queries.sql"
echo "3. Run Spark processing: spark-submit pyspark_pipeline.py"
