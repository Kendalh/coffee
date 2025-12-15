#!/usr/bin/env python3
"""
Script to populate SQLite database with coffee bean CSV data.
"""

import argparse

import os
import re
import sqlite3
import csv
from pathlib import Path
from typing import Tuple


def parse_filename(filename: str) -> Tuple[str, int, int]:
    """
    Parse filename to extract provider, year, and month.
    
    Expected format: <provider>_<YYYYMM>.csv
    Example: 金粽_202501.csv -> ('金粽', 2025, 1)
    """
    # Remove extension
    basename = os.path.splitext(filename)[0]
    
    # Split by underscore
    parts = basename.split('_')
    if len(parts) < 2:
        raise ValueError(f"Invalid filename format: {filename}")
    
    # Extract provider (everything except the last part)
    provider = '_'.join(parts[:-1])
    
    # Extract date part (last part)
    date_part = parts[-1]
    if not date_part.isdigit() or len(date_part) != 6:
        raise ValueError(f"Invalid date format in filename: {filename}")
    
    year = int(date_part[:4])
    month = int(date_part[4:])
    
    return provider, year, month


def create_tables(conn: sqlite3.Connection):
    """Create the necessary tables if they don't exist."""
    with open('sql/coffee_bean_schema.sql', 'r') as f:
        coffee_bean_sql = f.read()
        conn.executescript(coffee_bean_sql)
    
    with open('sql/latest_data_schema.sql', 'r') as f:
        latest_data_sql = f.read()
        conn.executescript(latest_data_sql)
    
    conn.commit()

def drop_tables(conn: sqlite3.Connection):
    """Drop all tables."""
    conn.execute("DROP TABLE IF EXISTS coffee_bean")
    conn.execute("DROP TABLE IF EXISTS latest_data")
    conn.commit()
    print("Tables dropped successfully")


def insert_coffee_bean_data(conn: sqlite3.Connection, csv_file_path: str):
    """
    Insert coffee bean data from CSV file into the database.
    
    Args:
        conn: SQLite database connection
        csv_file_path: Path to the CSV file
    """
    filename = os.path.basename(csv_file_path)
    provider, data_year, data_month = parse_filename(filename)
    
    print(f"Processing file: {filename}")
    print(f"Provider: {provider}, Year: {data_year}, Month: {data_month}")
    
    with open(csv_file_path, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        
        # Prepare INSERT statement
        columns = reader.fieldnames + ['provider', 'data_year', 'data_month']
        placeholders = ', '.join(['?' for _ in columns])
        insert_sql = f"INSERT OR REPLACE INTO coffee_bean ({', '.join(columns)}) VALUES ({placeholders})"
        
        # Insert each row
        for row in reader:
            # Add provider and date information
            values = [row[col] if col in row else '' for col in reader.fieldnames]
            values.extend([provider, data_year, data_month])
            
            # Convert numeric fields
            # Convert numeric fields
            try:
                if 'price_per_kg' in row and row['price_per_kg']:
                    idx = reader.fieldnames.index('price_per_kg')
                    values[idx] = float(values[idx])
            except ValueError:
                pass
                
            try:
                if 'price_per_pkg' in row and row['price_per_pkg']:
                    idx = reader.fieldnames.index('price_per_pkg')
                    values[idx] = float(values[idx])
            except ValueError:
                pass
            
            # Convert harvest_season to integer
            try:
                if 'harvest_season' in row and row['harvest_season']:
                    idx = reader.fieldnames.index('harvest_season')
                    values[idx] = int(values[idx])
            except ValueError:
                pass
            
            conn.execute(insert_sql, values)
    
    # Update latest_data table
    update_latest_data(conn, provider, data_year, data_month)
    
    conn.commit()
    print(f"Successfully inserted data from {filename}")


def update_latest_data(conn: sqlite3.Connection, provider: str, data_year: int, data_month: int):
    """
    Update the latest_data table with the most recent provider data.
    
    Args:
        conn: SQLite database connection
        provider: Provider name
        data_year: Data year
        data_month: Data month
    """
    # Check if provider already exists
    cursor = conn.execute("SELECT data_year, data_month FROM latest_data WHERE provider = ?", (provider,))
    result = cursor.fetchone()
    
    should_update = False
    if result is None:
        # Provider not in table, insert new record
        should_update = True
    else:
        # Compare dates
        existing_year, existing_month = result
        if data_year > existing_year or (data_year == existing_year and data_month > existing_month):
            should_update = True
    
    if should_update:
        conn.execute("""
            INSERT OR REPLACE INTO latest_data (provider, data_year, data_month) 
            VALUES (?, ?, ?)
        """, (provider, data_year, data_month))
        print(f"Updated latest data for provider {provider}: {data_year}-{data_month:02d}")


def main():
    """Main function to populate the database with CSV data."""
    parser = argparse.ArgumentParser(description='Populate SQLite database with coffee bean CSV data.')
    parser.add_argument('--drop', action='store_true', help='Drop all tables before processing')
    parser.add_argument('--recreate', action='store_true', help='Drop and recreate all tables')
    parser.add_argument('files', nargs='*', help='CSV files to process')
    
    args = parser.parse_args()
    
    # Connect to SQLite database (will create if it doesn't exist)
    conn = sqlite3.connect('coffee_beans.db')
    
    try:
        # Handle drop/recreate options
        if args.drop or args.recreate:
            drop_tables(conn)
        
        if args.recreate or not args.drop:
            # Create tables
            create_tables(conn)
            print("Tables created successfully")
        
        if args.drop or args.recreate:
            return
        
        # Process specified files or all CSV files in golden_data directory
        if args.files:
            csv_files = [Path(f) for f in args.files]
        else:
            golden_data_path = Path('golden_data')
            if not golden_data_path.exists():
                print("Error: golden_data directory not found")
                return
            
            csv_files = list(golden_data_path.glob('*.csv'))
            
        if not csv_files:
            print("No CSV files found to process")
            return
        
        print(f"Found {len(csv_files)} CSV files to process")
        
        for csv_file in csv_files:
            try:
                insert_coffee_bean_data(conn, str(csv_file))
            except Exception as e:
                print(f"Error processing {csv_file}: {e}")
                continue
        
        # Print summary
        cursor = conn.execute("SELECT COUNT(*) FROM coffee_bean")
        count = cursor.fetchone()[0]
        print(f"\nTotal records in database: {count}")
        
        cursor = conn.execute("SELECT provider, data_year, data_month FROM latest_data")
        latest_records = cursor.fetchall()
        print("\nLatest data by provider:")
        for provider, year, month in latest_records:
            print(f"  {provider}: {year}-{month:02d}")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()