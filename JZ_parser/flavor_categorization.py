#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Flavor Categorization with DeepSeek API

This script categorizes coffee bean flavor profiles into simplified flavor categories 
using the DeepSeek API.
"""

import json
import argparse
import os
import requests
from requests.exceptions import Timeout
from typing import List, Dict, Any
from pathlib import Path


class FlavorCategorizer:
    
    def __init__(self, api_key: str, model: str = "deepseek-chat"):
        self.api_key = api_key
        self.model = model
        self.api_url = "https://api.deepseek.com/v1/chat/completions"
        
    def load_flavor_categories(self, categories_path: str = "flavor_cateogy.json") -> List[Dict[str, str]]:
        """Load flavor categories from JSON file."""
        try:
            with open(categories_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading flavor categories: {e}")
            return []
    
    def create_prompt(self, flavor_profiles: List[Dict[str, str]], flavor_categories: List[Dict[str, str]]) -> str:
        """Create a prompt for categorizing flavor profiles."""
        prompt = f"""
Please map the detailed coffee bean flavor descriptions (as a JSON array in the <flavor_profiles> section) 
into simplified flavor categories. There are 8 categories with brief descriptions provided in the <flavor_category> section.
When there are multiple flavors in the flavor_profiles, take the first 3 as the higher priority to categorize.

You should return a JSON array like follows:
[
   {{"code": "xxx", "flavor_profile": "original text", "flavor_category": "mapped category from 8"}},
   ...
]

<flavor_profiles>
```json
{json.dumps(flavor_profiles, ensure_ascii=False, indent=2)}
```
</flavor_profiles>

<flavor_category>
{json.dumps(flavor_categories, ensure_ascii=False, indent=2)}
</flavor_category>

Important instructions:
1. Process each flavor profile and map it to exactly one of the 8 flavor categories
2. Return ONLY valid JSON, no other text
3. Preserve the original code and flavor_profile fields exactly as provided
4. Add the flavor_category field with the mapped category name
5. If a flavor profile cannot be clearly mapped, use "未分类" as the category
"""
        return prompt
    
    def _prepare_analysis(self, flavor_profiles: List[Dict[str, str]], flavor_categories: List[Dict[str, str]], 
                         temperature: float, streaming: bool) -> tuple:
        """Prepare analysis with DeepSeek API."""
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
                    "content": self.create_prompt(flavor_profiles, flavor_categories)
                }
            ],
            "stream": streaming,
            "temperature": temperature,
            "max_tokens": 8100
        }
        
        return headers, payload
    
    def categorize_flavors(self, flavor_profiles: List[Dict[str, str]], 
                          flavor_categories: List[Dict[str, str]], 
                          temperature: float = 0.1) -> List[Dict[str, str]]:
        """Categorize flavor profiles using DeepSeek API without streaming."""
        # Prepare analysis
        headers, payload = self._prepare_analysis(flavor_profiles, flavor_categories, temperature, False)
        
        print("Starting flavor categorization...")
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
            print("Request timed out (10 minutes).")
            return []
        except Exception as e:
            print(f"Error during analysis: {e}")
            return []
    
    def _process_response_content(self, content: str) -> List[Dict[str, str]]:
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
                    
                # Validate result is a list
                if isinstance(result, list):
                    return result
                else:
                    print("Warning: Expected list type result")
                    return []
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
    
    def save_to_json(self, results: List[Dict[str, str]], output_path: str):
        """Save results to JSON file."""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            print(f"\nResults saved to: {output_path}")
        except Exception as e:
            print(f"Error saving JSON file: {e}")


def extract_flavor_profiles_from_json(json_files: List[str]) -> List[Dict[str, str]]:
    """
    Extract flavor profiles from JSON files.
    
    Args:
        json_files: List of JSON file paths
        
    Returns:
        List of dictionaries with 'code' and 'flavor_profile' keys
    """
    flavor_profiles = []
    
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Extract flavor profiles from the JSON structure
            for page_data in data:
                coffee_beans = page_data.get("coffee_beans", [])
                for bean in coffee_beans:
                    code = bean.get("code", "")
                    flavor_profile = bean.get("flavor_profile", "")
                    if code and flavor_profile:
                        flavor_profiles.append({
                            "code": code,
                            "flavor_profile": flavor_profile
                        })
        except Exception as e:
            print(f"Error reading file {json_file}: {e}")
    
    return flavor_profiles


def update_json_files_with_categories(json_files: List[str], categorized_flavors: List[Dict[str, str]]):
    """
    Update original JSON files with flavor categories.
    
    Args:
        json_files: List of JSON file paths to update
        categorized_flavors: List of categorized flavors with 'code', 'flavor_profile', and 'flavor_category'
    """
    # Create a mapping from code to flavor category
    code_to_category = {item["code"]: item["flavor_category"] for item in categorized_flavors}
    
    for json_file in json_files:
        try:
            # Read the original file
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Update each coffee bean with its flavor category
            for page_data in data:
                coffee_beans = page_data.get("coffee_beans", [])
                for bean in coffee_beans:
                    code = bean.get("code", "")
                    if code in code_to_category:
                        bean["flavor_category"] = code_to_category[code]
            
            # Save the updated file
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            print(f"Updated {json_file} with flavor categories")
        except Exception as e:
            print(f"Error updating file {json_file}: {e}")


def process_json_files(input_files: List[str], output_folder: str, categorizer: FlavorCategorizer):
    """
    Process JSON files and categorize flavor profiles.
    
    Args:
        input_files: List of input JSON file paths
        output_folder: Output folder path for categorized files
        categorizer: FlavorCategorizer instance
    """
    # Load flavor categories
    flavor_categories = categorizer.load_flavor_categories()
    if not flavor_categories:
        print("Failed to load flavor categories")
        return
    
    # Create output folder if it doesn't exist
    Path(output_folder).mkdir(parents=True, exist_ok=True)
    
    for input_file in input_files:
        print(f"Processing {input_file}...")
        # Extract flavor profiles from the current JSON file
        flavor_profiles = extract_flavor_profiles_from_json([input_file])
        
        if not flavor_profiles:
            print(f"No flavor profiles found in {input_file}")
            continue
        
        print(f"Found {len(flavor_profiles)} flavor profiles in {input_file}")
        
        # Categorize flavors using LLM
        categorized_flavors = categorizer.categorize_flavors(flavor_profiles, flavor_categories)
        
        if categorized_flavors:
            # Generate output filename with the specified pattern
            input_path = Path(input_file)
            output_filename = f"{input_path.stem}_flavor.json"
            output_path = Path(output_folder) / output_filename
            
            # Save categorized flavors to output file
            categorizer.save_to_json(categorized_flavors, str(output_path))
            
            # Update original JSON file with flavor categories
            update_json_files_with_categories([input_file], categorized_flavors)
        else:
            print(f"No categorized flavors returned for {input_file}")


def main():
    """Main function to parse arguments and process JSON files."""
    parser = argparse.ArgumentParser(
        description="Categorize coffee bean flavor profiles using DeepSeek API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python flavor_categorization.py ground/*.json
  python flavor_categorization.py gold/*.json
        """
    )
    
    parser.add_argument(
        'input_files',
        nargs='+',
        help='Input JSON files to process'
    )
    

    
    parser.add_argument(
        '-o', '--output-folder',
        default='.',
        help='Output folder for categorized files (default: current directory)'
    )
    
    parser.add_argument(
        '--api-key',
        default='sk-de6d5dde9d384de294c14637d1018de2',
        help='DeepSeek API key'
    )
    
    parser.add_argument(
        '--temperature',
        type=float,
        default=0.1,
        help='Temperature for LLM creativity (default: 0.1)'
    )
    
    args = parser.parse_args()
    
    # Create categorizer instance
    categorizer = FlavorCategorizer(api_key=args.api_key)
    
    # Process the JSON files
    process_json_files(args.input_files, args.output_folder, categorizer)


if __name__ == "__main__":
    main()