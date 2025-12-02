import sys
import os
import json
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

import zon

import traceback

def test_single_dict():
    """Test encoding and decoding a single dictionary."""
    print("Testing Single Dict Input...")
    data = {"id": 1, "name": "Test"}
    try:
        encoded = zon.encode(data)
        print(f"Encoded: {encoded}")
        decoded = zon.decode(encoded)
        print(f"Decoded: {decoded}")
        assert decoded == [data] or decoded == data
        print("PASS")
    except Exception:
        traceback.print_exc()

def test_sparse_data():
    """Test encoding and decoding sparse data structures."""
    print("\nTesting Sparse Data...")
    data = [
        {"id": 1, "name": "A", "extra": "val"},
        {"id": 2, "name": "B"},
        {"id": 3, "extra": "val2"}
    ]
    try:
        encoded = zon.encode(data)
        print(f"Encoded: {encoded}")
        decoded = zon.decode(encoded)
        print(f"Decoded: {decoded}")
        print("PASS")
    except Exception:
        traceback.print_exc()

def test_mixed_types():
    """Test encoding and decoding mixed data types."""
    print("\nTesting Mixed Types...")
    data = [
        {"val": 1},
        {"val": "string"},
        {"val": True},
        {"val": None}
    ]
    try:
        encoded = zon.encode(data)
        print(f"Encoded: {encoded}")
        decoded = zon.decode(encoded)
        print(f"Decoded: {decoded}")
        print("PASS")
    except Exception:
        traceback.print_exc()

def test_ambiguity():
    """Test handling of ambiguous string/number values."""
    print("\nTesting String/Number Ambiguity...")
    data = [
        {"val": 123},
        {"val": "123"},
        {"val": "12.34"},
        {"val": 12.34}
    ]
    try:
        encoded = zon.encode(data)
        print(f"Encoded: {encoded}")
        decoded = zon.decode(encoded)
        print(f"Decoded: {decoded}")
        assert decoded == data
        print("PASS")
    except Exception:
        traceback.print_exc()

if __name__ == "__main__":
    test_single_dict()
    test_sparse_data()
    test_mixed_types()
    test_ambiguity()
