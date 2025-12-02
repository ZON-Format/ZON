import os
import json
import sys
import unittest

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

import zon

EXAMPLES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../examples'))

print(f"Verifying roundtrip for examples in {EXAMPLES_DIR}...\n")

if not os.path.exists(EXAMPLES_DIR):
    print(f"Examples directory {EXAMPLES_DIR} does not exist. Run generate_examples.py first.")
    sys.exit(1)

files = [f for f in os.listdir(EXAMPLES_DIR) if f.endswith('.json')]
files.sort()

passed = 0
failed = 0

def sort_keys(obj):
    """Recursively sort dictionary keys.
    
    Args:
        obj: Object to sort.
        
    Returns:
        Sorted object.
    """
    if isinstance(obj, list):
        return [sort_keys(i) for i in obj]
    elif isinstance(obj, dict):
        return {k: sort_keys(v) for k, v in sorted(obj.items())}
    else:
        return obj

for file in files:
    json_path = os.path.join(EXAMPLES_DIR, file)
    
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            original_json = json.load(f)
        
        encoded_zon = zon.encode(original_json)
        decoded_json = zon.decode(encoded_zon)
        
        sorted_original = sort_keys(original_json)
        sorted_decoded = sort_keys(decoded_json)
        
        if sorted_decoded == sorted_original:
            print(f"✅ {file}: Roundtrip successful")
            passed += 1
        else:
            print(f"❌ {file}: Roundtrip FAILED")
            print("Original:", json.dumps(sorted_original, indent=2))
            print("Decoded:", json.dumps(sorted_decoded, indent=2))
            failed += 1
            
    except Exception as e:
        print(f"❌ {file}: Roundtrip FAILED")
        print(f"Error: {e}")
        failed += 1

print(f"\nResults: {passed} passed, {failed} failed")

if failed > 0:
    sys.exit(1)
