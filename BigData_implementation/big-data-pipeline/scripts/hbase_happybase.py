#!/usr/bin/env python3

#HBase Integration using HappyBase
#Demonstrating CRUD operations for customer and product data
import happybase
import csv
import sys
import time
from datetime import datetime

class HBaseEcommerceManager:
    # HBase manager class for e-commerce data operations
    # This class handles all HBase interactions using HappyBase
    
    def __init__(self, host='localhost', port=9090):
        # Initializing HBase connection
        
        self.host = host
        self.port = port
        self.connection = None
        self.connect()
    
    def connect(self):
        # Establishing the connection to HBase
        # This connects to HBase using HappyBase
        try:
            print(f"Connecting to HBase at {self.host}:{self.port}...")
            self.connection = happybase.Connection(host=self.host, port=self.port)
            print("Successfully connected to HBase!")
            
            # List existing tables
            tables = self.connection.tables()
            print(f"Existing tables: {tables}")
            
        except Exception as e:
            print(f"Error connecting to HBase: {str(e)}")
            print("Make sure HBase is running and Thrift server is started")
            print("Start Thrift server with: hbase-daemon.sh start thrift")
            sys.exit(1)
    
    def create_customer_table(self):
        # Creating customer table in HBase
      
        print("Creating customer table...")
        
        table_name = b'customer_data'
        
        # Check if table exists
        if table_name in self.connection.tables():
            print("Customer table already exists, dropping and recreating...")
            self.connection.delete_table(table_name, disable=True)
        
        # Create table with column families
        families = {
            'info': dict(max_versions=1),  # Basic customer info
            'orders': dict(max_versions=5),  # Order history
            'analytics': dict(max_versions=1)  # Analytics data
        }
        
        self.connection.create_table(table_name, families)
        print(f"Table {table_name.decode()} created successfully!")
    
    def create_product_table(self):
        # Creating product table in HBase
        print("Creating product table...")
        
        table_name = b'product_data'
        
        # Check if table exists
        if table_name in self.connection.tables():
            print("Product table already exists, dropping and recreating...")
            self.connection.delete_table(table_name, disable=True)
        
        # Create table with column families
        families = {
            'info': dict(max_versions=1),  # Basic product info
            'sales': dict(max_versions=3),  # Sales metrics
            'inventory': dict(max_versions=1)  # Inventory data
        }
        
        self.connection.create_table(table_name, families)
        print(f"Table {table_name.decode()} created successfully!")
    
    def load_customer_data(self, csv_file_path):
        # Loading customer data from CSV into HBase
        # Demonstrating batch insert operations
        print(f"Loading customer data from {csv_file_path}...")
        
        table = self.connection.table('customer_data')
        
        try:
            with open(csv_file_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                
                batch_count = 0
                for row in reader:
                    customer_id = row['customer_id']
                    
                    # Prepare customer data for HBase
                    customer_data = {
                        b'info:customer_unique_id': row['customer_unique_id'],
                        b'info:zip_code': row['customer_zip_code_prefix'],
                        b'info:city': row['customer_city'],
                        b'info:state': row['customer_state'],
                        b'info:created_at': str(datetime.now()),
                        b'analytics:total_orders': '0',  # Initialize with 0
                        b'analytics:total_spent': '0.0'  # Initialize with 0.0
                    }
                    
                    # Insert customer data
                    table.put(customer_id.encode(), customer_data)
                    batch_count += 1
                    
                    # Print progress every 1000 customers
                    if batch_count % 1000 == 0:
                        print(f"Loaded {batch_count} customers...")
                
                print(f"Successfully loaded {batch_count} customers!")
                
        except FileNotFoundError:
            print(f"Error: File {csv_file_path} not found")
            return False
        except Exception as e:
            print(f"Error loading customer data: {str(e)}")
            return False
        
        return True
    
    def load_product_data(self, csv_file_path):
        # Load product data from CSV into HBase
        # This demonstrates another batch insert operation
        print(f"Loading product data from {csv_file_path}...")
        
        table = self.connection.table('product_data')
        
        try:
            with open(csv_file_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                
                batch_count = 0
                for row in reader:
                    product_id = row['product_id']
                    
                    # Prepare product data for HBase
                    product_data = {
                        b'info:category': row.get('product_category_name', 'unknown'),
                        b'info:name_length': row.get('product_name_lenght', '0'),
                        b'info:description_length': row.get('product_description_lenght', '0'),
                        b'info:photo_count': row.get('product_photos_qty', '0'),
                        b'info:weight_g': row.get('product_weight_g', '0'),
                        b'info:dimensions': f"{row.get('product_length_cm', '0')}x{row.get('product_height_cm', '0')}x{row.get('product_width_cm', '0')}",
                        b'info:created_at': str(datetime.now()),
                        b'sales:total_sold': '0',  # Initialize with 0
                        b'sales:total_revenue': '0.0',  # Initialize with 0.0
                        b'inventory:stock_status': 'available'  # Default status
                    }
                    
                    # Insert product data
                    table.put(product_id.encode(), product_data)
                    batch_count += 1
                    
                    # Print progress every 1000 products
                    if batch_count % 1000 == 0:
                        print(f"Loaded {batch_count} products...")
                
                print(f"Successfully loaded {batch_count} products!")
                
        except FileNotFoundError:
            print(f"Error: File {csv_file_path} not found")
            return False
        except Exception as e:
            print(f"Error loading product data: {str(e)}")
            return False
        
        return True
    
    def get_customer(self, customer_id):
        # Retrieving customer information by ID
        # This demonstrates read operations
        print(f"Retrieving customer: {customer_id}")
        
        table = self.connection.table('customer_data')
        
        try:
            # Get customer data
            customer = table.row(customer_id.encode())
            
            if customer:
                print(f"Customer found!")
                print(f"  Customer ID: {customer_id}")
                print(f"  City: {customer.get(b'info:city', b'N/A').decode()}")
                print(f"  State: {customer.get(b'info:state', b'N/A').decode()}")
                print(f"  Total Orders: {customer.get(b'analytics:total_orders', b'0').decode()}")
                print(f"  Total Spent: ${customer.get(b'analytics:total_spent', b'0.0').decode()}")
                return customer
            else:
                print(f"Customer {customer_id} not found!")
                return None
                
        except Exception as e:
            print(f"Error retrieving customer: {str(e)}")
            return None
    
    def get_product(self, product_id):
        # Retrieve product information by ID
        # This demonstrates another read operation
        print(f"Retrieving product: {product_id}")
        
        table = self.connection.table('product_data')
        
        try:
            # Get product data
            product = table.row(product_id.encode())
            
            if product:
                print(f"Product found!")
                print(f"  Product ID: {product_id}")
                print(f"  Category: {product.get(b'info:category', b'N/A').decode()}")
                print(f"  Weight: {product.get(b'info:weight_g', b'0').decode()}g")
                print(f"  Total Sold: {product.get(b'sales:total_sold', b'0').decode()}")
                print(f"  Total Revenue: ${product.get(b'sales:total_revenue', b'0.0').decode()}")
                return product
            else:
                print(f"Product {product_id} not found!")
                return None
                
        except Exception as e:
            print(f"Error retrieving product: {str(e)}")
            return None
    
    def update_customer_analytics(self, customer_id, total_orders, total_spent):
        # Update customer analytics data
        # This demonstrates update operations
        print(f"Updating analytics for customer: {customer_id}")
        
        table = self.connection.table('customer_data')
        
        try:
            # Update customer analytics
            analytics_data = {
                b'analytics:total_orders': str(total_orders),
                b'analytics:total_spent': str(total_spent),
                b'analytics:last_updated': str(datetime.now())
            }
            
            table.put(customer_id.encode(), analytics_data)
            print(f"Customer analytics updated successfully!")
            
        except Exception as e:
            print(f"Error updating customer analytics: {str(e)}")
            return False
        
        return True
    
    def update_product_sales(self, product_id, units_sold, revenue):
        # Update product sales data
        # This demonstrates another update operation
        print(f"Updating sales for product: {product_id}")
        
        table = self.connection.table('product_data')
        
        try:
            # Update product sales
            sales_data = {
                b'sales:total_sold': str(units_sold),
                b'sales:total_revenue': str(revenue),
                b'sales:last_updated': str(datetime.now())
            }
            
            table.put(product_id.encode(), sales_data)
            print(f"Product sales updated successfully!")
            
        except Exception as e:
            print(f"Error updating product sales: {str(e)}")
            return False
        
        return True
    
    def scan_customers_by_state(self, state, limit=10):
        # Scan customers by state
        # This demonstrates scan operations with filters
        print(f"Scanning customers in state: {state}")
        
        table = self.connection.table('customer_data')
        
        try:
            # Scan customers in specific state
            scanner = table.scan(filter=b"SingleColumnValueFilter('info', 'state', =, 'binary:{state}')")
            
            customers_found = 0
            for key, data in scanner:
                if customers_found >= limit:
                    break
                
                customer_id = key.decode()
                city = data.get(b'info:city', b'N/A').decode()
                total_orders = data.get(b'analytics:total_orders', b'0').decode()
                
                print(f"  {customer_id}: {city}, Orders: {total_orders}")
                customers_found += 1
            
            print(f"Found {customers_found} customers in {state}")
            
        except Exception as e:
            print(f"Error scanning customers: {str(e)}")
    
    def scan_products_by_category(self, category, limit=10):
        # Scan products by category
        # This demonstrates another scan operation
        print(f"Scanning products in category: {category}")
        
        table = self.connection.table('product_data')
        
        try:
            # Scan products in specific category
            scanner = table.scan(filter=b"SingleColumnValueFilter('info', 'category', =, 'binary:{category}')")
            
            products_found = 0
            for key, data in scanner:
                if products_found >= limit:
                    break
                
                product_id = key.decode()
                weight = data.get(b'info:weight_g', b'0').decode()
                total_sold = data.get(b'sales:total_sold', b'0').decode()
                
                print(f"  {product_id}: {weight}g, Sold: {total_sold}")
                products_found += 1
            
            print(f"Found {products_found} products in {category}")
            
        except Exception as e:
            print(f"Error scanning products: {str(e)}")
    
    def delete_customer(self, customer_id):
        # Delete customer from HBase
        # This demonstrates delete operations
        print(f"Deleting customer: {customer_id}")
        
        table = self.connection.table('customer_data')
        
        try:
            # Delete customer
            table.delete(customer_id.encode())
            print(f"Customer {customer_id} deleted successfully!")
            return True
            
        except Exception as e:
            print(f"Error deleting customer: {str(e)}")
            return False
    
    def get_table_stats(self, table_name):
        # Get table statistics
        # This demonstrates table metadata operations
        print(f"Getting statistics for table: {table_name}")
        
        try:
            table = self.connection.table(table_name)
            
            # Count rows (this is a simple count, not efficient for large tables)
            row_count = 0
            for _ in table.scan():
                row_count += 1
                if row_count % 1000 == 0:
                    print(f"Counted {row_count} rows...")
            
            print(f"Table {table_name} has {row_count} rows")
            return row_count
            
        except Exception as e:
            print(f"Error getting table stats: {str(e)}")
            return 0
    
    def close_connection(self):
        # Close HBase connection
        # Always close the connection when done
        if self.connection:
            self.connection.close()
            print("HBase connection closed.")

def main():
    """
    Main function to demonstrate HBase operations
    """
    print("=== HBase E-Commerce Data Management Demo ===")
    
    # Initialize HBase manager
    hbase_manager = HBaseEcommerceManager()
    
    try:
        # Create tables
        print("\n1. Creating tables...")
        hbase_manager.create_customer_table()
        hbase_manager.create_product_table()
        
        # Load data (assuming CSV files are in the datasets directory)
        print("\n2. Loading data...")
        customers_loaded = hbase_manager.load_customer_data('../datasets/olist_customers_dataset.csv')
        products_loaded = hbase_manager.load_product_data('../datasets/olist_products_dataset.csv')
        
        if customers_loaded and products_loaded:
            # Demonstrate CRUD operations
            print("\n3. Demonstrating CRUD operations...")
            
            # Read operations
            print("\n--- READ Operations ---")
            hbase_manager.get_customer('00012e2b2831e78376053e16e3b0466e')
            hbase_manager.get_product('00066943e09f9d04247044b134f9f8c2')
            
            # Update operations
            print("\n--- UPDATE Operations ---")
            hbase_manager.update_customer_analytics('00012e2b2831e78376053e16e3b0466e', 5, 1250.75)
            hbase_manager.update_product_sales('00066943e09f9d04247044b134f9f8c2', 25, 1875.50)
            
            # Scan operations
            print("\n--- SCAN Operations ---")
            hbase_manager.scan_customers_by_state('SP', 5)
            hbase_manager.scan_products_by_category('beleza_saude', 5)
            
            # Get table statistics
            print("\n--- Table Statistics ---")
            hbase_manager.get_table_stats('customer_data')
            hbase_manager.get_table_stats('product_data')
            
            # Delete operation (commented out to avoid actually deleting data)
            # print("\n--- DELETE Operations ---")
            # hbase_manager.delete_customer('test_customer_id')
        
        print("\n=== HBase Demo Completed Successfully! ===")
        
    except Exception as e:
        print(f"Error in HBase demo: {str(e)}")
        sys.exit(1)
    
    finally:
        # Always close the connection
        hbase_manager.close_connection()

if __name__ == "__main__":
    main()
