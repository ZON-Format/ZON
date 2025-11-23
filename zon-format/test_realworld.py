#!/usr/bin/env python3
"""Test ZON v7.0 on real-world JSON data from the internet"""

import json
import sys
sys.path.insert(0, 'src')

import zon

try:
    import toon_python as toon
    HAS_TOON = True
except ImportError:
    try:
        import toon_format as toon
        HAS_TOON = True
    except ImportError:
        HAS_TOON = False
        print("Warning: TOON not available, skipping TOON benchmarks")

def test_json_file(filepath, name):
    """Test compression on a JSON file"""
    print(f"\n{'='*70}")
    print(f"Testing: {name}")
    print(f"{'='*70}")
    
    # Load JSON
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    # Get JSON size
    json_str = json.dumps(data, separators=(',', ':'))
    json_size = len(json_str.encode('utf-8'))
    
    # Encode with ZON
    zon_str = zon.encode(data)
    zon_size = len(zon_str.encode('utf-8'))
    
    # Encode with TOON (if available)
    toon_size = None
    if HAS_TOON:
        try:
            if hasattr(toon, 'encode'):
                toon_bytes = toon.encode(data)
            elif hasattr(toon, 'dumps'):
                toon_bytes = toon.dumps(data)
            else:
                raise AttributeError("TOON has no encode or dumps method")
            toon_size = len(toon_bytes)
        except Exception as e:
            print(f"TOON encoding failed: {e}")
    
    # Calculate compression
    zon_reduction = ((json_size - zon_size) / json_size) * 100
    
    # Print results
    print(f"Number of records: {len(data)}")
    print(f"JSON size: {json_size:,} bytes")
    print(f"ZON v7.0 size: {zon_size:,} bytes ({zon_reduction:.1f}% compression)")
    
    if toon_size:
        toon_reduction = ((json_size - toon_size) / json_size) * 100
        vs_toon = ((toon_size - zon_size) / toon_size) * 100
        print(f"TOON size: {toon_size:,} bytes ({toon_reduction:.1f}% compression)")
        print(f"ZON vs TOON: {vs_toon:+.1f}%")
    
    # Show sample of ZON output
    lines = zon_str.split('\n')
    print(f"\nZON Output (first 3 lines):")
    for i, line in enumerate(lines[:3], 1):
        preview = line[:80] + '...' if len(line) > 80 else line
        print(f"  {i}: {preview}")
    
    return {
        'name': name,
        'records': len(data),
        'json_size': json_size,
        'zon_size': zon_size,
        'toon_size': toon_size,
        'zon_reduction': zon_reduction
    }

if __name__ == '__main__':
    results = []
    
    # Test JSONPlaceholder Users
    results.append(test_json_file('/tmp/test_users.json', 'JSONPlaceholder Users'))
    
    # Test GitHub Repos
    results.append(test_json_file('/tmp/test_github_repos.json', 'GitHub Repos'))
    
    # Summary
    print(f"\n{'='*80}")
    print("SUMMARY - Real-World JSON Compression")
    print(f"{'='*80}")
    
    if HAS_TOON:
        print(f"{'Dataset':<25} | {'Records':>8} | {'JSON':>10} | {'ZON':>10} | {'TOON':>10} | {'vs TOON':>10}")
        print("-" * 80)
        for r in results:
            vs_toon = ((r['toon_size'] - r['zon_size']) / r['toon_size'] * 100) if r['toon_size'] else 0
            print(f"{r['name']:<25} | {r['records']:>8} | {r['json_size']:>10,} | {r['zon_size']:>10,} | {r['toon_size']:>10,} | {vs_toon:>9.1f}%")
    else:
        print(f"{'Dataset':<25} | {'Records':>8} | {'JSON':>10} | {'ZON':>10} | {'Reduction':>10}")
        print("-" * 80)
        for r in results:
            print(f"{r['name']:<25} | {r['records']:>8} | {r['json_size']:>10,} | {r['zon_size']:>10,} | {r['zon_reduction']:>9.1f}%")
    
    avg_zon = sum(r['zon_reduction'] for r in results) / len(results)
    print("-" * 80)
    print(f"Average ZON Compression: {avg_zon:.1f}%")

