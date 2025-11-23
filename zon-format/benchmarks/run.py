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

DATA_DIR = "benchmarks/data"
DATASETS = ["github-repos.json", "employees.json", "analytics.json", "orders.json", "complex_nested.json"]

def load_dataset(filename):
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
        print(f"Warning: {filename} not found. Skipping.")
        return None
    with open(path, "r") as f:
        return json.load(f)

def run_benchmark():
    print(f"{'Dataset':<20} | {'JSON':<10} | {'ZON':<10} | {'TOON':<10} | {'ZON vs JSON':<12} | {'ZON vs TOON':<12}")
    print("-" * 90)
    
    for filename in DATASETS:
        data = load_dataset(filename)
        if data is None:
            continue
            
        # Extract list if wrapped in dict
        if isinstance(data, dict):
            # Find the first value that is a list
            found_list = False
            for k, v in data.items():
                if isinstance(v, list):
                    data = v
                    found_list = True
                    break
            if not found_list:
                print(f"Skipping {filename}: Could not find list in dict.")
                continue
        
        # JSON
        start = time.time()
        json_str = json.dumps(data)
        json_time = time.time() - start
        json_size = len(json_str)
        
        # ZON
        start = time.time()
        zon_str = zon.encode(data)
        zon_time = time.time() - start
        zon_size = len(zon_str)
        
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
        zon_vs_json = (1 - zon_size/json_size) * 100
        
        if toon_size > 0:
            zon_vs_toon = (1 - zon_size/toon_size) * 100
            toon_display = f"{toon_size}"
            zvt_display = f"{zon_vs_toon:.1f}%"
        elif toon_size == -1:
            toon_display = "ERR"
            zvt_display = "N/A"
        else:
            toon_display = "N/A"
            zvt_display = "N/A"
            
        print(f"{filename:<20} | {json_size:<10} | {zon_size:<10} | {toon_display:<10} | {zon_vs_json:.1f}%       | {zvt_display:<12}")

if __name__ == "__main__":
    run_benchmark()
