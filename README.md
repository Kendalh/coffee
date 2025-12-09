# Simple Python Web App

A basic RESTful web application that responds with "Hello Python Web".

## Endpoints

- `GET /` - Returns "Hello Python Web"

## How to Run

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