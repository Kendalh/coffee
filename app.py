from flask import Flask, request, jsonify, render_template
import logging
from datetime import datetime
import csv
import random
import os

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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=False, threaded=True)