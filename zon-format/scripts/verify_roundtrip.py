#!/usr/bin/env python3
"""
Verify Roundtrip

Port of verify_roundtrip.ts from the TypeScript implementation.
Verifies that all example files can be encoded to ZON and decoded back to their original form.
"""
import os
import sys
import json

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

import zon

EXAMPLES_DIR = os.path.join(os.path.dirname(__file__), '..', 'examples')


def sort_keys(obj):
    """Recursively sort keys in dictionaries for comparison."""
    if isinstance(obj, list):
        return [sort_keys(item) for item in obj]
    elif isinstance(obj, dict):
        return {k: sort_keys(v) for k, v in sorted(obj.items())}
    return obj


def main():
    print(f"Verifying roundtrip for examples in {EXAMPLES_DIR}...\n")

    if not os.path.exists(EXAMPLES_DIR):
        print(f"Examples directory not found. Run generate_examples.py first.")
        sys.exit(1)

    files = [f for f in os.listdir(EXAMPLES_DIR) if f.endswith('.json')]
    
    passed = 0
    failed = 0

    for file in files:
        json_path = os.path.join(EXAMPLES_DIR, file)
        
        with open(json_path, 'r') as f:
            original_json = json.load(f)
        
        try:
            # 1. Encode original JSON -> ZON
            encoded_zon = zon.encode(original_json)
            
            # 2. Decode ZON -> JSON
            decoded_json = zon.decode(encoded_zon)
            
            # 3. Compare (ignoring key order)
            sorted_original = sort_keys(original_json)
            sorted_decoded = sort_keys(decoded_json)
            
            if sorted_decoded == sorted_original:
                print(f"✅ {file}: Roundtrip successful")
                passed += 1
            else:
                print(f"❌ {file}: Roundtrip FAILED - Data mismatch")
                failed += 1
                
        except Exception as e:
            print(f"❌ {file}: Roundtrip FAILED")
            print(f"   Error: {e}")
            failed += 1

    print(f"\nResults: {passed} passed, {failed} failed")

    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
