-- E-COMMERCE DATA WAREHOUSE (HIVE)

CREATE DATABASE IF NOT EXISTS ecommerce;
USE ecommerce;

-- DROP TABLES (for re-runs)
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS customers;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS sales_summary;


-- ORDERS TABLE
CREATE EXTERNAL TABLE orders (
    order_id STRING,
    customer_id STRING,
    order_status STRING,
    order_purchase_timestamp STRING,
    order_approved_at STRING,
    order_delivered_carrier_date STRING,
    order_delivered_customer_date STRING,
    order_estimated_delivery_date STRING
)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ','
STORED AS TEXTFILE
LOCATION '/user/ashwini/ecommerce/raw/orders'
TBLPROPERTIES ('skip.header.line.count'='1');

-- ORDER ITEMS TABLE
CREATE EXTERNAL TABLE order_items (
    order_id STRING,
    order_item_id INT,
    product_id STRING,
    seller_id STRING,
    shipping_limit_date STRING,
    price DOUBLE,
    freight_value DOUBLE
)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ','
STORED AS TEXTFILE
LOCATION '/user/ashwini/ecommerce/raw/order_items'
TBLPROPERTIES ('skip.header.line.count'='1');


-- CUSTOMERS TABLE
CREATE EXTERNAL TABLE customers (
    customer_id STRING,
    customer_unique_id STRING,
    customer_zip_code_prefix INT,
    customer_city STRING,
    customer_state STRING
)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ','
STORED AS TEXTFILE
LOCATION '/user/ashwini/ecommerce/raw/customers'
TBLPROPERTIES ('skip.header.line.count'='1');

-- PRODUCTS TABLE
CREATE EXTERNAL TABLE products (
    product_id STRING,
    product_category_name STRING,
    product_name_lenght INT,
    product_description_lenght INT,
    product_photos_qty INT,
    product_weight_g INT,
    product_length_cm INT,
    product_height_cm INT,
    product_width_cm INT
)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ','
STORED AS TEXTFILE
LOCATION '/user/ashwini/ecommerce/raw/products'
TBLPROPERTIES ('skip.header.line.count'='1');

-- 1. TOP PRODUCT CATEGORIES BY REVENUE
SELECT 
    p.product_category_name,
    SUM(oi.price + oi.freight_value) AS total_sales,
    COUNT(DISTINCT oi.order_id) AS total_orders,
    AVG(oi.price) AS avg_price
FROM order_items oi
JOIN products p ON oi.product_id = p.product_id
WHERE p.product_category_name IS NOT NULL
GROUP BY p.product_category_name
ORDER BY total_sales DESC
LIMIT 10;


-- 2. MONTHLY SALES TREND
SELECT 
    substr(o.order_purchase_timestamp, 1, 7) AS month,
    COUNT(DISTINCT o.order_id) AS total_orders,
    SUM(oi.price + oi.freight_value) AS total_revenue,
    AVG(oi.price) AS avg_order_value
FROM orders o
JOIN order_items oi ON o.order_id = oi.order_id
WHERE o.order_status = 'delivered'
GROUP BY substr(o.order_purchase_timestamp, 1, 7)
ORDER BY month;


-- 3. TOP CUSTOMERS BY SPENDING
SELECT 
    c.customer_id,
    c.customer_city,
    c.customer_state,
    COUNT(DISTINCT o.order_id) AS total_orders,
    SUM(oi.price + oi.freight_value) AS total_spent,
    AVG(oi.price + oi.freight_value) AS avg_order_value
FROM customers c
JOIN orders o ON c.customer_id = o.customer_id
JOIN order_items oi ON o.order_id = oi.order_id
WHERE o.order_status = 'delivered'
GROUP BY c.customer_id, c.customer_city, c.customer_state
ORDER BY total_spent DESC
LIMIT 10;


-- 4. STATE-WISE ANALYSIS
SELECT 
    c.customer_state,
    COUNT(DISTINCT o.order_id) AS total_orders,
    SUM(oi.price + oi.freight_value) AS total_revenue,
    COUNT(DISTINCT c.customer_id) AS unique_customers,
    AVG(oi.price + oi.freight_value) AS avg_order_value
FROM customers c
JOIN orders o ON c.customer_id = o.customer_id
JOIN order_items oi ON o.order_id = oi.order_id
WHERE o.order_status = 'delivered'
GROUP BY c.customer_state
ORDER BY total_revenue DESC;


-- 5. ORDER STATUS DISTRIBUTION
SELECT 
    order_status,
    COUNT(*) AS order_count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) AS percentage
FROM orders
GROUP BY order_status
ORDER BY order_count DESC;

-- 6. PRODUCT CATEGORY PERFORMANCE
SELECT 
    p.product_category_name,
    COUNT(DISTINCT p.product_id) AS unique_products,
    COUNT(DISTINCT oi.order_id) AS total_orders,
    SUM(oi.price + oi.freight_value) AS total_revenue,
    AVG(oi.price) AS avg_product_price
FROM products p
LEFT JOIN order_items oi ON p.product_id = oi.product_id
WHERE p.product_category_name IS NOT NULL
GROUP BY p.product_category_name
HAVING COUNT(DISTINCT oi.order_id) > 0
ORDER BY total_revenue DESC
LIMIT 20;


-- 7. DELIVERY PERFORMANCE
SELECT 
    c.customer_state,
    AVG(CAST(datediff(o.order_delivered_customer_date, o.order_purchase_timestamp) AS INT)) AS avg_delivery_days,
    AVG(CAST(datediff(o.order_estimated_delivery_date, o.order_delivered_customer_date) AS INT)) AS avg_delay_days,
    SUM(CASE 
        WHEN o.order_delivered_customer_date <= o.order_estimated_delivery_date 
        THEN 1 ELSE 0 
    END) * 100.0 / COUNT(*) AS on_time_delivery_pct
FROM customers c
JOIN orders o ON c.customer_id = o.customer_id
WHERE o.order_status = 'delivered'
  AND o.order_delivered_customer_date IS NOT NULL
GROUP BY c.customer_state
ORDER BY on_time_delivery_pct DESC;


-- 8. MANAGED TABLE (PROCESSED DATA)
CREATE TABLE IF NOT EXISTS sales_summary (
    product_category_name STRING,
    total_sales DOUBLE,
    total_orders INT,
    avg_price DOUBLE,
    processing_date STRING
)
STORED AS ORC;

INSERT OVERWRITE TABLE sales_summary
SELECT 
    p.product_category_name,
    SUM(oi.price + oi.freight_value) AS total_sales,
    COUNT(DISTINCT oi.order_id) AS total_orders,
    AVG(oi.price) AS avg_price,
    current_date()
FROM order_items oi
JOIN products p ON oi.product_id = p.product_id
WHERE p.product_category_name IS NOT NULL
GROUP BY p.product_category_name;

-- FINAL OUTPUT
SELECT * FROM sales_summary ORDER BY total_sales DESC LIMIT 10;