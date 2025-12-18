#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF Coffee Bean Quotation Extractor

This script extracts text from a PDF coffee bean quotation file using pdfplumber,
identifies two key sections ("常用生豆报价单" and "精品生豆报价单"),
and creates separate TXT files for each section with proper formatting.

Features:
- Uses pdfplumber for accurate PDF text extraction
- Handles variable spacing in Chinese section headers
- Identifies coffee beans by their codes (S1-2, P-1, etc.)
- Adds separators before each coffee bean entry
"""

import os
import re
import argparse
from pathlib import Path
import pdfplumber

# Constants
COFFEE_BEAN_SEPARATOR = "=========="
COFFEE_BEAN_PATTERN = r'(?m)^([A-Z]+\d*-\d+[A-Z]*|[A-Z]\d+)'

def find_section_boundaries(pdf_text: str) -> dict:
    """
    Find the boundaries of the common and premium sections in the PDF text.
    Handles cases where Chinese characters may be space-separated.
    
    Args:
        pdf_text (str): Full PDF text
        
    Returns:
        dict: Dictionary with section boundaries {'common': (start, end), 'premium': (start, end)}
    """
    # Patterns to match section headers (accounting for possible spaces)
    common_patterns = [
        r"常用\s*生\s*豆\s*报\s*价\s*单",
        r"常用生豆报价单",
        r"常\s*用\s*生\s*豆\s*报\s*价\s*单",
        r"常用\s*豆\s*报\s*价\s*单",
        r"常用豆报价单",
        r"常\s*用\s*豆\s*报\s*价\s*单"
    ]
    
    premium_patterns = [
        r"精\s*品\s*生\s*豆\s*报\s*价\s*单",
        r"精品生豆报价单",
        r"精\s*品\s*生\s*豆\s*报\s*价\s*单",
        r"精\s*品\s*豆\s*报\s*价\s*单",
        r"精品豆报价单",
        r"精\s*品\s*豆\s*报\s*价\s*单"
    ]
    
    boundaries = {'common': (-1, -1), 'premium': (-1, -1)}
    
    # Find common section start
    common_start = -1
    for pattern in common_patterns:
        match = re.search(pattern, pdf_text)
        if match:
            common_start = match.start()
            break
    
    # Find premium section start
    premium_start = -1
    for pattern in premium_patterns:
        match = re.search(pattern, pdf_text)
        if match:
            premium_start = match.start()
            break
    
    # Determine section boundaries
    if common_start != -1 and premium_start != -1:
        # Both sections exist
        if common_start < premium_start:
            # Common section: from common_start to premium_start (exclusive)
            boundaries['common'] = (common_start, premium_start)
            # Premium section: from premium_start to end of document
            boundaries['premium'] = (premium_start, len(pdf_text))
        else:
            # Premium section: from premium_start to common_start (exclusive)
            boundaries['premium'] = (premium_start, common_start)
            # Common section: from common_start to end of document
            boundaries['common'] = (common_start, len(pdf_text))
    elif common_start != -1:
        # Only common section
        boundaries['common'] = (common_start, len(pdf_text))
    elif premium_start != -1:
        # Only premium section
        boundaries['premium'] = (premium_start, len(pdf_text))
    
    return boundaries


def add_coffee_bean_separators(text: str) -> str:
    """
    Add separators before each coffee bean entry in the text.
    
    Coffee bean entries typically start with patterns like:
    - Letter(s) followed by hyphen and number(s) (e.g., S1-2, S66-1, LA-1)
    - Letter followed by number(s) (e.g., S65, S2)
    - Complex patterns with slashes (e.g., S62-1/S62-2)
    
    Args:
        text (str): Text to process
        
    Returns:
        str: Text with separators added before coffee bean entries
    """
    # Add separator before each match using the constant
    # The pattern matches at the beginning of lines without capturing leading whitespace
    result = re.sub(COFFEE_BEAN_PATTERN, COFFEE_BEAN_SEPARATOR + '\n\\1', text)
    
    return result


def count_coffee_beans(text: str) -> int:
    """
    Count the number of coffee bean entries in the text.
    
    Args:
        text (str): Text to count coffee beans in
        
    Returns:
        int: Number of coffee bean entries
    """
    # Use the constant pattern to match coffee bean codes
    matches = re.findall(COFFEE_BEAN_PATTERN, text)
    return len(matches)


def split_text_by_coffee_beans(text: str, max_beans: int) -> list: 
    """
    Split text into chunks with a maximum number of coffee beans per chunk.
    
    Args:
        text (str): Text to split
        max_beans (int): Maximum number of coffee beans per chunk 
        
    Returns:
        list: List of text chunks
    """
    # First, ensure the text has separators added
    if not text.startswith(COFFEE_BEAN_SEPARATOR):
        text = COFFEE_BEAN_SEPARATOR + '\n' + text
    
    # Split the text by separators to get individual bean entries
    parts = text.split(COFFEE_BEAN_SEPARATOR + '\n')
    
    # The first part is empty (because we split at the beginning), so remove it
    if parts and parts[0] == '':
        parts = parts[1:]
    
    if len(parts) <= max_beans:
        # If we have fewer beans than the max, return the whole text with proper formatting
        return [COFFEE_BEAN_SEPARATOR + '\n' + (COFFEE_BEAN_SEPARATOR + '\n').join(parts)]
    
    # Split into chunks
    chunks = []
    for i in range(0, len(parts), max_beans):
        chunk_parts = parts[i:i + max_beans]
        chunk_text = COFFEE_BEAN_SEPARATOR + '\n' + (COFFEE_BEAN_SEPARATOR + '\n').join(chunk_parts)
        chunks.append(chunk_text)
    
    return chunks


def extract_sections_to_txt(input_pdf_path: str, output_dir: str, max_beans_per_chunk: int):  # Added parameter
    """
    Extract sections from PDF and save as TXT files.
    
    Args:
        input_pdf_path (str): Path to input PDF file
        output_dir (str): Directory to save output TXT files
        max_beans_per_chunk (int): Maximum number of beans per chunk 
    """
    try:
        # Extract filename components
        input_path = Path(input_pdf_path)
        filename = input_path.stem
        file_extension = input_path.suffix
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        print(f"Processing: {input_pdf_path}")
        print(f"Output directory: {output_dir}")
        
        # Extract text using pdfplumber
        pdf_text = ""
        try:
            with pdfplumber.open(input_pdf_path) as pdf:
                for page in pdf.pages:
                    pdf_text += page.extract_text() + "\n"
        except ImportError:
            print("Error: pdfplumber is not installed. Please install it using 'pip install pdfplumber'")
            return
        except Exception as e:
            print(f"Error opening PDF file: {e}")
            return
        
        if not pdf_text:
            print(f"Warning: Could not extract text from {input_pdf_path}")
            return
        
        # Find section boundaries
        boundaries = find_section_boundaries(pdf_text)
        print(f"Found sections: {boundaries}")
        
        # Process common section
        if boundaries['common'][0] != -1:
            common_start, common_end = boundaries['common']
            common_text = pdf_text[common_start:common_end]
            
            # Add separators before coffee bean entries
            common_text = add_coffee_bean_separators(common_text)
            
            # Count coffee beans in common section
            common_bean_count = count_coffee_beans(common_text)
            print(f"Common section has {common_bean_count} coffee beans")
            
            # Split into chunks if more than max_beans_per_chunk beans
            if common_bean_count > max_beans_per_chunk:  # Changed from hardcoded 100
                common_chunks = split_text_by_coffee_beans(common_text, max_beans_per_chunk)  # Use parameter
                print(f"Splitting common section into {len(common_chunks)} chunks")
                
                for i, chunk in enumerate(common_chunks):
                    common_filename = f"{filename}_common_{i+1}.txt"
                    common_path = os.path.join(output_dir, common_filename)
                    
                    with open(common_path, 'w', encoding='utf-8') as f:
                        f.write(chunk)
                    
                    print(f"Created: {common_filename}")
            else:
                # Save common section
                common_filename = f"{filename}_common.txt"
                common_path = os.path.join(output_dir, common_filename)
                
                with open(common_path, 'w', encoding='utf-8') as f:
                    f.write(common_text)
                
                print(f"Created: {common_filename}")
        
        # Process premium section
        if boundaries['premium'][0] != -1:
            premium_start, premium_end = boundaries['premium']
            premium_text = pdf_text[premium_start:premium_end]
            
            # Add separators before coffee bean entries
            premium_text = add_coffee_bean_separators(premium_text)
            
            # Count coffee beans in premium section
            premium_bean_count = count_coffee_beans(premium_text)
            print(f"Premium section has {premium_bean_count} coffee beans")
            
            # Split into chunks if more than max_beans_per_chunk beans
            if premium_bean_count > max_beans_per_chunk:  # Changed from hardcoded 100
                premium_chunks = split_text_by_coffee_beans(premium_text, max_beans_per_chunk)  # Use parameter
                print(f"Splitting premium section into {len(premium_chunks)} chunks")
                
                for i, chunk in enumerate(premium_chunks):
                    premium_filename = f"{filename}_premium_{i+1}.txt"
                    premium_path = os.path.join(output_dir, premium_filename)
                    
                    with open(premium_path, 'w', encoding='utf-8') as f:
                        f.write(chunk)
                    
                    print(f"Created: {premium_filename}")
            else:
                # Save premium section
                premium_filename = f"{filename}_premium.txt"
                premium_path = os.path.join(output_dir, premium_filename)
                
                with open(premium_path, 'w', encoding='utf-8') as f:
                    f.write(premium_text)
                
                print(f"Created: {premium_filename}")
        
        print("Processing completed successfully!")
        
    except Exception as e:
        print(f"Error processing {input_pdf_path}: {e}")


def process_multiple_pdfs(input_paths: list, output_dir: str, max_beans_per_chunk: int):  # Added parameter
    """
    Process multiple PDF files.
    
    Args:
        input_paths (list): List of input PDF file paths
        output_dir (str): Directory to save output TXT files
        max_beans_per_chunk (int): Maximum number of beans per chunk 
    """
    for pdf_path in input_paths:
        if os.path.isfile(pdf_path) and pdf_path.lower().endswith('.pdf'):
            extract_sections_to_txt(pdf_path, output_dir, max_beans_per_chunk)  # Pass parameter
        else:
            print(f"Skipping {pdf_path} (not a PDF file)")


def main():
    """Main function to parse arguments and process PDF files."""
    parser = argparse.ArgumentParser(
        description="Extract text from PDF coffee bean quotation files and split into sections",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python pdf_extractor.py input.pdf -o output_folder
  python pdf_extractor.py *.pdf -o extracted_texts
        """
    )
    
    parser.add_argument(
        'input_files',
        nargs='+',
        help='Input PDF files to process'
    )
    
    parser.add_argument(
        '-o', '--output-dir',
        default='extracted_texts',
        help='Output directory for extracted TXT files (default: extracted_texts)'
    )
    
    parser.add_argument(  # Added new argument
        '--max-beans-per-chunk',
        type=int,
        default=30,
        help='Maximum number of coffee beans per chunk file (default: 30)'
    )
    
    args = parser.parse_args()
    
    # Process the PDF files with the max_beans_per_chunk parameter
    process_multiple_pdfs(args.input_files, args.output_dir, args.max_beans_per_chunk)


if __name__ == "__main__":
    main()