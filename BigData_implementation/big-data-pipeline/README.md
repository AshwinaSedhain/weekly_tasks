# Big Data Pipeline Project

## Overview

This project demonstrates a complete big data processing pipeline using Hadoop ecosystem tools. It processes e-commerce data and performs storage, batch processing, analytics, and machine learning.

## Technologies Used

- Hadoop (HDFS, MapReduce)
- Hive
- Spark (ETL and ML)
- HBase
- Python

## Dataset

### Brazilian E-Commerce Dataset 

https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce

**Used files:**
- orders
- order_items
- customers
- products

## Project Workflow

1. Store data in HDFS
2. Process data using MapReduce
3. Perform SQL analysis using Hive
4. Run ETL and analytics using Spark
5. Apply basic machine learning using Spark MLlib
6. Store and retrieve data using HBase

## Project Structure

```
big-data-pipeline/
|-- datasets/          CSV files
|-- scripts/           Processing scripts
|-- hive_queries.sql   Hive queries
|-- outputs/           Results
|-- README.md
```

## How to Run

### Start Hadoop
```bash
start-dfs.sh
start-yarn.sh
```

### Load Data into HDFS
```bash
cd scripts
./load_to_hdfs.sh
```

### Run MapReduce
```bash
hadoop jar hadoop-streaming.jar \
-files mapper.py,reducer.py \
-mapper "python3 mapper.py" \
-reducer "python3 reducer.py" \
-input /ecommerce/raw \
-output /ecommerce/results/mapreduce
```

### Run Hive Queries
```bash
hive -f hive_queries.sql
```

### Run Spark Pipeline
```bash
spark-submit pyspark_pipeline.py
```

### Run ML Model
```bash
spark-submit spark_mllib.py
```

### Run HBase Script
```bash
python3 hbase_happybase.py
```

## Output

- Sales analysis by product category
- Monthly revenue trends
- Customer analysis
- State-wise sales distribution
- Basic machine learning predictions
- HBase data storage and retrieval

## Learning Outcomes

- Distributed storage using HDFS
- Batch processing using MapReduce
- SQL-based analytics using Hive
- Data processing using Spark
- NoSQL database usage with HBase
- Basic machine learning on big data