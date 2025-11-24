#!/usr/bin/env python3
"""
Comprehensive ZON Benchmark - Tests all 3 data types
Compares JSON, ZON, and TOON formats with beautiful visualization.

Data Types:
1. Local Data (benchmarks/data/*.json)
2. Internet Data (from public APIs)
3. MongoDB Data (irregular schemas)
"""

import sys
import json
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
import zon

# Try to import TOON for comparison
try:
    import toon
    HAS_TOON = True
except ImportError:
    HAS_TOON = False


def format_bytes(size):
    """Format bytes to human-readable."""
    for unit in ['B', 'KB', 'MB']:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} GB"


def benchmark_dataset(name, data):
    """Benchmark a single dataset."""
    # JSON baseline
    json_str = json.dumps(data)
    json_size = len(json_str)
    
    # ZON encoding
    start = time.time()
    zon_str = zon.encode(data)
    zon_time = (time.time() - start) * 1000
    zon_size = len(zon_str)
    
    # TOON encoding
    if HAS_TOON:
        start = time.time()
        toon_str = toon.dump(data)
        toon_time = (time.time() - start) * 1000
        toon_size = len(toon_str)
    else:
        toon_size = None
        toon_time = None
    
    # Verify roundtrip
    decoded = zon.decode(zon_str)
    roundtrip_ok = (decoded == data)
    
    # Calculate compression
    zon_compression = (1 - zon_size / json_size) * 100
    if toon_size:
        zon_vs_toon = ((zon_size - toon_size) / toon_size) * 100
    else:
        zon_vs_toon = None
    
    return {
        'name': name,
        'json_size': json_size,
        'zon_size': zon_size,
        'toon_size': toon_size,
        'zon_time': zon_time,
        'toon_time': toon_time,
        'zon_compression': zon_compression,
        'zon_vs_toon': zon_vs_toon,
        'roundtrip': roundtrip_ok
    }


def print_section(title):
    """Print formatted section header."""
    print("\n" + "═" * 90)
    print(f"  {title}")
    print("═" * 90)


def print_results_table(results, title):
    """Print results in a beautiful table."""
    print_section(title)
    
    print(f"\n{'Dataset':<30} | {'Records':>8} | {'JSON':>10} | {'ZON':>10} | {'Compress':>9} | {'vs TOON':>9} | {'RT':>4}")
    print("-" * 110)
    
    for r in results:
        # Count records
        if isinstance(r['data'], dict):
            # Count first list/array found
            rec_count = 0
            for v in r['data'].values():
                if isinstance(v, list):
                    rec_count = len(v)
                    break
            if rec_count == 0:
                rec_count = 1
        elif isinstance(r['data'], list):
            rec_count = len(r['data'])
        else:
            rec_count = 1
        
        rt_icon = "✅" if r['roundtrip'] else "❌"
        vs_toon = f"{r['zon_vs_toon']:+.1f}%" if r['zon_vs_toon'] is not None else "N/A"
        
        print(f"{r['name']:<30} | {rec_count:8} | {format_bytes(r['json_size']):>10} | "
              f"{format_bytes(r['zon_size']):>10} | {r['zon_compression']:8.1f}% | "
              f"{vs_toon:>9} | {rt_icon:>4}")


def main():
    """Run comprehensive benchmark."""
    data_dir = Path(__file__).parent / 'data'
    
    print("\n" + "█" * 90)
    print("  ZON COMPREHENSIVE BENCHMARK - JSON vs ZON vs TOON")
    print("█" * 90)
    
    if not HAS_TOON:
        print("\n⚠️  TOON not installed. Install with: pip install toon-format")
        print("   Comparison will show ZON vs JSON only.\n")
    
    all_results = []
    
    # ========================================
    # 1. LOCAL DATA
    # ========================================
    local_files = list(data_dir.glob('*.json'))
    local_files = [f for f in local_files if not f.name.startswith('internet_')]
    
    local_results = []
    for json_file in sorted(local_files):
        print(f"\n📁 Loading {json_file.name}...")
        with open(json_file) as f:
            data = json.load(f)
        
        result = benchmark_dataset(json_file.stem, data)
        result['data'] = data
        local_results.append(result)
        all_results.append(result)
    
    if local_results:
        print_results_table(local_results, "1. LOCAL DATA (benchmarks/data/)")
    
    # ========================================
    # 2. INTERNET DATA
    # ========================================
    internet_files = list(data_dir.glob('internet_*.json'))
    
    internet_results = []
    for json_file in sorted(internet_files):
        print(f"\n🌐 Loading {json_file.name}...")
        with open(json_file) as f:
            data = json.load(f)
        
        result = benchmark_dataset(json_file.stem.replace('internet_', ''), data)
        result['data'] = data
        internet_results.append(result)
        all_results.append(result)
    
    if internet_results:
        print_results_table(internet_results, "2. INTERNET DATA (Public APIs)")
    else:
        print_section("2. INTERNET DATA (Public APIs)")
        print("\n⚠️  No internet data found. Run: python benchmarks/fetch_internet_data.py\n")
    
    # ========================================
    # 3. MONGODB DATA
    # ========================================
    mongodb_file = data_dir / 'mongodb_irregular.json'
    
    if mongodb_file.exists():
        print(f"\n🗄️  Loading {mongodb_file.name}...")
        with open(mongodb_file) as f:
            data = json.load(f)
        
        result = benchmark_dataset('mongodb_irregular', data)
        result['data'] = data
        mongodb_results = [result]
        all_results.append(result)
        
        print_results_table(mongodb_results, "3. MONGODB DATA (Irregular Schemas)")
    
    # ========================================
    # SUMMARY
    # ========================================
    if all_results:
        print_section("📊 OVERALL SUMMARY")
        
        total_json = sum(r['json_size'] for r in all_results)
        total_zon = sum(r['zon_size'] for r in all_results)
        avg_compression = (1 - total_zon / total_json) * 100
        
        if HAS_TOON:
            total_toon = sum(r['toon_size'] for r in all_results if r['toon_size'])
            if total_toon > 0:
                avg_vs_toon = ((total_zon - total_toon) / total_toon) * 100
            else:
                avg_vs_toon = None
        else:
            avg_vs_toon = None
        
        all_passed = all(r['roundtrip'] for r in all_results)
        
        print(f"\nTotal JSON Size:  {format_bytes(total_json)}")
        print(f"Total ZON Size:   {format_bytes(total_zon)}")
        print(f"Average Compression: {avg_compression:.1f}%")
        
        if avg_vs_toon is not None:
            symbol = "+" if avg_vs_toon > 0 else ""
            print(f"ZON vs TOON: {symbol}{avg_vs_toon:.1f}%")
        
        print(f"\nRoundtrip Accuracy: {'✅ ALL PASS' if all_passed else '❌ SOME FAILED'}")
        print(f"Datasets Tested: {len(all_results)}")
        
        print("\n" + "═" * 90)
        print("  ✅ Benchmark Complete!")
        print("═" * 90 + "\n")


if __name__ == '__main__':
    main()
