#!/usr/bin/env python3
"""
Validation script for comparing LLM output JSON files with ground truth JSON files.
This script compares coffee bean entries in the LLM output JSON file to the ground truth.
"""

import json
import argparse
from typing import Dict, List, Any, Tuple


def load_json_file(file_path: str) -> Any:
    """Load and parse a JSON file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: File not found - {file_path}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in file {file_path} - {e}")
        return None


def flatten_coffee_beans(json_data: List[Dict]) -> Dict[str, Dict]:
    """
    Flatten the coffee beans data from the JSON structure into a dictionary
    keyed by the coffee bean code for easy comparison.
    """
    flattened = {}
    
    # The JSON structure is an array of page objects
    for page_obj in json_data:
        if 'coffee_beans' in page_obj:
            for bean in page_obj['coffee_beans']:
                if 'code' in bean:
                    flattened[bean['code']] = bean
    
    return flattened


def compare_fields(ground_truth: Dict, llm_output: Dict, fields: List[str]) -> Dict[str, Tuple[Any, Any, bool]]:
    """
    Compare specific fields between ground truth and LLM output.
    Returns a dictionary with field name as key and (expected, actual, match) as value.
    """
    comparisons = {}
    
    for field in fields:
        expected = ground_truth.get(field)
        actual = llm_output.get(field)
        
        # Handle special cases for comparison
        match = compare_values(expected, actual)
        comparisons[field] = (expected, actual, match)
    
    return comparisons


def compare_values(expected: Any, actual: Any) -> bool:
    """Compare two values, handling special cases like floats and None values."""
    # If both are None or both are empty strings, consider them equal
    if (expected is None or expected == "") and (actual is None or actual == ""):
        return True
    
    # For numeric values, allow small differences due to floating point precision
    if isinstance(expected, (int, float)) and isinstance(actual, (int, float)):
        return abs(float(expected) - float(actual)) < 0.001
    
    # For strings, convert to string and normalize for comparison
    expected_str = str(expected)
    actual_str = str(actual)
    
    import re
    # Normalize: remove leading/trailing spaces and collapse multiple spaces
    expected_normalized = re.sub(r'\s+', ' ', expected_str.strip())
    actual_normalized = re.sub(r'\s+', ' ', actual_str.strip())
    
    # Remove all punctuation marks (both English and Chinese) and extra whitespace for comparison
    # This includes common punctuation: .,;:!?()[]{}-/ and Chinese equivalents
    # Also includes various Unicode dash characters: - ‒ – — ―
    expected_normalized = re.sub(r'[\s"\',.;:!?()\[\]{}\-‒–—―\/、。，；：！？（）【】《》〈〉「」]+', '', expected_normalized).lower()
    actual_normalized = re.sub(r'[\s"\',.;:!?()\[\]{}\-‒–—―\/、。，；：！？（）【】《》〈〉「」]+', '', actual_normalized).lower()
    
    return expected_normalized == actual_normalized


def calculate_accuracy(match_results: List[Dict]) -> float:
    """Calculate overall accuracy based on field matches."""
    total_fields = 0
    matched_fields = 0
    
    for result in match_results:
        for field_comparison in result['field_comparisons'].values():
            total_fields += 1
            if field_comparison[2]:  # if match is True
                matched_fields += 1
    
    return (matched_fields / total_fields * 100) if total_fields > 0 else 0


def validate_coffee_beans(ground_truth_file: str, llm_output_file: str) -> None:
    """Main validation function."""
    # Load both JSON files
    ground_truth_data = load_json_file(ground_truth_file)
    if ground_truth_data is None:
        return
    
    llm_output_data = load_json_file(llm_output_file)
    if llm_output_data is None:
        return
    
    # Flatten the data for easier comparison
    ground_truth_beans = flatten_coffee_beans(ground_truth_data)
    llm_output_beans = flatten_coffee_beans(llm_output_data)
    
    # Define the fields to compare
    fields_to_compare = [
        'code', 'name', 'country', 'flavor_profile', 'price_per_kg', 'price_per_pkg',
        'origin', 'grade', 'humidity', 'altitude', 'density', 'processing_method',
        'harvest_season', 'variety'
    ]
    
    # Track comparison results
    match_results = []
    missing_in_llm = []
    extra_in_llm = []
    
    # Compare each coffee bean in ground truth
    for code, ground_truth_bean in ground_truth_beans.items():
        if code in llm_output_beans:
            llm_bean = llm_output_beans[code]
            field_comparisons = compare_fields(ground_truth_bean, llm_bean, fields_to_compare)
            
            # Count matches
            matches = sum(1 for _, _, match in field_comparisons.values() if match)
            total = len(field_comparisons)
            
            match_results.append({
                'code': code,
                'matches': matches,
                'total': total,
                'accuracy': (matches / total * 100) if total > 0 else 0,
                'field_comparisons': field_comparisons
            })
        else:
            missing_in_llm.append(code)
    
    # Find beans in LLM output that are not in ground truth
    for code in llm_output_beans:
        if code not in ground_truth_beans:
            extra_in_llm.append(code)
    
    # Print summary
    print("=" * 80)
    print("LLM OUTPUT VALIDATION REPORT")
    print("=" * 80)
    print(f"Ground Truth File: {ground_truth_file}")
    print(f"LLM Output File: {llm_output_file}")
    print()
    
    print(f"Total Coffee Beans in Ground Truth: {len(ground_truth_beans)}")
    print(f"Total Coffee Beans in LLM Output: {len(llm_output_beans)}")
    print(f"Matching Coffee Beans: {len(match_results)}")
    print(f"Missing in LLM Output: {len(missing_in_llm)}")
    print(f"Extra in LLM Output: {len(extra_in_llm)}")
    print()
    
    # Calculate overall accuracy
    overall_accuracy = calculate_accuracy(match_results)
    print(f"Overall Field Accuracy: {overall_accuracy:.2f}%")
    print()
    
    # Show missing beans
    if missing_in_llm:
        print("Missing Coffee Beans in LLM Output:")
        for code in missing_in_llm:
            print(f"  - {code}")
        print()
    
    # Show extra beans
    if extra_in_llm:
        print("Extra Coffee Beans in LLM Output:")
        for code in extra_in_llm:
            print(f"  - {code}")
        print()
    
    # Show detailed comparison for beans with mismatches
    mismatched_beans = [result for result in match_results if result['accuracy'] < 100]
    
    if mismatched_beans:
        print("Detailed Comparison for Mismatched Beans:")
        print("-" * 50)
        for result in mismatched_beans:
            print(f"Coffee Bean Code: {result['code']}")
            print(f"Accuracy: {result['accuracy']:.2f}% ({result['matches']}/{result['total']} fields match)")
            
            # Show only mismatched fields
            for field, (expected, actual, match) in result['field_comparisons'].items():
                if not match:
                    print(f"  {field}:")
                    print(f"    Expected: {expected}")
                    print(f"    Actual:   {actual}")
            print()
    
    # Summary of perfectly matched beans
    perfect_matches = [result for result in match_results if result['accuracy'] == 100]
    if perfect_matches:
        print(f"Perfectly Matched Beans ({len(perfect_matches)}):")
        for result in perfect_matches:
            print(f"  - {result['code']}")
        print()


def main():
    """Main function to parse arguments and run validation."""
    parser = argparse.ArgumentParser(description="Validate LLM output against ground truth JSON files")
    parser.add_argument("ground_truth", help="Path to the ground truth JSON file")
    parser.add_argument("llm_output", help="Path to the LLM output JSON file")
    
    args = parser.parse_args()
    
    validate_coffee_beans(args.ground_truth, args.llm_output)


if __name__ == "__main__":
    main()