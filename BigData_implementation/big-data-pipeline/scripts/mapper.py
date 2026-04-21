#!/usr/bin/env python3

#MapReduce Mapper for E-Commerce Sales Analysis

import sys
import csv

def main():
    """
    Main mapper function
    Reading each line from stdin and extracting product information
    Emitting product_category and sales amount for each order item
    """
    
    # Creating CSV reader to handle comma-separated values
    reader = csv.reader(sys.stdin)
    
    # Skipping header row if it exists
    # Checking if the first line looks like a header
    first_line = True
    
    for row in reader:
        # Skipping empty lines
        if not row or len(row) == 0:
            continue
            
        # Skipping header row (first row with column names)
        if first_line and row[0] == 'order_id':
            first_line = False
            continue
        
        first_line = False
        
        try:
            # Extracting relevant columns from order_items dataset
            
            if len(row) >= 7:
                order_id = row[0]
                order_item_id = row[1] 
                product_id = row[2]
                seller_id = row[3]
                price = float(row[5])  # price is at index 5
                freight_value = float(row[6])  # freight_value is at index 6
                
                # Calculating total amount for this order item (price + freight)
                total_amount = price + freight_value
                
                # Emitting product_id and total amount
                # The reducer will aggregate these by product
                print(f"{product_id}\t{total_amount}")
                
        except (ValueError, IndexError) as e:
            # Handling malformed data gracefully
            print(f"ERROR: Malformed line - {row}", file=sys.stderr)
            continue

if __name__ == "__main__":
    main()
