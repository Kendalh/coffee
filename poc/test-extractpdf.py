#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple PDF Text Extractor

This script extracts all text content from a PDF file and saves it as plain text,
preserving the original structure and spacing as much as possible using pdfplumber.

Usage:
    python test-extractpdf.py input.pdf output.txt
"""

import sys
import argparse
import pdfplumber


def extract_text_from_pdf(pdf_path):
    """
    Extract text from a PDF file while preserving structure and spacing using pdfplumber.
    
    Args:
        pdf_path (str): Path to the input PDF file
        
    Returns:
        str: Extracted text content
    """
    text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                # Extract text from each page and preserve line breaks
                page_text = page.extract_text()
                if page_text:  # Check if text was extracted
                    text += page_text + "\n\n"  # Add extra newline between pages
                else:
                    # If no text extracted, try alternative method
                    page_text = page.extract_text_simple()
                    if page_text:
                        text += page_text + "\n\n"
    except Exception as e:
        print(f"Error reading PDF file: {e}")
        return ""
    
    return text


def save_text_to_file(text, output_path):
    """
    Save extracted text to a file.
    
    Args:
        text (str): Text content to save
        output_path (str): Path to the output text file
    """
    try:
        with open(output_path, 'w', encoding='utf-8') as file:
            file.write(text)
        print(f"Text successfully extracted and saved to: {output_path}")
    except Exception as e:
        print(f"Error saving text to file: {e}")


def main():
    """Main function to parse arguments and process PDF extraction."""
    parser = argparse.ArgumentParser(
        description="Extract text from a PDF file and save as plain text using pdfplumber",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python test-extractpdf.py input.pdf output.txt
  python test-extractpdf.py document.pdf extracted_text.txt
        """
    )
    
    parser.add_argument(
        'input_file',
        help='Input PDF file to extract text from'
    )
    
    parser.add_argument(
        'output_file',
        help='Output text file to save extracted content'
    )
    
    # If no arguments provided, show help
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)
    
    args = parser.parse_args()
    
    # Validate input file
    if not args.input_file.lower().endswith('.pdf'):
        print("Error: Input file must be a PDF file (.pdf)")
        sys.exit(1)
    
    # Extract text from PDF
    print(f"Extracting text from: {args.input_file}")
    extracted_text = extract_text_from_pdf(args.input_file)
    
    if not extracted_text:
        print("Warning: No text extracted from the PDF file. The file might be image-based or protected.")
    
    # Save extracted text to output file
    save_text_to_file(extracted_text, args.output_file)


if __name__ == "__main__":
    main()