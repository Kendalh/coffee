# Simple Python Web App

A basic RESTful web application that responds with "Hello Python Web".

## Coffee Bean Data Processing Pipeline

This project implements a complete pipeline for processing raw coffee bean quotation PDFs and populating the data into a relational database. The pipeline consists of four main components:

1. **PDF Chunker** (`pdf_chunk.py`) - Splits large PDF quotation files into smaller sections based on content (common beans vs premium beans)
2. **LLM Parser** (`llm_parser.py`) - Uses AI to extract structured data from PDF sections and convert to JSON format
3. **CSV Merger** (`csv_merger.py`) - Combines JSON files from multiple sources into consolidated CSV files
4. **SQLite Populator** (`sqlite_populator.py`) - Populates the SQLite database with data from CSV files

The complete workflow processes raw PDFs through multiple stages, converting binary PDFs to structured data before storing in a relational database.

### 1. PDF Chunker (pdf_chunk.py)

Splits large PDF quotation files into manageable chunks based on content sections.

**Usage:**
```bash
python3 pdf_chunk.py input.pdf -o output_folder
python3 pdf_chunk.py *.pdf -o chunks
python3 pdf_chunk.py quotation.pdf --max-pages 5 -o small_chunks
```

**Features:**
- Identifies sections like "常用豆报价单" (common beans) and "精品豆报价单" (premium beans)
- Handles Chinese character spacing variations
- Chunks large sections into smaller PDFs (default: 5 pages per chunk)
- Names files with descriptive patterns: `<Brand>_<YYYYMM>_<section>_<chunk>.pdf`

### 2. LLM Parser (llm_parser.py)

Uses DeepSeek AI to extract structured coffee bean data from PDF sections and convert to JSON format.

**Usage:**
```bash
python3 llm_parser.py input_section.pdf -o output.json
python3 llm_parser.py chunk_*.pdf -o parsed_data
```

**Features:**
- Extracts structured data including name, flavor profile, prices, origin, etc.
- Handles multi-page PDFs with proper pagination
- Outputs JSON format with page-level organization
- Processes multiple files in batch mode

### 3. CSV Merger (csv_merger.py)

Combines multiple JSON files into consolidated CSV files for easier processing.

**Usage:**
```bash
python3 csv_merger.py "silver_data/金粽_202505_*" -o merged_coffee_beans.csv
python3 csv_merger.py "silver_data/*" -o all_coffee_beans.csv
```

**Features:**
- Merges data from multiple JSON sources
- Standardizes field formats (comma replacement, year extraction)
- Adds bean type classification (common/premium)
- Generates clean CSV output with proper quoting

### 4. SQLite Populator (sqlite_populator.py)

Populates the SQLite database with coffee bean data from CSV files.

**Usage:**
```bash
# Process all CSV files in golden_data directory
python3 sqlite_populator.py

# Process specific CSV files
python3 sqlite_populator.py golden_data/金粽_202501.csv golden_data/金粽_202505.csv

# Drop and recreate tables, then process all files
python3 sqlite_populator.py --recreate

# Drop tables only
python3 sqlite_populator.py --drop
```

**Options:**
- `--drop` - Drop all tables before processing
- `--recreate` - Drop and recreate all tables
- `files` - One or more CSV files to process (if not specified, processes all files in `golden_data` directory)

**Features:**
- Creates SQLite database (`coffee_beans.db`) if it doesn't exist
- Uses composite primary key `(data_year, data_month, name)` for proper data updates
- Tracks latest data available for each provider
- Supports INSERT OR REPLACE for data override capability

## Web Application

### Endpoints

- `GET /` - Returns "Hello Python Web"

### How to Run

1. Install the required dependencies:
   ```
   python3 -m pip install -r requirements.txt
   ```

2. Run the application:
   ```
   python3 app.py
   ```

3. Open your browser and navigate to `http://localhost:5002`

## Running with Log Output to File

To redirect logs to a specific file, you can use one of these methods:

### Method 1: Shell redirection
```
python3 app.py > app.log 2>&1
```

### Method 2: Using the logging configuration in code
The application is configured to log to both console and file. By default, it logs to console, but you can modify the logging configuration in `app.py` to also log to a file by adding a FileHandler:

```python
# In app.py, modify the handlers section to include:
handlers=[
    logging.StreamHandler(),  # Log to console
    logging.FileHandler('app.log')  # Log to file
]
```

The application will display "Hello Python Web" when you visit the root endpoint and will log detailed information about each request and response.