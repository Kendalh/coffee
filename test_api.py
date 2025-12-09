import requests
import json
import csv
import random
from typing import Dict, Any
from enum import Enum

class DesiredFlavor(Enum):
    """Enumeration of desired flavor profiles"""
    BRIGHT_FRUITY_ACIDITY = "明亮果酸型(Bright & Fruity Acidity)"
    FLORAL_TEA_LIKE = "花香茶感型(Floral & Tea-like)"
    JUICY_TROPICAL_FRUIT = "果汁感热带水果型(Juicy & Tropical Fruit)"
    BALANCED_CLEAN = "均衡圆润型(Balanced & Clean)"
    CHOCOLATE_NUTTY = "巧克力坚果调型(Chocolate & Nutty)"
    CARAMEL_SWEETNESS = "焦糖甜感型(Caramel Sweetness)"
    WINEY_FERMENTED = "酒香发酵型(Winey & Fermented)"
    EARTHY_SPICY = "烟熏木质型(Earthy & Spicy)"

def load_coffee_data(csv_file: str) -> list:
    """
    Load coffee data from CSV file
    
    Args:
        csv_file (str): Path to the CSV file
        
    Returns:
        list: List of dictionaries containing coffee data
    """
    coffees = []
    with open(csv_file, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            # Skip empty rows
            if row['名称'].strip():
                coffees.append(row)
    return coffees

def convert_coffee_to_features(coffee: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert coffee data to features format for the API
    
    Args:
        coffee (dict): Coffee data from CSV
        
    Returns:
        dict: Formatted coffee features
    """
    # Randomly select a desired flavor
    desired_flavor = random.choice(list(DesiredFlavor)).value
    
    # Map CSV fields to API fields
    features = {
        "origin": coffee.get('产地', ''),
        "variety": coffee.get('品种', ''),
        "density": coffee.get('密度(g/l)', ''),
        "altitude": coffee.get('海拔(m)', ''),
        "moisture_content": coffee.get('含水量(%)', ''),
        "processing_method": coffee.get('处理法', ''),
        "grade": coffee.get('等级', ''),
        "desired_flavor": desired_flavor  # Randomly selected flavor
    }
    
    # Clean up altitude data (handle ranges)
    altitude = features["altitude"]
    if isinstance(altitude, str) and '-' in altitude:
        try:
            # Take the average of the range
            parts = altitude.split('-')
            min_alt = float(parts[0].strip())
            max_alt = float(parts[1].strip().split()[0])  # Handle cases like "1500-2000 2025"
            features["altitude"] = (min_alt + max_alt) / 2
        except:
            # If conversion fails, leave as is
            pass
    
    # Convert moisture content to float if possible
    moisture = features["moisture_content"]
    if isinstance(moisture, str) and moisture.replace('.', '', 1).isdigit():
        features["moisture_content"] = float(moisture)
        
    return features

def test_roast_recommendation(coffee_features: Dict[str, Any], coffee_name: str):
    """
    Test the roast recommendation API with given coffee features
    
    Args:
        coffee_features (dict): Coffee features for the API
        coffee_name (str): Name of the coffee being tested
    """
    # API endpoint
    url = "http://localhost:5002/roast-recommendation"
    
    print(f"\n{'='*60}")
    print(f"Testing Roast Recommendation for: {coffee_name}")
    print(f"{'='*60}")
    
    # Display coffee features
    print("\nCoffee Features:")
    for key, value in coffee_features.items():
        print(f"  {key}: {value}")
    
    # Make the request
    try:
        response = requests.post(url, json=coffee_features, timeout=60)
        
        # Print the response
        if response.status_code == 200:
            print("\n✅ Roast Recommendations Received:")
            response_data = response.json()
            
            # Print general suggestions
            print("\n📍 GENERAL SUGGESTIONS:")
            print("-" * 30)
            general_suggestions = response_data.get("general_suggestions", "No general suggestions provided")
            print(general_suggestions)
            
            # Print artisan alog profiles
            print("\n📋 ARTISAN ALOG PROFILES:")
            print("-" * 30)
            phases = response_data.get("artisan_alog", {}).get("phases", [])
            for i, phase in enumerate(phases, 1):
                print(f"\n{i}. {phase.get('phase', 'Unknown Phase')}")
                print(f"   Temperature: {phase.get('temperature', 'N/A')}")
                print(f"   RoR: {phase.get('ror', 'N/A')}")
                print(f"   Notes: {phase.get('notes', 'No notes provided')}")
        else:
            print(f"\n❌ Error: {response.status_code}")
            print(response.text)
            
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Request failed: {e}")
    except json.JSONDecodeError as e:
        print(f"\n❌ Failed to decode JSON response: {e}")

def main():
    """
    Main function to load coffee data, select random samples, and test the API
    """
    # Load coffee data
    csv_file = "premium_coffee.csv"
    try:
        coffees = load_coffee_data(csv_file)
        print(f"Loaded {len(coffees)} coffee entries from {csv_file}")
    except FileNotFoundError:
        print(f"Error: Could not find {csv_file}")
        return
    except Exception as e:
        print(f"Error loading coffee data: {e}")
        return
    
    # Select 2 random coffees (skip the header row)
    if len(coffees) < 2:
        print("Not enough coffee data to sample from")
        return
        
    random_coffees = random.sample(coffees, min(2, len(coffees)))
    
    # Test each coffee
    for i, coffee in enumerate(random_coffees, 1):
        print(f"\n{'='*80}")
        print(f"SAMPLE {i}: {coffee.get('名称', 'Unknown Coffee')}")
        print(f"{'='*80}")
        
        # Convert to features format
        coffee_features = convert_coffee_to_features(coffee)
        
        # Test the API
        test_roast_recommendation(coffee_features, coffee.get('名称', 'Unknown Coffee'))

if __name__ == "__main__":
    main()