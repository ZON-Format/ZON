#!/usr/bin/env python3
"""
Nested Structure Verification - Checks that nested objects are preserved correctly
Focuses on structure integrity rather than strict equality (tolerates key ordering and numeric equivalence).
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
import zon


def values_equivalent(original, decoded):
    """Check if two values are equivalent, allowing int/float equivalence.
    
    Args:
        original: Original value.
        decoded: Decoded value.
        
    Returns:
        True if values are equivalent.
    """
    if type(original) == type(decoded):
        return original == decoded
    
    if isinstance(original, (int, float)) and isinstance(decoded, (int, float)):
        return float(original) == float(decoded)
    
    return False


def check_nested_structure(original, decoded, path='root', allow_numeric_equivalence=True):
    """Recursively check that nested structures match.
    
    Tolerates:
    - Key ordering differences in dicts
    - Int/float equivalence (127.0 == 127)
    
    Args:
        original: Original data.
        decoded: Decoded data.
        path: Current path in the structure.
        allow_numeric_equivalence: Whether to allow int/float equivalence.
        
    Returns:
        True if structures match.
    """
    if allow_numeric_equivalence and isinstance(original, (int, float)) and isinstance(decoded, (int, float)):
        if not values_equivalent(original, decoded):
            print(f"  ❌ Numeric value mismatch at {path}: {original!r} != {decoded!r}")
            return False
        return True
    
    if type(original) != type(decoded):
        if not (isinstance(original, (int, float)) and isinstance(decoded, (int, float))):
            print(f"  ❌ Type mismatch at {path}: {type(original).__name__} != {type(decoded).__name__}")
            return False
    
    if isinstance(original, dict):
        orig_keys = set(original.keys())
        dec_keys = set(decoded.keys())
        
        if orig_keys != dec_keys:
            missing = orig_keys - dec_keys
            extra = dec_keys - orig_keys
            if missing:
                print(f"  ❌ Missing keys at {path}: {missing}")
            if extra:
                print(f"  ❌ Extra keys at {path}: {extra}")
            return False
        
        for key in original:
            if not check_nested_structure(original[key], decoded[key], f"{path}.{key}", allow_numeric_equivalence):
                return False
                
    elif isinstance(original, list):
        if len(original) != len(decoded):
            print(f"  ❌ List length mismatch at {path}: {len(original)} != {len(decoded)}")
            return False
        
        for i, (orig_item, dec_item) in enumerate(zip(original, decoded)):
            if not check_nested_structure(orig_item, dec_item, f"{path}[{i}]", allow_numeric_equivalence):
                return False
                
    else:
        if not values_equivalent(original, decoded):
            print(f"  ❌ Value mismatch at {path}:")
            print(f"     Original: {original!r} ({type(original).__name__})")
            print(f"     Decoded:  {decoded!r} ({type(decoded).__name__})")
            return False
    
    return True


def verify_dataset(filepath):
    """Verify a single dataset.
    
    Args:
        filepath: Path to the dataset file.
        
    Returns:
        True if verification passed.
    """
    print(f"\n{'='*80}")
    print(f"Testing: {filepath.stem}")
    print('='*80)
    
    with open(filepath) as f:
        original = json.load(f)
    
    encoded = zon.encode(original)
    decoded = zon.decode(encoded)
    
    print("\n🔍 Verifying nested structure preservation...")
    if check_nested_structure(original, decoded):
        print("  ✅ NESTED STRUCTURE: PERFECT (with numeric tolerance)")
        return True
    else:
        print("  ❌ NESTED STRUCTURE: HAS ISSUES")
        return False


def main():
    """Run verification on all datasets."""
    data_dir = Path(__file__).parent / 'data'
    
    print("\n" + "█"*80)
    print("  NESTED STRUCTURE VERIFICATION")
    print("  Checks that nested objects/arrays are preserved correctly")
    print("  Allows int/float equivalence (127.0 == 127)")
    print("█"*80)
    
    datasets = sorted(data_dir.glob('*.json'))
    
    results = []
    for dataset in datasets:
        if dataset.name.startswith('internet_'):
            continue
        passed = verify_dataset(dataset)
        results.append((dataset.stem, passed))
    
    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    
    passed_count = sum(1 for _, p in results if p)
    total = len(results)
    
    for name, passed in results:
        icon = "✅" if passed else "❌"
        print(f"{icon} {name}")
    
    print(f"\n{passed_count}/{total} datasets passed nested structure verification")
    
    if passed_count == total:
        print("\n✅ ALL NESTED STRUCTURES PRESERVED PERFECTLY!")
    else:
        print(f"\n⚠️  {total - passed_count} dataset(s) have nested structure issues")


if __name__ == '__main__':
    main()
