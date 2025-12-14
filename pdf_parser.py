#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF Coffee Bean Quotation Parser

This script parses PDF files containing coffee bean quotations and generates CSV files
based on the requirements in prompt.MD.

The PDF files should be named in the format <Brand>_<YYYYMM>.pdf
Two CSV files are generated per PDF:
1. For beans in "常用生豆报价单" section
2. For beans in "精品生豆" section

Features extracted include:
咖啡豆名, 风味, 产区, 品种, 等级, 含水量, 处理法, 密度值, 海拔, 规格, 产季, 每公斤价格, 每5公斤价格, 整包价格
"""

import os
import re
import csv
import json
from pathlib import Path
from typing import List, Dict
import PyPDF2
from openai import OpenAI


# Field names in Chinese as per requirements
FIELD_NAMES = [
    "咖啡豆名", "风味", "产区", "品种", "等级", "含水量", 
    "处理法", "密度值", "海拔", "规格", "产季", "每公斤价格", "每5公斤价格", "整包价格"
]


def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extract text content from a PDF file.
    
    Args:
        pdf_path (str): Path to the PDF file
        
    Returns:
        str: Extracted text content
    """
    text = ""
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
    except Exception as e:
        print(f"Error extracting text from {pdf_path}: {e}")
        return ""
    
    return text


def parse_pdf_with_llm(pdf_text: str, brand: str, date: str) -> Dict[str, List[List[str]]]:
    """
    Parse PDF content using LLM to extract coffee bean information.
    
    Args:
        pdf_text (str): Extracted text from PDF
        brand (str): Brand name from filename
        date (str): Date from filename (YYYYMM)
        
    Returns:
        Dict[str, List[List[str]]]: Parsed data for both sections
    """
    
    # System prompt for the LLM
    system_prompt = """You are an expert at parsing coffee bean quotation documents. 
    Your task is to extract structured data from the provided PDF text.
    
    The document contains two sections:
    1. "常用生豆报价单" (Common Green Bean Quotations)
    2. "精品生豆报价单" (Premium Green Bean Quotations)
    
    For each coffee bean entry in both sections, extract the following fields:
    咖啡豆名 (Coffee Bean Name), 风味 (Flavor), 产区 (Origin), 品种 (Variety), 等级 (Grade), 
    含水量 (Moisture Content), 处理法 (Processing Method), 密度值 (Density), 海拔 (Altitude), 
    规格 (Specifications), 产季 (Harvest Season), 每公斤价格 (Price per KG), 每5公斤价格 (Price per 5KG), 
    整包价格 (Bulk Price)
    
    Important formatting rules:
    1. If any content contains ',', replace it with ' ' (space)
    2. For the 咖啡豆名 field, remove all spaces in the name
    3. If fields can't be extracted, leave them blank
    
    Respond with a structured JSON format containing:
    {
        "common_beans": [["咖啡豆名", "风味", "产区", ...], [...]],
        "premium_beans": [["咖啡豆名", "风味", "产区", ...], [...]]
    }
    """
    
    # User prompt with the PDF content
    user_prompt = f"""Parse the following coffee bean quotation PDF from {brand} dated {date}.
    
    PDF Content:
    {pdf_text[:4000]}  # Limiting to first 4000 chars to avoid token limits
    
    Extract the coffee bean information from both "常用生豆报价单" and "精品生豆" sections.
    
    Expected JSON Response Format:
    {{
        "common_beans": [["咖啡豆名", "风味", "产区", "品种", "等级", "含水量", "处理法", "密度值", "海拔", "规格", "产季", "每公斤价格", "每5公斤价格", "整包价格"], [...]],
        "premium_beans": [["咖啡豆名", "风味", "产区", "品种", "等级", "含水量", "处理法", "密度值", "海拔", "规格", "产季", "每公斤价格", "每5公斤价格", "整包价格"], [...]]
    }}
    """
    
    client = OpenAI(
        api_key=os.getenv("DASHSCOPE_API_KEY", "sk-712886a429ba4813b5d8643ad8070219"),
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        timeout=120.0
    )
    
    try:
        completion = client.chat.completions.create(
            model="qwen-plus",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
            timeout=120.0
        )
        
        # Parse and return the response
        response_data = json.loads(completion.choices[0].message.content)
        return response_data
        
    except Exception as e:
        print(f"Error parsing PDF with LLM: {e}")
        # Return empty structure on error
        return {
            "common_beans": [FIELD_NAMES],
            "premium_beans": [FIELD_NAMES]
        }


def save_to_csv(data: List[List[str]], csv_path: str):
    """
    Save data to CSV file.
    
    Args:
        data (List[List[str]]): Data to save
        csv_path (str): Path to save CSV file
    """
    try:
        with open(csv_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerows(data)
        print(f"CSV file saved: {csv_path}")
    except Exception as e:
        print(f"Error saving CSV file {csv_path}: {e}")


def process_pdf_file(pdf_path: str) -> bool:
    """
    Process a single PDF file and generate CSV files.
    
    Args:
        pdf_path (str): Path to the PDF file
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Extract brand and date from filename
        filename = Path(pdf_path).stem
        if '_' not in filename:
            print(f"Invalid filename format: {filename}. Expected format: <Brand>_<YYYYMM>")
            return False
            
        brand, date = filename.split('_', 1)
        
        # Validate date format
        if not re.match(r'^\d{6}$', date):
            print(f"Invalid date format in filename: {date}. Expected format: YYYYMM")
            return False
        
        # Extract text from PDF
        print(f"Extracting text from {pdf_path}...")
        pdf_text = extract_text_from_pdf(pdf_path)
        if not pdf_text:
            print(f"Failed to extract text from {pdf_path}")
            return False
            
        # Parse with LLM
        print(f"Parsing content with LLM...")
        parsed_data = parse_pdf_with_llm(pdf_text, brand, date)
        
        # Generate CSV filenames
        common_csv_path = f"{brand}_{date}_common.csv"
        premium_csv_path = f"{brand}_{date}_premium.csv"
        
        # Save CSV files
        print(f"Saving CSV files...")
        save_to_csv(parsed_data.get("common_beans", [FIELD_NAMES]), common_csv_path)
        save_to_csv(parsed_data.get("premium_beans", [FIELD_NAMES]), premium_csv_path)
        
        print(f"Successfully processed {pdf_path}")
        return True
        
    except Exception as e:
        print(f"Error processing {pdf_path}: {e}")
        return False


def process_pdf_directory(directory_path: str = "."):
    """
    Process all PDF files in a directory.
    
    Args:
        directory_path (str): Path to directory containing PDF files
    """
    pdf_files = list(Path(directory_path).glob("*.pdf"))
    
    if not pdf_files:
        print(f"No PDF files found in {directory_path}")
        return
    
    print(f"Found {len(pdf_files)} PDF files to process")
    
    success_count = 0
    for pdf_file in pdf_files:
        if process_pdf_file(str(pdf_file)):
            success_count += 1
    
    print(f"\nProcessing complete: {success_count}/{len(pdf_files)} files processed successfully")


def main():
    """Main function to process PDF files."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Parse PDF coffee bean quotation files and generate CSV files")
    parser.add_argument("pdf_files", nargs="*", help="PDF files to process")
    parser.add_argument("--dir", "-d", default=".", help="Directory containing PDF files to process")
    
    args = parser.parse_args()
    
    if args.pdf_files:
        # Process specific PDF files
        for pdf_file in args.pdf_files:
            process_pdf_file(pdf_file)
    else:
        # Process all PDF files in directory
        process_pdf_directory(args.dir)


if __name__ == "__main__":
    main()