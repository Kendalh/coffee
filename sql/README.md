# SQLite Database Schema

This directory contains the SQL schema files for the coffee bean database.

## Tables

### coffee_bean
Stores the coffee bean data from CSV files with additional metadata.

Fields:
- `name`: Coffee bean name (part of primary key)
- `type`: Type of coffee (e.g., premium, common)
- `country`: Country of origin
- `flavor_profile`: Description of flavors
- `origin`: Specific region/origin
- `harvest_season`: Harvest season/year (INTEGER)
- `code`: Product code
- `price_per_kg`: Price per kilogram
- `price_per_pkg`: Price per package
- `grade`: Quality grade
- `altitude`: Growing altitude
- `density`: Bean density
- `processing_method`: Processing method used
- `variety`: Coffee variety
- `provider`: Data provider (extracted from filename)
- `data_year`: Year of data (extracted from filename) (part of primary key)
- `data_month`: Month of data (extracted from filename) (part of primary key)

Primary Key: (data_year, data_month, name)

### latest_data
Tracks the latest data available for each provider.

Fields:
- `provider`: Data provider name (PRIMARY KEY)
- `data_year`: Latest data year for this provider
- `data_month`: Latest data month for this provider
- `last_updated`: Timestamp when record was last updated

## Usage

The database is populated using the `sqlite_populator.py` script in the root directory:

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

This script will:
1. Create the SQLite database (`coffee_beans.db`) if it doesn't exist
2. Create the tables using the schema files in this directory
3. Parse all CSV files specified or in the `golden_data` directory
4. Extract provider and date information from filenames
5. Insert coffee bean data into the `coffee_bean` table (using INSERT OR REPLACE to handle updates)
6. Update the `latest_data` table with the most recent data for each provider