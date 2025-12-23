from flask import Flask, request, jsonify, render_template
import logging
from datetime import datetime
import csv
import random
import os

# Import the coffee service
from coffee_service import CoffeeQueryService

# Import the coffee filters
from coffee_filters import CountryFilter, ProviderFilter, TypeFilter, get_all_countries, get_all_providers, get_all_types, get_all_flavor_categories

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[
        logging.StreamHandler()  # Log to console by default
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__, template_folder='templates')

# Initialize the coffee query service
coffee_service = CoffeeQueryService()

def load_random_coffee():
    """Load a random coffee from the CSV file"""
    csv_file = os.path.join(os.path.dirname(__file__), 'premium_coffee.csv')
    try:
        with open(csv_file, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            coffees = [row for row in reader if row['名称'].strip()]
            if coffees:
                return random.choice(coffees)
    except Exception as e:
        logger.error("Error loading coffee data: %s", str(e))
    return {}

def convert_coffee_to_features(coffee):
    """Convert coffee data to features format"""
    # Define flavor options
    flavors = [
        "明亮果酸型(Bright & Fruity Acidity)",
        "花香茶感型(Floral & Tea-like)",
        "果汁感热带水果型(Juicy & Tropical Fruit)",
        "均衡圆润型(Balanced & Clean)",
        "巧克力坚果调型(Chocolate & Nutty)",
        "焦糖甜感型(Caramel Sweetness)",
        "酒香发酵型(Winey & Fermented)",
        "烟熏木质型(Earthy & Spicy)"
    ]
    
    # Clean up altitude data (handle ranges)
    altitude = coffee.get('海拔(m)', '')
    if isinstance(altitude, str) and '-' in altitude:
        try:
            # Take the average of the range
            parts = altitude.split('-')
            min_alt = float(parts[0].strip())
            max_alt = float(parts[1].strip().split()[0])  # Handle cases like "1500-2000 2025"
            altitude = (min_alt + max_alt) / 2
        except:
            # If conversion fails, leave as is
            pass
    
    # Convert moisture content to float if possible
    moisture = coffee.get('含水量(%)', '')
    if isinstance(moisture, str) and moisture.replace('.', '', 1).isdigit():
        moisture = float(moisture)
        
    return {
        "origin": coffee.get('产地', ''),
        "variety": coffee.get('品种', ''),
        "density": coffee.get('密度(g/l)', ''),
        "altitude": altitude,
        "moisture_content": moisture,
        "processing_method": coffee.get('处理法', ''),
        "grade": coffee.get('等级', ''),
        "desired_flavor": random.choice(flavors)  # Randomly select a flavor
    }

@app.before_request
def log_request_info():
    logger.info('Request: %s %s; Headers: %s; Body: %s', 
        request.method, request.url, dict(request.headers), request.get_data())

@app.after_request
def log_response_info(response):
    logger.info('Response: %s %s', response.status, response.get_data(as_text=True))
    return response

@app.route('/')
def index():
    # Load a random coffee as default values
    random_coffee = load_random_coffee()
    coffee_features = convert_coffee_to_features(random_coffee)
    
    # Define flavor options
    flavors = [
        "明亮果酸型(Bright & Fruity Acidity)",
        "花香茶感型(Floral & Tea-like)",
        "果汁感热带水果型(Juicy & Tropical Fruit)",
        "均衡圆润型(Balanced & Clean)",
        "巧克力坚果调型(Chocolate & Nutty)",
        "焦糖甜感型(Caramel Sweetness)",
        "酒香发酵型(Winey & Fermented)",
        "烟熏木质型(Earthy & Spicy)"
    ]
    
    return render_template('index.html', coffee=coffee_features, flavors=flavors)

@app.route('/roast-recommendation', methods=['POST'])
def roast_recommendation():
    try:
        # Get JSON data from request
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        # Import the roast plan recommender
        from roast_plan_recommender import get_roast_recommendations
        
        # Get roast recommendations
        recommendations = get_roast_recommendations(data)
        
        return jsonify(recommendations)
        
    except Exception as e:
        logger.error("Error processing request: %s", str(e))
        return jsonify({"error": "Internal server error"}), 500

# Coffee query endpoints
@app.route('/api/coffee-beans', methods=['GET'])
def get_coffee_beans():
    """Get all coffee beans with pagination support and optional filters."""
    try:
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 10))
        country = request.args.get('country')
        bean_type = request.args.get('type')
        flavor_category = request.args.get('flavor_category')
        
        # Validate page size
        if page_size not in [10, 50, 100]:
            page_size = 10
            
        # Build SQL query with optional filters
        conditions = ["provider = ?"]
        params = ['金粽']
        
        if country:
            conditions.append("country = ?")
            params.append(country)
            
        if bean_type:
            conditions.append("type = ?")
            params.append(bean_type)
            
        if flavor_category:
            conditions.append("flavor_category = ?")
            params.append(flavor_category)
            
        where_clause = "WHERE " + " AND ".join(conditions)
        sql_query = f"SELECT * FROM coffee_bean {where_clause} ORDER BY name"
        
        result = coffee_service.query_coffee_beans(
            sql_query=sql_query,
            params=tuple(params),
            page=page, 
            page_size=page_size
        )
        return jsonify(result)
        
    except Exception as e:
        logger.error("Error processing request: %s", str(e))
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/coffee-beans/search', methods=['POST'])
def search_coffee_beans():
    """Search coffee beans using a custom SQL query."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
            
        sql_query = data.get('query')
        params = data.get('params', [])
        page = data.get('page', 1)
        page_size = data.get('page_size', 10)
        
        if not sql_query:
            return jsonify({"error": "SQL query is required"}), 400
            
        # Validate page size
        if page_size not in [10, 50, 100]:
            page_size = 10
            
        # Security check: ensure query is selecting from coffee_bean table
        if not sql_query.lower().strip().startswith('select'):
            return jsonify({"error": "Only SELECT queries are allowed"}), 400
            
        result = coffee_service.query_coffee_beans(
            sql_query=sql_query,
            params=tuple(params),
            page=page,
            page_size=page_size
        )
        return jsonify(result)
        
    except Exception as e:
        logger.error("Error processing request: %s", str(e))
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/coffee-beans/<name>/<int:year>/<int:month>', methods=['GET'])
def get_coffee_bean(name, year, month):
    """Get a specific coffee bean by name and date."""
    try:
        coffee_bean = coffee_service.get_coffee_bean_by_name(name, year, month)
        if coffee_bean:
            return jsonify(coffee_bean.to_dict())
        else:
            return jsonify({"error": "Coffee bean not found"}), 404
            
    except Exception as e:
        logger.error("Error processing request: %s", str(e))
        return jsonify({"error": "Internal server error"}), 500


@app.route('/api/coffee-beans/<name>/price-trends', methods=['GET'])
def get_coffee_bean_price_trends(name):
    """Get price trends for a specific coffee bean across all time periods."""
    try:
        price_trends = coffee_service.get_price_trends(name)
        if price_trends:
            return jsonify(price_trends)
        else:
            return jsonify([])  # Return empty array if no data found
            
    except Exception as e:
        logger.error("Error processing request: %s", str(e))
        return jsonify({"error": "Internal server error"}), 500


# Filter endpoints
@app.route('/api/filters/countries', methods=['GET'])
def get_countries():
    """Get all available countries for filtering."""
    try:
        countries = get_all_countries()
        # Return as a sorted list
        return jsonify(sorted(list(countries)))
    except Exception as e:
        logger.error("Error processing request: %s", str(e))
        return jsonify({"error": "Internal server error"}), 500


@app.route('/api/filters/providers', methods=['GET'])
def get_providers():
    """Get all available providers for filtering."""
    try:
        providers = get_all_providers()
        # Return as a sorted list
        return jsonify(sorted(list(providers)))
    except Exception as e:
        logger.error("Error processing request: %s", str(e))
        return jsonify({"error": "Internal server error"}), 500


@app.route('/api/filters/flavor-categories', methods=['GET'])
def get_flavor_categories():
    """Get all available flavor categories for filtering."""
    try:
        flavor_categories = get_all_flavor_categories()
        # Return as a sorted list
        return jsonify(sorted(list(flavor_categories)))
    except Exception as e:
        logger.error("Error processing request: %s", str(e))
        return jsonify({"error": "Internal server error"}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=False, threaded=True)