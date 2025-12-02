#!/usr/bin/env python3
"""
Export benchmark datasets to JSON and ZON formats.

This creates parallel datasets in both formats for:
- Cross-platform verification (Python vs TypeScript)
- Size comparison
- Roundtrip testing
"""

import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

import zon

# Output directory
OUTPUT_DIR = Path(__file__).parent.parent.parent / 'benchmarks' / 'data_export'


def export_dataset(name, data):
    """Export a dataset to both JSON and ZON formats.
    
    Args:
        name: Name of the dataset.
        data: Data to export.
        
    Returns:
        Dictionary containing export statistics.
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    json_path = OUTPUT_DIR / f"{name}.json"
    with open(json_path, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    zon_str = zon.encode(data)
    zon_path = OUTPUT_DIR / f"{name}.zonf"
    with open(zon_path, 'w') as f:
        f.write(zon_str)
    
    json_size = json_path.stat().st_size
    zon_size = zon_path.stat().st_size
    compression = ((json_size - zon_size) / json_size) * 100
    
    print(f"✅ {name}")
    print(f"   JSON: {json_size:,} bytes")
    print(f"   ZON:  {zon_size:,} bytes ({compression:.1f}% compression)")
    
    return {
        'name': name,
        'json_size': json_size,
        'zon_size': zon_size,
        'compression': compression
    }


def main():
    print('=' * 80)
    print('  EXPORTING BENCHMARK DATASETS')
    print('=' * 80)
    print()
    
    data_dir = Path(__file__).parent.parent.parent / 'benchmarks' / 'data'
    
    stats = []
    
    for json_file in sorted(data_dir.glob('*.json')):
        name = json_file.stem
        
        print(f"📦 Processing: {name}...")
        
        with open(json_file) as f:
            data = json.load(f)
        
        stat = export_dataset(name, data)
        stats.append(stat)
        print()
    
    # Summary
    print('=' * 80)
    print('  SUMMARY')
    print('=' * 80)
    print()
    
    total_json = sum(s['json_size'] for s in stats)
    total_zon = sum(s['zon_size'] for s in stats)
    total_compression = ((total_json - total_zon) / total_json) * 100
    
    print(f"Datasets exported: {len(stats)}")
    print(f"Total JSON size:   {total_json:,} bytes")
    print(f"Total ZON size:    {total_zon:,} bytes")
    print(f"Overall compression: {total_compression:.1f}%")
    print()
    print(f"📁 Output directory: {OUTPUT_DIR}")
    print()
    print('✅ Export complete!')
    print('=' * 80)


if __name__ == '__main__':
    main()
