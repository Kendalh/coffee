#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF Coffee Bean Quotation Chunker

This script takes a raw coffee bean quotation PDF and splits it into smaller chunks
based on sections: "常用豆报价单" and "精品豆报价单".

Features:
- Identifies sections even when Chinese characters have spaces
- Creates separate PDFs for each section
- Chunks large sections (>10 pages) into 10-page segments
- Names files as <Brand>_<YYYYMM>_<section>_<chunk>.pdf
"""

import os
import re
import argparse
from pathlib import Path
import PyPDF2


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
    
    # Determine section boundaries - completely reworked to avoid any overlap
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




def create_chunked_pdfs(input_pdf_path: str, output_dir: str, max_pages_per_chunk: int = 10):
    """
    Create chunked PDFs based on sections.
    
    Args:
        input_pdf_path (str): Path to input PDF file
        output_dir (str): Directory to save output PDFs
        max_pages_per_chunk (int): Maximum pages per chunk
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
        
        # Extract text to find sections
        with open(input_pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            pdf_text = ""
            page_texts = []
            for page in pdf_reader.pages:
                page_text = page.extract_text() + "\n"
                pdf_text += page_text
                page_texts.append(page_text)
        
        if not pdf_text:
            print(f"Warning: Could not extract text from {input_pdf_path}")
            return
        
        # Find section boundaries
        boundaries = find_section_boundaries(pdf_text)
        print(f"Found sections: {boundaries}")
        
        # Adjust boundaries to prevent overlap
        sorted_sections = [(name, bounds) for name, bounds in boundaries.items() if bounds[0] != -1]
        sorted_sections.sort(key=lambda x: x[1][0])  # Sort by start position
        
        adjusted_boundaries = {}
        for i, (section_name, (section_start, section_end)) in enumerate(sorted_sections):
            if i < len(sorted_sections) - 1:
                # Not the last section, adjust end to just before next section starts
                next_section_start = sorted_sections[i + 1][1][0]
                adjusted_boundaries[section_name] = (section_start, next_section_start)
            else:
                # Last section, keep original end
                adjusted_boundaries[section_name] = (section_start, section_end)
        
        print(f"Adjusted boundaries: {adjusted_boundaries}")
        
        # Map adjusted boundaries to page ranges
        total_pages = len(pdf_reader.pages)
        section_page_ranges = {}
        
        # Find page numbers for each section by checking which page contains the section start/end
        for section_name, (section_start, section_end) in adjusted_boundaries.items():
            if section_start == -1:
                print(f"No {section_name} section found")
                continue
            
            # Find start page
            start_page = -1
            cumulative_length = 0
            for page_num, page_text in enumerate(page_texts):
                page_end = cumulative_length + len(page_text)
                if cumulative_length <= section_start < page_end:
                    start_page = page_num
                    break
                cumulative_length = page_end
            
            if start_page == -1:
                print(f"Could not determine start page for {section_name} section")
                continue
            
            # Find end page
            end_page = total_pages  # Default to end of document
            
            # For non-last sections, find the page that contains the section end
            if section_end < len(pdf_text):
                cumulative_length = 0
                for page_num, page_text in enumerate(page_texts):
                    page_end = cumulative_length + len(page_text)
                    if cumulative_length <= section_end <= page_end:
                        end_page = page_num
                        break
                    cumulative_length = page_end
            
            section_page_ranges[section_name] = (start_page, end_page)
            print(f"{section_name} section: pages {start_page+1}-{end_page}")
        
        # Process each section
        for section_name, (start_page, end_page) in section_page_ranges.items():
            print(f"Processing {section_name} section...")
            
            total_pages = end_page - start_page
            if total_pages <= 0:
                print(f"Skipping {section_name} section (no pages)")
                continue
                
            print(f"{section_name} section: {total_pages} pages (pages {start_page+1}-{end_page})")
            
            # Determine section type for filename
            section_type = "common" if section_name == "common" else "premium"
            
            if total_pages <= max_pages_per_chunk:
                # Single PDF for this section
                output_filename = f"{filename}_{section_type}_1.pdf"
                output_path = os.path.join(output_dir, output_filename)
                
                create_section_pdf(input_pdf_path, output_path, start_page, end_page)
                print(f"Created: {output_filename}")
            else:
                # Chunk into multiple PDFs
                chunk_num = 1
                current_page = start_page
                
                while current_page < end_page:
                    chunk_end_page = min(current_page + max_pages_per_chunk, end_page)
                    
                    output_filename = f"{filename}_{section_type}_{chunk_num}.pdf"
                    output_path = os.path.join(output_dir, output_filename)
                    
                    create_section_pdf(input_pdf_path, output_path, current_page, chunk_end_page)
                    print(f"Created: {output_filename} (pages {current_page+1}-{chunk_end_page})")
                    
                    current_page = chunk_end_page
                    chunk_num += 1
        
        print("Processing completed successfully!")
        
    except Exception as e:
        print(f"Error processing {input_pdf_path}: {e}")


def create_section_pdf(input_pdf_path: str, output_pdf_path: str, start_page: int, end_page: int):
    """
    Create a new PDF file containing only the specified page range.
    
    Args:
        input_pdf_path (str): Path to the original PDF file
        output_pdf_path (str): Path for the new section PDF
        start_page (int): Start page index (0-based, inclusive)
        end_page (int): End page index (0-based, exclusive)
    """
    try:
        # Create PDF writer
        pdf_writer = PyPDF2.PdfWriter()
        
        # Extract pages
        with open(input_pdf_path, 'rb') as input_file:
            pdf_reader = PyPDF2.PdfReader(input_file)
            
            # Extract pages in the specified range
            for page_num in range(start_page, min(end_page, len(pdf_reader.pages))):
                pdf_writer.add_page(pdf_reader.pages[page_num])
        
        # Write to output file
        with open(output_pdf_path, 'wb') as output_file:
            pdf_writer.write(output_file)
            
    except Exception as e:
        print(f"Error creating section PDF {output_pdf_path}: {e}")


def process_multiple_pdfs(input_paths: list, output_dir: str, max_pages_per_chunk: int = 10):
    """
    Process multiple PDF files.
    
    Args:
        input_paths (list): List of input PDF file paths
        output_dir (str): Directory to save output PDFs
        max_pages_per_chunk (int): Maximum pages per chunk
    """
    for pdf_path in input_paths:
        if os.path.isfile(pdf_path) and pdf_path.lower().endswith('.pdf'):
            create_chunked_pdfs(pdf_path, output_dir, max_pages_per_chunk)
        else:
            print(f"Skipping {pdf_path} (not a PDF file)")


def main():
    """Main function to parse arguments and process PDF files."""
    parser = argparse.ArgumentParser(
        description="Chunk PDF coffee bean quotation files into sections",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python pdf_chunk.py input.pdf -o output_folder
  python pdf_chunk.py *.pdf -o chunks
  python pdf_chunk.py quotation.pdf --max-pages 5 -o small_chunks
        """
    )
    
    parser.add_argument(
        'input_files',
        nargs='+',
        help='Input PDF files to process'
    )
    
    parser.add_argument(
        '-o', '--output-dir',
        default='chunks',
        help='Output directory for chunked PDFs (default: chunks)'
    )
    
    parser.add_argument(
        '--max-pages',
        type=int,
        default=5,
        help='Maximum pages per chunk (default: 5)'
    )
    
    args = parser.parse_args()
    
    # Process the PDF files
    process_multiple_pdfs(args.input_files, args.output_dir, args.max_pages)


if __name__ == "__main__":
    main()