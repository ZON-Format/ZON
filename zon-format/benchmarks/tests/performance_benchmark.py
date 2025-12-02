#!/usr/bin/env python3
"""
Performance Benchmarks - Encode/Decode Speed

Measures encoding and decoding performance for ZON vs JSON.
"""

import json
import time
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

import zon

def benchmark_dataset(name, data, iterations=100):
    """Benchmark a single dataset.
    
    Args:
        name: Name of the dataset.
        data: Data to benchmark.
        iterations: Number of iterations to run.
        
    Returns:
        Dictionary containing benchmark results.
    """
    json_encode_times = []
    for _ in range(iterations):
        start = time.perf_counter()
        json_str = json.dumps(data, separators=(',', ':'))
        end = time.perf_counter()
        json_encode_times.append((end - start) * 1000)
    
    json_decode_times = []
    for _ in range(iterations):
        start = time.perf_counter()
        json.loads(json_str)
        end = time.perf_counter()
        json_decode_times.append((end - start) * 1000)
    
    zon_encode_times = []
    for _ in range(iterations):
        start = time.perf_counter()
        zon_str = zon.encode(data)
        end = time.perf_counter()
        zon_encode_times.append((end - start) * 1000)
    
    zon_decode_times = []
    for _ in range(iterations):
        start = time.perf_counter()
        zon.decode(zon_str)
        end = time.perf_counter()
        zon_decode_times.append((end - start) * 1000)
    
    avg_json_encode = sum(json_encode_times) / len(json_encode_times)
    avg_json_decode = sum(json_decode_times) / len(json_decode_times)
    avg_zon_encode = sum(zon_encode_times) / len(zon_encode_times)
    avg_zon_decode = sum(zon_decode_times) / len(zon_decode_times)
    
    return {
        'name': name,
        'json_encode_ms': avg_json_encode,
        'json_decode_ms': avg_json_decode,
        'zon_encode_ms': avg_zon_encode,
        'zon_decode_ms': avg_zon_decode,
        'json_size': len(json_str),
        'zon_size': len(zon_str) if zon_str else 0
    }


def main():
    """Run performance benchmark."""
    print('█' * 100)
    print('  ZON PERFORMANCE BENCHMARK - Encode/Decode Speed')
    print('█' * 100)
    print()
    
    datasets = {
        'Small (Hiking)': {
            'context': {
                'task': 'Our favorite hikes together',
                'location': 'Boulder',
                'season': 'spring_2025'
            },
            'friends': ['ana', 'luis', 'sam'],
            'hikes': [
                {'id': 1, 'name': 'Blue Lake Trail', 'distanceKm': 7.5, 'elevationGain': 320},
                {'id': 2, 'name': 'Ridge Overlook', 'distanceKm': 9.2, 'elevationGain': 540},
                {'id': 3, 'name': 'Wildflower Loop', 'distanceKm': 5.1, 'elevationGain': 180}
            ]
        },
        'Medium (1K Array)': {
            'items': [{'id': i, 'value': f'item-{i}', 'active': i % 2 == 0} for i in range(1000)]
        },
        'Large (10K Array)': {
            'records': [{'id': i, 'data': f'record-{i}', 'status': 'active'} for i in range(10000)]
        },
        'Nested (Deep)': {
            'level1': {
                'level2': {
                    'level3': {
                        'level4': {
                            'level5': {
                                'data': [{'id': i, 'name': f'item-{i}'} for i in range(100)]
                            }
                        }
                    }
                }
            }
        }
    }
    
    results = []
    
    for name, data in datasets.items():
        print(f'📊 Benchmarking: {name}...')
        
        iterations = 100 if 'Large' not in name else 10
        result = benchmark_dataset(name, data, iterations=iterations)
        results.append(result)
        
        print(f'   JSON: {result["json_encode_ms"]:.3f}ms encode, {result["json_decode_ms"]:.3f}ms decode')
        print(f'   ZON:  {result["zon_encode_ms"]:.3f}ms encode, {result["zon_decode_ms"]:.3f}ms decode')
        print()
    
    print('=' * 120)
    print('  PERFORMANCE SUMMARY')
    print('=' * 120)
    print()
    
    header = f"{'Dataset':<20} | {'JSON Size':>10} | {'ZON Size':>10} | {'JSON Enc':>10} | {'ZON Enc':>10} | {'JSON Dec':>10} | {'ZON Dec':>10}"
    print(header)
    print('-' * len(header))
    
    for r in results:
        json_size = f"{r['json_size']:,} B"
        zon_size = f"{r['zon_size']:,} B"
        json_enc = f"{r['json_encode_ms']:.3f} ms"
        zon_enc = f"{r['zon_encode_ms']:.3f} ms"
        json_dec = f"{r['json_decode_ms']:.3f} ms"
        zon_dec = f"{r['zon_decode_ms']:.3f} ms"
        
        print(f"{r['name']:<20} | {json_size:>10} | {zon_size:>10} | {json_enc:>10} | {zon_enc:>10} | {json_dec:>10} | {zon_dec:>10}")
    
    print()
    print('=' * 120)
    print()
    
    print('📈 ANALYSIS:')
    print()
    for r in results:
        size_reduction = ((r['json_size'] - r['zon_size']) / r['json_size']) * 100
        enc_slowdown = (r['zon_encode_ms'] / r['json_encode_ms'])
        dec_slowdown = (r['zon_decode_ms'] / r['json_decode_ms'])
        
        print(f"{r['name']}:")
        print(f"  Size Reduction: {size_reduction:.1f}% ({r['json_size']:,} → {r['zon_size']:,} bytes)")
        print(f"  Encode Speed: {enc_slowdown:.1f}x slower than JSON ({r['zon_encode_ms']:.3f}ms vs {r['json_encode_ms']:.3f}ms)")
        print(f"  Decode Speed: {dec_slowdown:.1f}x slower than JSON ({r['zon_decode_ms']:.3f}ms vs {r['json_decode_ms']:.3f}ms)")
        print()
    
    print('=' * 120)
    print('✅ Benchmark Complete!')
    print('=' * 120)


if __name__ == '__main__':
    main()
