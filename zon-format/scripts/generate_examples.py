#!/usr/bin/env python3
"""Generate example ZON files from JSON sources to match TypeScript examples."""

import json
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from zon import encode_adaptive, AdaptiveEncodeOptions


def load_json_file(filepath):
    """Load JSON from file."""
    with open(filepath, 'r') as f:
        return json.load(f)


def generate_zon_files(ts_examples_dir, py_output_dir):
    """Generate ZON files from JSON sources and compare with TS examples."""
    
    ts_dir = Path(ts_examples_dir)
    py_dir = Path(py_output_dir)
    py_dir.mkdir(parents=True, exist_ok=True)
    
    # Find all source JSON files
    source_files = sorted(ts_dir.glob("*_source.json"))
    
    results = []
    
    for source_file in source_files:
        base_name = source_file.stem.replace("_source", "")
        
        print(f"\n{'='*60}")
        print(f"Processing: {base_name}")
        print(f"{'='*60}")
        
        # Load source data
        try:
            data = load_json_file(source_file)
        except Exception as e:
            print(f"ERROR loading {source_file}: {e}")
            continue
        
        # Generate for each mode
        for mode in ['compact', 'llm', 'readable']:
            mode_name = 'llm-optimized' if mode == 'llm' else mode
            
            ts_file = ts_dir / f"{base_name}_{mode}.zonf"
            py_file = py_dir / f"{base_name}_{mode}.zonf"
            
            # Generate Python output
            try:
                if mode_name == 'llm-optimized':
                    py_output = encode_adaptive(
                        data, 
                        AdaptiveEncodeOptions(mode='llm-optimized')
                    )
                else:
                    py_output = encode_adaptive(
                        data,
                        AdaptiveEncodeOptions(mode=mode_name)
                    )
                
                # Save Python output
                with open(py_file, 'w') as f:
                    f.write(py_output)
                
                # Load TS output
                if ts_file.exists():
                    with open(ts_file, 'r') as f:
                        ts_output = f.read()
                    
                    # Compare
                    match = py_output.strip() == ts_output.strip()
                    
                    result = {
                        'file': base_name,
                        'mode': mode,
                        'match': match,
                        'py_size': len(py_output),
                        'ts_size': len(ts_output)
                    }
                    results.append(result)
                    
                    if match:
                        print(f"  ✅ {mode:12} MATCH")
                    else:
                        print(f"  ❌ {mode:12} MISMATCH")
                        print(f"     Python size: {len(py_output)} bytes")
                        print(f"     TS size: {len(ts_output)} bytes")
                        
                        # Show first difference
                        py_lines = py_output.strip().split('\n')
                        ts_lines = ts_output.strip().split('\n')
                        
                        for i, (py_line, ts_line) in enumerate(zip(py_lines, ts_lines)):
                            if py_line != ts_line:
                                print(f"     First diff at line {i+1}:")
                                print(f"       Python: {py_line[:80]}")
                                print(f"       TS:     {ts_line[:80]}")
                                break
                else:
                    print(f"  ⚠️  {mode:12} TS file not found")
                    result = {
                        'file': base_name,
                        'mode': mode,
                        'match': None,
                        'py_size': len(py_output),
                        'ts_size': 0
                    }
                    results.append(result)
                    
            except Exception as e:
                print(f"  ❌ {mode:12} ERROR: {e}")
                result = {
                    'file': base_name,
                    'mode': mode,
                    'match': False,
                    'error': str(e)
                }
                results.append(result)
    
    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    
    total = len([r for r in results if r.get('match') is not None])
    matches = len([r for r in results if r.get('match') is True])
    mismatches = len([r for r in results if r.get('match') is False])
    
    print(f"Total comparisons: {total}")
    print(f"Matches: {matches} ({matches/total*100:.1f}%)")
    print(f"Mismatches: {mismatches} ({mismatches/total*100:.1f}%)")
    
    if mismatches > 0:
        print(f"\nMismatched files:")
        for r in results:
            if r.get('match') is False:
                print(f"  - {r['file']} ({r['mode']})")
    
    return results


if __name__ == "__main__":
    ts_examples = "/tmp/ZON-TS/examples/modes"
    py_output = "/home/runner/work/ZON/ZON/zon-format/examples/modes_generated"
    
    if not Path(ts_examples).exists():
        print(f"ERROR: TS examples directory not found: {ts_examples}")
        sys.exit(1)
    
    results = generate_zon_files(ts_examples, py_output)
    
    # Exit with error code if there are mismatches
    mismatches = len([r for r in results if r.get('match') is False])
    sys.exit(1 if mismatches > 0 else 0)
