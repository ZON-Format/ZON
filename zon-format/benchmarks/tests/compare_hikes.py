#!/usr/bin/env python3
"""
Compare the hiking data example in JSON, ZON, and TOON formats.
This is the example used on TOON's website.
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))
import zon


def count_tokens(text):
    """Approximate token count (rough estimation)."""
    return len(text) // 4


def main():
    data_dir = Path(__file__).parent.parent / 'data'
    
    # Load JSON data
    with open(data_dir / 'hikes.json') as f:
        data = json.load(f)
    
    # Load TOON reference
    with open(data_dir / 'hikes.toon') as f:
        toon_str = f.read().strip()
    
    json_formatted = json.dumps(data, indent=2)
    
    json_compact = json.dumps(data, separators=(',', ':'))
    
    if hasattr(zon, "encode") and callable(zon.encode):
        zon_str = zon.encode(data)
    elif hasattr(zon, "dumps") and callable(zon.dumps):
        zon_str = zon.dumps(data)
    elif hasattr(zon, "to_zon") and callable(zon.to_zon):
        zon_str = zon.to_zon(data)
    else:
        raise AttributeError("zon module does not provide 'encode', 'dumps', or 'to_zon' functions")

    print("=" * 100)
    print("  HIKING DATA COMPARISON - JSON vs ZON vs TOON")
    print("=" * 100)
    print("\nThis is the example used on TOON's official website (toonformat.dev)")
    print()
    
    print("─" * 100)
    print("JSON (formatted, 2-space indent)")
    print("─" * 100)
    print(json_formatted)
    print(f"\nSize: {len(json_formatted)} bytes")
    print(f"Estimated tokens: ~{count_tokens(json_formatted)}")
    
    print("\n" + "─" * 100)
    print("JSON (compact/minified)")
    print("─" * 100)
    print(json_compact)
    print(f"\nSize: {len(json_compact)} bytes")
    print(f"Estimated tokens: ~{count_tokens(json_compact)}")
    
    print("\n" + "─" * 100)
    print("ZON")
    print("─" * 100)
    print(zon_str)
    print(f"\nSize: {len(zon_str)} bytes")
    print(f"Estimated tokens: ~{count_tokens(zon_str)}")
    
    print("\n" + "─" * 100)
    print("TOON (reference format)")
    print("─" * 100)
    print(toon_str)
    print(f"\nSize: {len(toon_str)} bytes")
    print(f"Estimated tokens: ~{count_tokens(toon_str)}")
    
    print("\n" + "=" * 100)
    print("  SUMMARY")
    print("=" * 100)
    
    baseline = len(json_formatted)
    
    results = [
        ("JSON (formatted)", len(json_formatted), count_tokens(json_formatted)),
        ("JSON (compact)", len(json_compact), count_tokens(json_compact)),
        ("ZON", len(zon_str), count_tokens(zon_str)),
        ("TOON", len(toon_str), count_tokens(toon_str)),
    ]
    
    print(f"\n{'Format':<20} | {'Bytes':>8} | {'Est. Tokens':>12} | {'vs JSON':>12}")
    print("-" * 65)
    
    for name, size, tokens in results:
        compression = ((baseline - size) / baseline) * 100
        print(f"{name:<20} | {size:8} | {tokens:12} | {compression:11.1f}%")
    
    print("\n" + "=" * 100)
    print("  KEY FINDINGS")
    print("=" * 100)
    print(f"\n✅ ZON is {((baseline - len(zon_str)) / baseline * 100):.1f}% smaller than formatted JSON")
    print(f"✅ TOON is {((baseline - len(toon_str)) / baseline * 100):.1f}% smaller than formatted JSON")
    print(f"\n📊 ZON vs TOON: {abs(len(zon_str) - len(toon_str))} bytes difference")
    
    if len(zon_str) < len(toon_str):
        print(f"   ZON is {((len(toon_str) - len(zon_str)) / len(toon_str) * 100):.1f}% smaller than TOON")
    else:
        print(f"   TOON is {((len(zon_str) - len(toon_str)) / len(zon_str) * 100):.1f}% smaller than ZON")
    
    print("\n" + "=" * 100 + "\n")


if __name__ == '__main__':
    main()
