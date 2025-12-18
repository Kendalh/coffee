#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script to verify chunking fix
"""

from pdf_extractor import split_text_by_coffee_beans, count_coffee_beans

# Create test text with more than 100 coffee beans
test_text = ""
for i in range(150):
    test_text += f"==========\nS{i+1} Coffee bean {i+1}\nSome description\n\n"

print(f"Total beans in test text: {count_coffee_beans(test_text)}")

# Split into chunks
chunks = split_text_by_coffee_beans(test_text, 100)
print(f"Number of chunks: {len(chunks)}")

# Check each chunk
for i, chunk in enumerate(chunks):
    bean_count = count_coffee_beans(chunk)
    print(f"Chunk {i+1}: {bean_count} beans")
    
    # Check if chunk starts with separator
    starts_with_separator = chunk.startswith("==========\n")
    print(f"  Chunk starts with separator: {starts_with_separator}")
    
    # Show first few characters of chunk for debugging
    if i == 0:
        print(f"  First 30 chars: {repr(chunk[:30])}")