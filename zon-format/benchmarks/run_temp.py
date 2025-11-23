import time
import json
import zon
import os
import sys

# Try to import toon
try:
    import toon_python as toon
    HAS_TOON = True
except ImportError:
    try:
        import toon_format as toon
        HAS_TOON = True
    except ImportError:
        HAS_TOON = False

TEMP_DIR = "benchmarks/temp"

def load_dataset(filename):
    path = os.path.join(TEMP_DIR, filename)
    if not os.path.exists(path):
        print(f"Warning: {filename} not found. Skipping.")
        return None
    with open(path, "r") as f:
        return json.load(f)

def run_benchmark():
    if not os.path.exists(TEMP_DIR):
        print(f"Error: Directory {TEMP_DIR} does not exist.")
        return

    files = [f for f in os.listdir(TEMP_DIR) if f.endswith(".json")]
    if not files:
        print("No JSON files found in benchmarks/temp/")
        return
        
    print(f"{'Dataset':<25} | {'JSON':<10} | {'ZON':<10} | {'TOON':<10} | {'ZON vs JSON':<12} | {'ZON vs TOON':<12}")
    print("-" * 95)
    
    for filename in sorted(files):
        data = load_dataset(filename)
        if data is None:
            continue
            
        # Extract list if wrapped in dict (common in datasets)
        if isinstance(data, dict):
            # Treat as single item list to preserve entire structure
            data = [data]
        elif isinstance(data, list):
            pass
        else:
            print(f"Skipping {filename}: Data is not a list or dict.")
            continue
            
        # JSON
        start = time.time()
        json_str = json.dumps(data)
        json_time = time.time() - start
        json_size = len(json_str)
        
        # ZON
        start = time.time()
        try:
            zon_str = zon.encode(data)
            zon_time = time.time() - start
            zon_size = len(zon_str)
        except Exception as e:
            print(f"ZON Error on {filename}: {e}")
            zon_size = -1
        
        # TOON
        toon_size = 0
        toon_time = 0
        if HAS_TOON:
            try:
                start = time.time()
                if hasattr(toon, 'encode'):
                    toon_str = toon.encode(data)
                    toon_time = time.time() - start
                    toon_size = len(toon_str)
                elif hasattr(toon, 'dumps'):
                    toon_str = toon.dumps(data)
                    toon_time = time.time() - start
                    toon_size = len(toon_str)
            except Exception:
                toon_size = -1 # Error
        
        # Metrics
        if zon_size > 0:
            zon_vs_json = (1 - zon_size/json_size) * 100
            zvj_display = f"{zon_vs_json:.1f}%"
        else:
            zvj_display = "ERR"
            
        if toon_size > 0 and zon_size > 0:
            zon_vs_toon = (1 - zon_size/toon_size) * 100
            toon_display = f"{toon_size}"
            zvt_display = f"{zon_vs_toon:.1f}%"
        elif toon_size == -1:
            toon_display = "ERR"
            zvt_display = "N/A"
        else:
            toon_display = "N/A"
            zvt_display = "N/A"
            
        print(f"{filename:<25} | {json_size:<10} | {zon_size:<10} | {toon_display:<10} | {zvj_display:<12} | {zvt_display:<12}")

if __name__ == "__main__":
    run_benchmark()
