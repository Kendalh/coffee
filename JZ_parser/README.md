# JZ Parser - PDF Coffee Bean Quotation Extractor

This tool extracts text from PDF coffee bean quotation files and splits them into separate sections for common and premium beans.

## Features

- Uses `pdfplumber` for accurate PDF text extraction
- Identifies sections "常用生豆报价单" and "精品生豆报价单" (handles variable spacing between Chinese characters)
- Creates separate TXT files for each section
- Adds separators (`==========`) before each coffee bean entry
- Supports coffee bean codes in formats like:
  - S1-2 (letter + number + hyphen + number)
  - P-1 (letter + hyphen + number)
  - S23-3 (letter + numbers + hyphen + number)
  - LA-1 / CB-1 (two letters + hyphen + number)
  - S66 (letter + numbers, followed by space or newline)

## Installation

1. Install required dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Or specifically install pdfplumber:
   ```
   pip install pdfplumber
   ```

## Usage

### Command Line

```bash
python pdf_extractor.py input.pdf -o output_directory
```

### Examples

Process a single PDF file:
```bash
python pdf_extractor.py quotation.pdf -o extracted_texts
```

Process multiple PDF files:
```bash
python pdf_extractor.py *.pdf -o extracted_texts
```

## Output Files

The script generates two TXT files for each PDF:
- `<filename>_common.txt` - Contains the "常用生豆报价单" section
- `<filename>_premium.txt` - Contains the "精品生豆报价单" section

Each coffee bean entry in the output files will be preceded by a separator line (`==========`).

## How It Works

1. The script uses `pdfplumber` to accurately extract text from PDF files
2. It identifies the section boundaries using regular expressions that handle variable spacing in Chinese characters
3. It splits the content into appropriate sections
4. It adds separators before each coffee bean entry based on pattern matching
5. Finally, it saves each section as a separate TXT file

## Error Handling

- If `pdfplumber` is not installed, the script will show an error message
- If a PDF file cannot be opened or processed, the script will continue with other files
- If no sections are found, no output files will be created for that section