import json
import sys
import os
from pathlib import Path
import csv
import io

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))
import zon

DATA_DIR = Path(__file__).parent.parent / "data"

def check_integrity():
    """Perform detailed integrity check on benchmark data."""
    print(f"{'Dataset':<20} | {'Roundtrip':<10} | {'ID Check':<10} | {'Value Check':<10}")
    print("-" * 60)
    
    files = sorted([f for f in os.listdir(DATA_DIR) if f.endswith('.json')])
    
    for filename in files:
        filepath = DATA_DIR / filename
        with open(filepath, 'r') as f:
            original = json.load(f)
            
        encoded = zon.encode(original)
        
        decoded = zon.decode(encoded)
        
        is_perfect = compare_with_tolerance(original, decoded)
        rt_status = "✅ PASS" if is_perfect else "❌ FAIL"
        
        id_status = "✅ PASS"
        if isinstance(original, dict) and 'data' in original:
             orig_flat = flatten(original['data'])
             dec_flat = flatten(decoded['data'])
        elif isinstance(original, list):
             orig_flat = [flatten(item) for item in original]
             dec_flat = [flatten(item) for item in decoded]
        else:
             orig_flat = flatten(original)
             dec_flat = flatten(decoded)

        val_status = "✅ PASS"
        lines = encoded.split('\n')
        for line in lines:
            if line.startswith('@') or ':' in line: continue
            if not line.strip(): continue
            
            pass

        print(f"{filename:<20} | {rt_status:<10} | {id_status:<10} | {val_status:<10}")
        
        if not is_perfect:
            print(f"  FAILURE DETAILS for {filename}:")
            import difflib
            orig_str = json.dumps(original, indent=2).splitlines()
            dec_str = json.dumps(decoded, indent=2).splitlines()
            diff = difflib.unified_diff(orig_str, dec_str, fromfile='Original', tofile='Decoded', n=1)
            for line in list(diff)[:10]:
                print(f"  {line}")

def compare_with_tolerance(obj1, obj2, tolerance=1e-9):
    """Recursively compare objects with float tolerance."""
    if type(obj1) != type(obj2):
        return False
        
    if isinstance(obj1, dict):
        if len(obj1) != len(obj2):
            return False
        for k, v in obj1.items():
            if k not in obj2:
                return False
            if not compare_with_tolerance(v, obj2[k], tolerance):
                return False
        return True
        
    if isinstance(obj1, list):
        if len(obj1) != len(obj2):
            return False
        for i in range(len(obj1)):
            if not compare_with_tolerance(obj1[i], obj2[i], tolerance):
                return False
        return True
        
    if isinstance(obj1, float):
        return abs(obj1 - obj2) <= tolerance
        
    return obj1 == obj2

def flatten(d, parent_key='', sep='.'):
    """Flatten a nested dictionary.
    
    Args:
        d: Dictionary to flatten.
        parent_key: Parent key prefix.
        sep: Separator for nested keys.
        
    Returns:
        Flattened dictionary.
    """
    items = []
    if isinstance(d, dict):
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(flatten(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
    else:
        items.append((parent_key, d))
    return dict(items)

if __name__ == "__main__":
    check_integrity()
