#!/bin/bash

# Hive Working Script - Only Real Working Code
# Removes manual/static parts, keeps only actual execution

echo "=== Hive Query Execution ==="

# Environment setup
export HADOOP_HOME=/home/ashwini/hadoop
export PATH=$PATH:/home/ashwini/bigdata/hive/bin:/home/ashwini/hadoop/bin

echo "Environment: HADOOP_HOME=$HADOOP_HOME"
echo "Hive binary: $(which hive)"

# Execute real Hive commands
echo ""
echo "1. Creating database:"
hive -e "CREATE DATABASE IF NOT EXISTS ecommerce;" 2>/dev/null || echo "Database creation failed"

echo ""
echo "2. Using database:"
hive -e "USE ecommerce;" 2>/dev/null || echo "Database selection failed"

echo ""
echo "3. Creating orders table:"
hive -e "CREATE EXTERNAL TABLE IF NOT EXISTS orders (order_id STRING, customer_id STRING, order_status STRING) ROW FORMAT DELIMITED FIELDS TERMINATED BY ',' STORED AS TEXTFILE LOCATION '/user/ashwini/ecommerce/raw/orders' TBLPROPERTIES ('skip.header.line.count'='1');" 2>/dev/null || echo "Table creation failed"

echo ""
echo "4. Sample query:"
hive -e "SELECT COUNT(*) as count FROM orders LIMIT 1;" 2>/dev/null || echo "Query failed"

echo ""
echo "5. HDFS data status:"
hdfs dfs -ls /user/ashwini/ecommerce/raw

echo ""
echo "=== Execution Complete ==="
