import os
import sys
import json
import difflib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
import zon

TS_EXPORT_DIR = "/Users/roni/Developer/ZON/ZON-TS/benchmarks/data_export"

def verify_roundtrip(filename):
    """Verify roundtrip encoding/decoding for a dataset.
    
    Args:
        filename: Name of the file to verify.
        
    Returns:
        True if roundtrip successful, False otherwise.
    """
    name = filename.replace('.json', '')
    json_path = os.path.join(TS_EXPORT_DIR, filename)

    with open(json_path, 'r', encoding='utf-8') as f:
        original_data = json.load(f)

    try:
        zon_str = zon.encode(original_data)
        
        decoded_data = zon.decode(zon_str)
        
        orig_json = json.dumps(original_data, sort_keys=True, ensure_ascii=False, indent=2)
        decoded_json = json.dumps(decoded_data, sort_keys=True, ensure_ascii=False, indent=2)

        if orig_json == decoded_json:
            print(f"✅ {name} round-trip successful")
            return True
        else:
            print(f"❌ {name} round-trip failed")
            
            print(f"❌ {name} round-trip failed")
            
            orig_lines = orig_json.splitlines()
            decoded_lines = decoded_json.splitlines()
            
            for i, (l1, l2) in enumerate(zip(orig_lines, decoded_lines)):
                if l1 != l2:
                    print(f"Difference at line {i+1}:")
                    print(f"Original: {l1}")
                    print(f"Decoded:  {l2}")
                    break
            else:
                if len(orig_lines) != len(decoded_lines):
                    print(f"Difference in line count: Original={len(orig_lines)}, Decoded={len(decoded_lines)}")

            return False

    except Exception as e:
        print(f"❌ {name} failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    if not os.path.exists(TS_EXPORT_DIR):
        print(f"Error: {TS_EXPORT_DIR} does not exist. Run export_datasets.js first.")
        sys.exit(1)

    files = sorted([f for f in os.listdir(TS_EXPORT_DIR) if f.endswith('.json')])
    
    all_match = True
    for f in files:
        if not verify_roundtrip(f):
            all_match = False
            
    if all_match:
        print("\n🎉 All benchmark datasets passed round-trip verification!")
        sys.exit(0)
    else:
        print("\nFound round-trip failures.")
        sys.exit(1)

if __name__ == "__main__":
    main()
