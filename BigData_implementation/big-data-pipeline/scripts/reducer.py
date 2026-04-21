#!/usr/bin/env python3

#MapReduce Reducer for E-Commerce Sales Analysis

import sys

def main():
    """
    Main reducer function
    Reading mapper output and aggregating sales by product
    Calculating total sales amount and count of orders for each product
    """
    
    current_product = None
    total_sales = 0.0
    order_count = 0
    
    # Reading each line from stdin (mapper output)
    for line in sys.stdin:
        # Removing whitespace and splitting by tab
        line = line.strip()
        if not line:
            continue
            
        try:
            # Splitting the line into product_id and amount
            product_id, amount = line.split('\t')
            
            # Converting amount to float
            amount = float(amount)
            
            # Checking if we're still processing the same product
            if current_product == product_id:
                # Same product, adding to running totals
                total_sales += amount
                order_count += 1
            else:
                # New product, outputting results for previous product (if any)
                if current_product is not None:
                    print(f"{current_product}\t{total_sales:.2f}\t{order_count}")
                
                # Starting tracking new product
                current_product = product_id
                total_sales = amount
                order_count = 1
                
        except (ValueError, IndexError) as e:
            # Handling malformed data gracefully
            print(f"ERROR: Malformed line - {line}", file=sys.stderr)
            continue
    
    # Don't forget to output the last product
    if current_product is not None:
        print(f"{current_product}\t{total_sales:.2f}\t{order_count}")

if __name__ == "__main__":
    main()
