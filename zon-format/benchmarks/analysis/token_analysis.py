#!/usr/bin/env python3
"""
Analyze token counts using the exact same tokenizer as TOON's benchmarks.
TOON uses gpt-tokenizer with o200k_base encoding (GPT-5 tokenizer).
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))
import zon

try:
    import tiktoken
    HAS_TIKTOKEN = True
except ImportError:
    HAS_TIKTOKEN = False
    print("⚠️  tiktoken not installed. Install with: pip install tiktoken")
    sys.exit(1)


def count_tokens_accurate(text, encoding_name='o200k_base'):
    """Count tokens using tiktoken with the specified encoding.
    
    Args:
        text: Text to tokenize.
        encoding_name: Encoding name.
        
    Returns:
        Number of tokens.
    """
    encoding = tiktoken.get_encoding(encoding_name)
    return len(encoding.encode(text))


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
    
    zon_str = zon.encode(data)
    
    print("=" * 100)
    print("  TOKEN ANALYSIS - Using GPT-5 Tokenizer (o200k_base)")
    print("=" * 100)
    print("\nThis matches TOON's official benchmark methodology")
    print("Reference: https://github.com/toon-format/toon#benchmarks")
    print()
    
    results = []
    
    formats = [
        ("JSON (formatted)", json_formatted),
        ("JSON (compact)", json_compact),
        ("ZON", zon_str),
        ("TOON", toon_str),
    ]
    
    print("─" * 100)
    print(f"{'Format':<20} | {'Bytes':>8} | {'o200k_base':>12} | {'cl100k_base':>12} | {'p50k_base':>12}")
    print("─" * 100)
    
    for name, text in formats:
        tokens_o200k = count_tokens_accurate(text, 'o200k_base')
        tokens_cl100k = count_tokens_accurate(text, 'cl100k_base')
        tokens_p50k = count_tokens_accurate(text, 'p50k_base')
        
        results.append({
            'name': name,
            'text': text,
            'bytes': len(text),
            'tokens_o200k': tokens_o200k,
            'tokens_cl100k': tokens_cl100k,
            'tokens_p50k': tokens_p50k,
        })
        
        print(f"{name:<20} | {len(text):8} | {tokens_o200k:12} | {tokens_cl100k:12} | {tokens_p50k:12}")
    
    print("\n" + "=" * 100)
    print("  TOON'S CLAIMED NUMBERS vs ACTUAL")
    print("=" * 100)
    
    json_result = next(r for r in results if r['name'] == 'JSON (formatted)')
    toon_result = next(r for r in results if r['name'] == 'TOON')
    zon_result = next(r for r in results if r['name'] == 'ZON')
    
    print(f"\nJSON (formatted):")
    print(f"  TOON claims: 235 tokens")
    print(f"  o200k_base:  {json_result['tokens_o200k']} tokens")
    print(f"  cl100k_base: {json_result['tokens_cl100k']} tokens")
    print(f"  p50k_base:   {json_result['tokens_p50k']} tokens")
    
    print(f"\nTOON:")
    print(f"  TOON claims: 106 tokens")
    print(f"  o200k_base:  {toon_result['tokens_o200k']} tokens")
    print(f"  cl100k_base: {toon_result['tokens_cl100k']} tokens")
    print(f"  p50k_base:   {toon_result['tokens_p50k']} tokens")
    
    print(f"\nZON:")
    print(f"  o200k_base:  {zon_result['tokens_o200k']} tokens")
    print(f"  cl100k_base: {zon_result['tokens_cl100k']} tokens")
    print(f"  p50k_base:   {zon_result['tokens_p50k']} tokens")
    
    print("\n" + "=" * 100)
    print("  COMPRESSION ANALYSIS (using o200k_base)")
    print("=" * 100)
    
    baseline_tokens = json_result['tokens_o200k']
    
    print(f"\n{'Format':<20} | {'Tokens':>8} | {'Reduction':>12}")
    print("─" * 50)
    for r in results:
        reduction = ((baseline_tokens - r['tokens_o200k']) / baseline_tokens) * 100
        print(f"{r['name']:<20} | {r['tokens_o200k']:8} | {reduction:11.1f}%")
    
    print("\n" + "=" * 100)
    print("  ZON vs TOON")
    print("=" * 100)
    
    toon_tokens = toon_result['tokens_o200k']
    zon_tokens = zon_result['tokens_o200k']
    
    print(f"\nToken count:")
    print(f"  TOON: {toon_tokens}")
    print(f"  ZON:  {zon_tokens}")
    print(f"  Difference: {abs(toon_tokens - zon_tokens)} tokens")
    
    if zon_tokens < toon_tokens:
        print(f"  ZON is {((toon_tokens - zon_tokens) / toon_tokens * 100):.1f}% fewer tokens")
    else:
        print(f"  TOON is {((zon_tokens - toon_tokens) / zon_tokens * 100):.1f}% fewer tokens")
    
    print("\n" + "=" * 100)
    print("  FULL TEXT OUTPUT")
    print("=" * 100)
    
    for r in results:
        print(f"\n{r['name']} ({r['tokens_o200k']} tokens, {r['bytes']} bytes):")
        print("─" * 100)
        print(r['text'])
    
    print("\n" + "=" * 100 + "\n")


if __name__ == '__main__':
    main()
