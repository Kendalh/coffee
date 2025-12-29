# SQL Query Tool for LLMs

This tool enables LLMs (like DeepSeek) to execute SQL queries against the coffee bean database and retrieve structured results.

## Overview

The SQL Query Tool provides a safe and structured interface for LLMs to interact with the `coffee_beans.db` SQLite database. It includes security measures to prevent data modification and returns results in a format suitable for LLM consumption.

## Features

- Execute SELECT queries against the coffee bean database
- Parameterized queries to prevent SQL injection
- Schema inspection capabilities
- Sample data retrieval
- Structured result formatting
- Built-in security validation (only SELECT statements allowed)

## Installation

```bash
pip install pandas
```

The tool uses `sqlite3` which is part of Python's standard library, so no additional installation is required for database connectivity.

## Usage

### Basic Usage

```python
from qa-agent.sql_query_tool import SQLQueryTool

# Initialize the tool
tool = SQLQueryTool(db_path="coffee_beans.db")

# Execute a query
query = "SELECT name, country, price_per_kg FROM coffee_bean WHERE country = ?"
params = ["BRAZIL"]
result = tool.run_query(query, params)

if result["success"]:
    print(f"Found {result['row_count']} results:")
    for row in result["results"]:
        print(row)
else:
    print(f"Error: {result['error']}")
```

### Available Methods

1. `run_query(query, params=None)` - Execute an SQL SELECT query
2. `get_table_schema(table_name="coffee_bean")` - Get table schema information
3. `get_sample_data(table_name="coffee_bean", limit=5)` - Get sample data from a table

### LLM Tool Definitions

The tool provides pre-defined function schemas for use with LLMs:

- `get_tool_definition()` - For executing SQL queries
- `get_schema_tool_definition()` - For getting table schemas
- `get_sample_tool_definition()` - For getting sample data

## Database Schema

The main table is `coffee_bean` with the following columns:
- `name`: Coffee bean name (part of primary key)
- `type`: Type of coffee (e.g., premium, common)
- `country`: Country of origin
- `flavor_profile`: Description of flavors
- `flavor_category`: Category of flavors
- `origin`: Specific region/origin
- `harvest_season`: Harvest season/year (INTEGER)
- `code`: Product code
- `price_per_kg`: Price per kilogram
- `price_per_pkg`: Price per package
- `sold_out`: Boolean indicating if item is sold out
- `grade`: Quality grade
- `altitude`: Growing altitude
- `density`: Bean density
- `processing_method`: Processing method used
- `variety`: Coffee variety
- `humidity`: Humidity level
- `plot`: Plot information
- `estate`: Estate information
- `provider`: Data provider (extracted from filename)
- `data_year`: Year of data (part of primary key)
- `data_month`: Month of data (part of primary key)

Primary Key: (data_year, data_month, name)

## Security

- Only SELECT statements are allowed
- Parameterized queries prevent SQL injection
- Direct access to other SQL operations (INSERT, UPDATE, DELETE, DROP) is blocked

## Example Queries

```sql
-- Find premium coffee beans from Brazil
SELECT name, country, price_per_kg, flavor_profile 
FROM coffee_bean 
WHERE country = 'BRAZIL' AND type = 'premium';

-- Get the most expensive coffee beans
SELECT name, country, price_per_kg 
FROM coffee_bean 
ORDER BY price_per_kg DESC 
LIMIT 5;

-- Find coffee beans by flavor profile
SELECT name, country, flavor_profile 
FROM coffee_bean 
WHERE flavor_profile LIKE '%citrus%';
```