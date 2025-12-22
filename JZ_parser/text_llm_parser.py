#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Text Coffee Bean Parser with DeepSeek API

This script parses text files containing coffee bean information using the DeepSeek API
and converts them to JSON format similar to the LLM output.
"""

import json
import argparse
import os
import re
import requests
from requests.exceptions import Timeout
from typing import List, Dict, Any
from pathlib import Path


class CoffeeBeanTextAnalyzer:
    
    def __init__(self, api_key: str, model: str = "deepseek-chat"):
        self.api_key = api_key
        self.model = model
        self.api_url = "https://api.deepseek.com/v1/chat/completions"
        
    def create_prompt(self) -> str:
        """Create a prompt for parsing coffee bean information from text."""
        prompt = """
Please analyze the following coffee bean quotation text and extract all coffee bean information. 


Parsing Requirements:
1. Coffee beans are separated by "==========".
2. Extract the following fields for each coffee bean:
   - code: The coffee bean code (e.g., "I-2")
   - name: The full name of the coffee bean (Extract the Chinese name)
   - country: The country of origin (Extract Chinese)
   - flavor_profile: Flavor characteristics (followed by 风味：)
   - price_per_kg: Price per kilogram (number)
   - price_per_pkg: Package price (number)
   - origin: Origin/region information (possible fields are 产地、产区)
   - plot: More detailed plot information (field to parse is 地块), leave to None if not present
   - estate: Estate information (field to parse is 庄园), leave to None is not present
   - grade: Grade of the coffee bean
   - humidity: Moisture content (with %)
   - altitude: Growing altitude
   - density: Density value (with g/l)
   - processing_method: Processing method
   - harvest_season: Harvest season/year
   - variety: Coffee variety
   - sold_out: If there is "售罄", mark this field as True, otherwise False
Extra Process: 
   - Some of the name attributes will have double countires like "哥伦比亚 哥伦比亚 慧兰 苏帕摩", "卢旺达 卢旺达 波旁种 水洗 15目+". In such cases, dedup the county name in the name. 

Important Instructions:
1. Process the text sequentially from top to bottom
2. When you encounter a coffee bean code (like I-2, C-1, etc.) (Separated by "=========="), begin extracting information for that bean
3. Continue extracting until you reach the next separator or end of text
4. Prices are usually in format like "￥84/KG" or "￥74/KG"
6. Structure the output as a JSON array with page objects containing coffee_beans arrays
7. Output ONLY valid JSON, no other text

Example Output Format:
[
  {
    "page": 1,
    "coffee_beans": [
      {
        "code": "I-2",
        "name": "印度尼西亚 苏门答腊 曼特宁G1",
        "country": "印度尼西亚",
        "flavor_profile": "草药，香料，坚果，巧克力，焦糖，低酸值，醇厚，油脂丰富",
        "price_per_kg": 84.0,
        "price_per_pkg": 74.0,
        "origin": "Sumatra",
        "plot": "A地块",
        "estate": "曼特宁庄园",
        "grade": "G1",
        "humidity": "13.5%",
        "altitude": "1300-1600M",
        "density": "860g/l",
        "processing_method": "湿刨法",
        "harvest_season": "2024年",
        "variety": "Mandeling",
        "sold_out": False
      }
    ]
  }
]
Begin parsing the following text:
"""
        return prompt
    
    def _prepare_text_analysis(self, text_content: str, temperature: float, streaming: bool) -> tuple:
        """Prepare text analysis with DeepSeek API."""
        # Prepare request headers
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Prepare payload
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": self.create_prompt() + f"\n\n{text_content}"
                }
            ],
            "stream": streaming,
            "temperature": temperature,  # Lower temperature for less creativity
            "max_tokens": 8100  # DeepSeek's limit is 8192
        }
        
        return headers, payload
    
    def analyze_text_streaming(self, text_content: str, temperature: float = 0.1) -> List[Dict[str, Any]]:
        """Analyze text content using DeepSeek API with streaming."""
        # Prepare analysis
        headers, payload = self._prepare_text_analysis(text_content, temperature, True)
        
        print("Starting text analysis with streaming...")
        try:
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                stream=True,
                timeout=600  # 10 minute timeout
            )
            
            if response.status_code != 200:
                print(f"API request failed with status code: {response.status_code}")
                return []
            
            # Collect streaming response
            full_response = ""
            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    
                    # Process SSE format
                    if line.startswith("data: "):
                        data = line[6:]  # Remove "data: " prefix
                        
                        if data == "[DONE]":
                            print("\nStreaming response ended")
                            break
                        
                        try:
                            chunk = json.loads(data)
                            if "choices" in chunk and len(chunk["choices"]) > 0:
                                delta = chunk["choices"][0].get("delta", {})
                                content = delta.get("content", "")
                                
                                if content:
                                    full_response += content
                        except json.JSONDecodeError:
                            continue
            
            print("\n" + "=" * 50)
            
            # Process the response
            return self._process_response_content(full_response)
                
        except Timeout:
            print("Request timed out (10 minutes). Skipping file processing.")
            return []
        except Exception as e:
            print(f"Error during analysis: {e}")
            return []
    
    def analyze_text(self, text_content: str, temperature: float = 0.1) -> List[Dict[str, Any]]:
        """Analyze text content using DeepSeek API without streaming."""
        # Prepare analysis
        headers, payload = self._prepare_text_analysis(text_content, temperature, False)
        
        print("Starting text analysis...")
        try:
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=600  # 10 minute timeout
            )
            
            if response.status_code != 200:
                print(f"API request failed with status code: {response.status_code}")
                return []
            
            # Parse response
            response_data = response.json()
            
            if "choices" in response_data and len(response_data["choices"]) > 0:
                content = response_data["choices"][0]["message"]["content"]
                return self._process_response_content(content)
            else:
                print("No valid content found in response")
                return []
                
        except Timeout:
            print("Request timed out (10 minutes). Skipping file processing.")
            return []
        except Exception as e:
            print(f"Error during analysis: {e}")
            return []
    
    def _process_response_content(self, content: str) -> List[Dict[str, Any]]:
        """Process the response content and extract JSON."""
        # Extract JSON from response
        try:
            # Find the first JSON object or array
            json_str = self.extract_first_json_object(content)
            
            if json_str:
                # Try to parse JSON
                try:
                    result = json.loads(json_str)
                except json.JSONDecodeError as je:
                    raise je  # Re-raise the original exception
                    
                # Validate and clean data
                cleaned_result = self.clean_results(result)
                return cleaned_result
            else:
                print("No valid JSON data found")
                # Print part of response for debugging
                print(f"Response preview: {content[:500]}...")
                return []
                
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {e}")
            print(f"Raw response length: {len(content)} characters")
            # Print part of response for debugging
            print(f"Response preview: {content[:500]}...")
            return []
    
    def extract_first_json_object(self, text: str) -> str:
        """
        Extract the first complete JSON object or array from text.
        """
        # Find first '{' or '[' position
        start_brace = text.find('{')
        start_bracket = text.find('[')
        
        # Determine start position
        if start_brace == -1 and start_bracket == -1:
            return ""
        elif start_brace == -1:
            start_pos = start_bracket
            end_char = ']'
        elif start_bracket == -1:
            start_pos = start_brace
            end_char = '}'
        else:
            # Select the earlier one
            if start_brace < start_bracket:
                start_pos = start_brace
                end_char = '}'
            else:
                start_pos = start_bracket
                end_char = ']'
        
        # Find matching end symbol from start position
        bracket_count = 0
        in_string = False
        escape_next = False
        
        for i in range(start_pos, len(text)):
            char = text[i]
            
            # Handle escape characters
            if escape_next:
                escape_next = False
                continue
                
            if char == '\\':
                escape_next = True
                continue
                
            # Handle strings
            if char == '"' and not escape_next:
                in_string = not in_string
                continue
                
            # Skip all characters if inside string
            if in_string:
                continue
                
            # Count brackets
            if (end_char == ']' and char == '[') or (end_char == '}' and char == '{'):
                bracket_count += 1
            elif (end_char == ']' and char == ']') or (end_char == '}' and char == '}'):
                bracket_count -= 1
                if bracket_count == 0:
                    # Found matching end symbol
                    json_str = text[start_pos:i+1]
                    # Clean JSON string
                    json_str = json_str.replace('\n', '').replace('\r', '')
                    json_str = ' '.join(json_str.split())
                    return json_str
        
        # If no complete JSON object found, try simple extraction
        if start_pos != -1:
            # Try to extract content from start position to reasonable length
            end_pos = min(start_pos + 10000, len(text))  # Limit length
            json_str = text[start_pos:end_pos]
            # Try to clean and return
            json_str = json_str.replace('\n', '').replace('\r', '')
            json_str = ' '.join(json_str.split())
            return json_str
        
        # Return empty string if no JSON object found
        return ""    
    
    def clean_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Clean and validate extracted results."""
        if not isinstance(results, list):
            print(f"Warning: Expected list type result, but got {type(results)}")
            return []
        
        cleaned = []
        
        for i, page_data in enumerate(results):
            if not isinstance(page_data, dict):
                print(f"Warning: Item {i+1} is not dict type, skipping")
                continue
                
            page_num = page_data.get("page", 0)
            coffee_beans = page_data.get("coffee_beans", [])
            
            # Validate page_num
            if not isinstance(page_num, int) or page_num <= 0:
                print(f"Warning: Invalid page number {page_num}, using index {i+1}")
                page_num = i + 1
            
            # Validate coffee_beans
            if not isinstance(coffee_beans, list):
                print(f"Warning: coffee_beans on page {page_num} is not list type, skipping")
                coffee_beans = []
            
            cleaned_beans = []
            for j, bean in enumerate(coffee_beans):
                if not isinstance(bean, dict):
                    print(f"Warning: Bean {j+1} on page {page_num} is not dict type, skipping")
                    continue
                
                # Clean price fields
                price = bean.get("price_per_kg")
                if isinstance(price, str):
                    # Try to extract number from string
                    import re
                    price_match = re.search(r'[\d.]+', str(price))
                    if price_match:
                        try:
                            price = float(price_match.group())
                        except ValueError:
                            price = None
                    else:
                        price = None
                elif not isinstance(price, (int, float)) and price is not None:
                    price = None
                
                # Ensure all required fields exist with correct types
                cleaned_bean = {
                    "code": str(bean.get("code", "")),
                    "name": str(bean.get("name", "")),
                    "country": str(bean.get("country", "")),
                    "flavor_profile": str(bean.get("flavor_profile", "")),
                    "price_per_kg": price,
                    "price_per_pkg": bean.get("price_per_pkg"),  # Keep original type
                    "origin": str(bean.get("origin", "")),
                    "plot": str(bean.get("plot", "")),
                    "estate": str(bean.get("estate", "")),
                    "grade": str(bean.get("grade", "")),
                    "humidity": str(bean.get("humidity", "")),
                    "altitude": str(bean.get("altitude", "")),
                    "density": str(bean.get("density", "")),
                    "processing_method": str(bean.get("processing_method", "")),
                    "harvest_season": str(bean.get("harvest_season", "")),
                    "variety": str(bean.get("variety", "")),
                    "sold_out": bool(bean.get("sold_out", False))
                }
                
                cleaned_beans.append(cleaned_bean)
            
            if cleaned_beans:  # Only add pages with data
                cleaned.append({
                    "page": page_num,
                    "coffee_beans": cleaned_beans
                })
        
        return cleaned
    
    def save_to_json(self, results: List[Dict[str, Any]], output_path: str):
        """Save results to JSON file."""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            print(f"\nResults saved to: {output_path}")
        except Exception as e:
            print(f"Error saving JSON file: {e}")
    
    def print_summary(self, results: List[Dict[str, Any]]):
        """Print analysis summary."""
        total_pages = len(results)
        total_coffees = sum(len(page["coffee_beans"]) for page in results)
        
        print("\n" + "=" * 50)
        print("Analysis Summary:")
        print(f"Total processed pages: {total_pages}")
        print(f"Total extracted coffee beans: {total_coffees}")
        print("=" * 50)
        
        # Print statistics by page
        for page in results:
            page_num = page["page"]
            count = len(page["coffee_beans"])
            print(f"Page {page_num}: {count} coffee beans")


def process_text_file(input_path: str, output_path: str, analyzer: CoffeeBeanTextAnalyzer, streaming: bool = False):
    """
    Process a text file and convert it to JSON using DeepSeek API.
    
    Args:
        input_path (str): Path to input text file
        output_path (str): Path to output JSON file
        analyzer (CoffeeBeanTextAnalyzer): Analyzer instance
        streaming (bool): Whether to use streaming API
    """
    print(f"Processing: {input_path}")
    
    # Read the text file
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            text_content = f.read()
    except Exception as e:
        print(f"Error reading file {input_path}: {e}")
        return
    
    # Analyze text with DeepSeek API
    if streaming:
        results = analyzer.analyze_text_streaming(text_content)
    else:
        results = analyzer.analyze_text(text_content)
    
    if results is not None and len(results) > 0:
        # Print summary
        analyzer.print_summary(results)
        
        # Save to JSON file
        analyzer.save_to_json(results, output_path)
    else:
        print(f"No data extracted or error occurred: {input_path}")


def process_multiple_files(input_paths: List[str], output_dir: str, analyzer: CoffeeBeanTextAnalyzer, streaming: bool = False):
    """
    Process multiple text files.
    
    Args:
        input_paths (List[str]): List of input text file paths
        output_dir (str): Directory to save output JSON files
        analyzer (CoffeeBeanTextAnalyzer): Analyzer instance
        streaming (bool): Whether to use streaming API
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    for input_path in input_paths:
        if os.path.isfile(input_path) and input_path.lower().endswith('.txt'):
            # Generate output filename
            input_filename = Path(input_path).stem
            output_filename = input_filename + ".json"
            output_path = os.path.join(output_dir, output_filename)
            
            # Process the file
            process_text_file(input_path, output_path, analyzer, streaming)
        else:
            print(f"Skipping {input_path} (not a text file)")


def main():
    """Main function to parse arguments and process text files."""
    parser = argparse.ArgumentParser(
        description="Parse text files containing coffee bean information using DeepSeek API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python text_llm_parser.py input.txt -o output_folder
  python text_llm_parser.py *.txt -o parsed_data
        """
    )
    
    parser.add_argument(
        'input_files',
        nargs='+',
        help='Input text files to process'
    )
    
    parser.add_argument(
        '-o', '--output-dir',
        default='silver_data',
        help='Output directory for JSON files (default: silver_data)'
    )
    
    parser.add_argument(
        '--api-key',
        default='sk-de6d5dde9d384de294c14637d1018de2',
        help='DeepSeek API key'
    )
    
    parser.add_argument(
        '--streaming',
        action='store_true',
        help='Use streaming API (default: False)'
    )
    
    parser.add_argument(
        '--temperature',
        type=float,
        default=0.1,
        help='Temperature for LLM creativity (default: 0.1)'
    )
    
    args = parser.parse_args()
    
    # Create analyzer instance
    analyzer = CoffeeBeanTextAnalyzer(api_key=args.api_key)
    
    # Process the text files
    process_multiple_files(args.input_files, args.output_dir, analyzer, args.streaming)


if __name__ == "__main__":
    main()