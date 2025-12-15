#!/usr/bin/env python3
"""
CSV Merger Tool

This script processes coffee bean JSON files and merges them into a CSV format.
It handles file patterns, extracts bean types, processes fields, and filters data
according to the specified requirements.
"""

import json
import csv
import os
import re
import argparse
from pathlib import Path
from typing import List, Dict, Any


def extract_bean_type(filename: str) -> str:
    """
    Extract bean type (common or premium) from filename.
    Expected pattern: <provider>_<YYYYMM>_<type>_<chunk>.json
    """
    # Look for common or premium in the filename
    if '_common_' in filename:
        return 'common'
    elif '_premium_' in filename:
        return 'premium'
    else:
        # Try to extract from the pattern <provider>_<YYYYMM>_<type>_<chunk>.json
        parts = filename.split('_')
        if len(parts) >= 3:
            # The third part should be the type
            potential_type = parts[2].lower()
            if potential_type in ['common', 'premium']:
                return potential_type
        return 'unknown'


def process_field_value(field_name: str, value: str) -> str:
    """
    Process field values according to requirements:
    - For name, flavor_profile, origin: replace commas with spaces
    - For harvest_season: extract only the year as YYYY format
    """
    if value is None or value == "None" or value == "":
        return ''
    
    value = str(value)
    
    # Handle fields that need comma replacement
    if field_name in ['name', 'flavor_profile', 'origin', 'variety']:
        # Replace commas and Chinese punctuation with spaces
        value = re.sub(r'[,，、]+', ' ', value)
        # Clean up extra spaces
        value = re.sub(r'\s+', ' ', value).strip()
    
    # Handle harvest_season to extract year
    elif field_name == 'harvest_season':
        # Extract 4-digit year
        year_match = re.search(r'(19|20)\d{2}', value)
        if year_match:
            return year_match.group(0)
        # If no 4-digit year found, try to extract any year-like pattern
        year_match = re.search(r'\d{4}', value)
        if year_match:
            return year_match.group(0)
        return ''
    
    return value


def extract_country_from_name(name: str) -> str:
    """
    Extract country from the name field (first space-delimited part)
    """
    if not name:
        return ''
    
    # Split by space and take the first part
    parts = name.split(' ')
    if parts:
        return parts[0]
    return ''


def process_json_file(file_path: str) -> List[Dict[str, Any]]:
    """
    Process a JSON file and extract coffee beans data
    """
    beans_data = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Extract bean type from filename
        bean_type = extract_bean_type(os.path.basename(file_path))
        
        # Process each page in the JSON
        for page in data:
            if 'coffee_beans' in page:
                for bean in page['coffee_beans']:
                    # Skip if name is empty/None
                    if not bean.get('name') or bean.get('name') == "None" or bean.get('name') == "":
                        continue
                    
                    # Create a new record with processed fields
                    processed_bean = {}
                    
                    # Copy all existing fields and process them
                    for key, value in bean.items():
                        processed_bean[key] = process_field_value(key, value)
                    
                    # Add the type field
                    processed_bean['type'] = bean_type
                    
                    # Add country field
                    processed_bean['country'] = extract_country_from_name(processed_bean.get('name', ''))
                    
                    # Extract year from harvest_season
                    if 'harvest_season' in processed_bean:
                        processed_bean['harvest_season'] = process_field_value('harvest_season', processed_bean['harvest_season'])
                    
                    beans_data.append(processed_bean)
    except Exception as e:
        print(f"Error processing file {file_path}: {e}")
    
    return beans_data


def merge_json_to_csv(file_pattern: str, output_csv: str = None):
    """
    Merge JSON files matching the pattern into a CSV file
    """
    # Find all files matching the pattern
    files = list(Path('.').glob(file_pattern))
    
    if not files:
        print(f"No files found matching pattern: {file_pattern}")
        return
    
    print(f"Found {len(files)} files matching pattern: {file_pattern}")
    
    # If no output CSV specified, generate from pattern
    if not output_csv:
        # Use the pattern prefix for output filename
        pattern_parts = file_pattern.split('/')
        if len(pattern_parts) > 1:
            prefix = pattern_parts[-1].split('*')[0].rstrip('_')
            output_csv = f"{prefix}_all.csv"
        else:
            output_csv = "merged_coffee_beans.csv"
    
    # Collect all beans data
    all_beans = []
    for file_path in files:
        print(f"Processing file: {file_path}")
        beans = process_json_file(str(file_path))
        print(f"  Extracted {len(beans)} beans from {file_path}")
        all_beans.extend(beans)
    
    if not all_beans:
        print("No coffee beans data found in the files.")
        return
    
    # Define the standard field order for the CSV
    fieldnames = [
        'name', 'type', 'country', 'flavor_profile', 'origin', 'harvest_season',
        'code', 'price_per_kg', 'price_per_pkg', 'grade', 'altitude', 
        'density', 'processing_method', 'variety'
    ]
    
    # Write to CSV with explicit quoting to handle special characters
    with open(output_csv, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        
        for bean in all_beans:
            # Ensure all fields are present in the bean data
            row = {}
            for field in fieldnames:
                row[field] = bean.get(field, '')
            writer.writerow(row)
    
    print(f"Successfully merged {len(all_beans)} coffee beans into {output_csv}")


def main():
    parser = argparse.ArgumentParser(description='Merge coffee bean JSON files into CSV')
    parser.add_argument('file_pattern', help='Wildcard pattern for JSON files (e.g., silver_data/金粽_202505_*)')
    parser.add_argument('-o', '--output', help='Output CSV filename (optional)')
    
    args = parser.parse_args()
    
    merge_json_to_csv(args.file_pattern, args.output)


if __name__ == '__main__':
    main()