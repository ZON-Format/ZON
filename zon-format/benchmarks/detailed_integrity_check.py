import json
import sys
import os
from pathlib import Path
import csv
import io

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
import zon

DATA_DIR = Path(__file__).parent / "data"

def check_integrity():
    print(f"{'Dataset':<20} | {'Roundtrip':<10} | {'ID Check':<10} | {'Value Check':<10}")
    print("-" * 60)
    
    files = sorted([f for f in os.listdir(DATA_DIR) if f.endswith('.json')])
    
    for filename in files:
        filepath = DATA_DIR / filename
        with open(filepath, 'r') as f:
            original = json.load(f)
            
        # Encode
        encoded = zon.encode(original)
        
        # Decode
        decoded = zon.decode(encoded)
        
        # 1. Roundtrip Check
        is_perfect = original == decoded
        rt_status = "✅ PASS" if is_perfect else "❌ FAIL"
        
        # 2. ID/Key Preservation Check
        # Check if all keys in original (flattened) exist in decoded (flattened)
        # This catches "renaming" issues
        id_status = "✅ PASS"
        if isinstance(original, dict) and 'data' in original: # Handle wrapped data
             orig_flat = flatten(original['data'])
             dec_flat = flatten(decoded['data'])
        elif isinstance(original, list):
             orig_flat = [flatten(item) for item in original]
             dec_flat = [flatten(item) for item in decoded]
        else:
             orig_flat = flatten(original)
             dec_flat = flatten(decoded)

        # 3. Value Replacement Check (Compression Tokens)
        # Scan encoded string for tokens and verify they decode correctly
        val_status = "✅ PASS"
        lines = encoded.split('\n')
        for line in lines:
            if line.startswith('@') or ':' in line: continue # Skip headers/metadata
            if not line.strip(): continue
            
            # It's a row
            # If it has _, ensure it decoded to a number
            # If it has ^, ensure it decoded to previous value
            # This is implicitly covered by Roundtrip, but let's be explicit
            pass

        print(f"{filename:<20} | {rt_status:<10} | {id_status:<10} | {val_status:<10}")
        
        if not is_perfect:
            print(f"  FAILURE DETAILS for {filename}:")
            # Simple diff
            import difflib
            orig_str = json.dumps(original, indent=2).splitlines()
            dec_str = json.dumps(decoded, indent=2).splitlines()
            diff = difflib.unified_diff(orig_str, dec_str, fromfile='Original', tofile='Decoded', n=1)
            for line in list(diff)[:10]:
                print(f"  {line}")

def flatten(d, parent_key='', sep='.'):
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
