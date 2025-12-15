CREATE TABLE IF NOT EXISTS latest_data (
    provider TEXT PRIMARY KEY,
    data_year INTEGER,
    data_month INTEGER,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);