#!/usr/bin/env python3
"""Comprehensive TOON Benchmark - Testing on diverse datasets"""

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

def benchmark(filepath, name, extract_key=None):
    """Run benchmark on a dataset"""
    with open(filepath, 'r') as f:
        raw = json.load(f)
    
    data = raw[extract_key] if extract_key else raw
    if not isinstance(data, list):
        print(f"Skipping {name}: Not a list")
        return None
    
    json_str = json.dumps(data, separators=(',', ':'))
    json_size = len(json_str.encode('utf-8'))
    
    zon_str = zon.encode(data)
    zon_size = len(zon_str.encode('utf-8'))
    
    toon_size = None
    if HAS_TOON:
        try:
            if hasattr(toon, 'encode'):
                toon_bytes = toon.encode(data)
            elif hasattr(toon, 'dumps'):
                toon_bytes = toon.dumps(data)
            toon_size = len(toon_bytes)
        except: pass
    
    return {
        'name': name,
        'records': len(data),
        'json': json_size,
        'zon': zon_size,
        'toon': toon_size,
        'zon_vs_json': ((json_size - zon_size) / json_size) * 100,
        'zon_vs_toon': ((toon_size - zon_size) / toon_size * 100) if toon_size else None
    }

if __name__ == '__main__':
    print("ZON v7.0 COMPREHENSIVE BENCHMARK")
    print("=" * 100)
    
    results = []
    
    # Test all datasets
    datasets = [
        ('/tmp/test_random_users.json', 'Random Users API (50)', 'results'),
        ('/tmp/test_stackoverflow.json', 'StackOverflow Q&A (50)', 'items'),
        ('/tmp/test_posts.json', 'JSONPlaceholder Posts (100)', None),
        ('/tmp/test_comments.json', 'JSONPlaceholder Comments (100)', None),
        ('/tmp/test_users.json', 'JSONPlaceholder Users (10)', None),
        ('/tmp/test_github_repos.json', 'GitHub Repos (8)', None),
    ]
    
    for filepath, name, key in datasets:
        result = benchmark(filepath, name, key)
        if result:
            results.append(result)
            zon_vs_json = result['zon_vs_json']
            zvt = f"{result['zon_vs_toon']:+.1f}%" if result['zon_vs_toon'] else "N/A"
            print(f"✓ {name:<40} | {result['records']:>4} records | ZON: {result['zon']:>6,} | vs JSON: {zon_vs_json:>5.1f}% | vs TOON: {zvt:>8}")
    
    print("\n" + "=" * 120)
    print("FINAL RESULTS")
    print("=" * 120)
    print(f"{'Dataset':<42} | {'Recs':>5} | {'JSON':>10} | {'ZON':>10} | {'TOON':>10} | {'vs JSON':>8} | {'vs TOON':>9}")
    print("-" * 120)
    
    for r in results:
        toon_str = f"{r['toon']:,}" if r['toon'] else "N/A"
        zvt_str = f"{r['zon_vs_toon']:+.1f}%" if r['zon_vs_toon'] else "N/A"
        print(f"{r['name']:<42} | {r['records']:>5} | {r['json']:>10,} | {r['zon']:>10,} | {toon_str:>10} | {r['zon_vs_json']:>7.1f}% | {zvt_str:>9}")
    
    avg_vs_json = sum(r['zon_vs_json'] for r in results) / len(results)
    valid_toon = [r for r in results if r['zon_vs_toon'] is not None]
    avg_vs_toon = sum(r['zon_vs_toon'] for r in valid_toon) / len(valid_toon) if valid_toon else 0
    
    print("-" * 120)
    print(f"{'AVERAGE':<42} | {'':<5} | {'':<10} | {'':<10} | {'':<10} | {avg_vs_json:>7.1f}% | {avg_vs_toon:>8.1f}%")
    print("=" * 120)
    
    print(f"\n🏆 ZON v7.0 beats TOON by {avg_vs_toon:.1f}% on average across {len(valid_toon)} datasets")
    print(f"📊 Average compression vs JSON: {avg_vs_json:.1f}%")
