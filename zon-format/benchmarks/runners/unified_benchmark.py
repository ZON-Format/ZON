#!/usr/bin/env python3
"""
Unified Benchmark - JSON vs ZON (and TOON reference when available)

This script:
- Scans `benchmarks/data/` for `*.json` datasets (and matching `.toon` files)
- Computes sizes for JSON (formatted and compact), ZON encoding, and TOON reference file if present
- Computes token counts using `tiktoken` for both `o200k_base` and `cl100k_base` encodings
- Prints a single consolidated table with results and a brief summary

Run: python zon-format/benchmarks/unified_benchmark.py
"""

import sys
import json
from pathlib import Path
from textwrap import shorten

sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))
import zon

try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except Exception as e:
    tiktoken = None
    TIKTOKEN_AVAILABLE = False
    print("⚠️  Warning: tiktoken not available. Token counts will not be displayed.")
    print("   Install with: pip install tiktoken --break-system-packages")

DATA_DIR = Path(__file__).parent.parent / 'data'


def count_tokens(text, encoding_name):
    """Count tokens in text using specified encoding.
    
    Args:
        text: Text to tokenize.
        encoding_name: Name of the encoding to use.
        
    Returns:
        Number of tokens or None if tiktoken is not available.
    """
    if not tiktoken:
        return None
    try:
        enc = tiktoken.get_encoding(encoding_name)
        return len(enc.encode(text))
    except Exception:
        return None


def load_toon_if_exists(json_path: Path):
    """Load matching TOON file if it exists.
    
    Args:
        json_path: Path to the JSON file.
        
    Returns:
        Content of the TOON file or None.
    """
    toon_path = json_path.with_suffix('.toon')
    if toon_path.exists():
        return toon_path.read_text(encoding='utf-8').strip()
    return None


def analyze_dataset(json_path: Path):
    """Analyze a single dataset for size and token counts.
    
    Args:
        json_path: Path to the JSON file.
        
    Returns:
        Dictionary containing analysis results.
    """
    name = json_path.stem
    with open(json_path, encoding='utf-8') as f:
        data = json.load(f)

    json_formatted = json.dumps(data, indent=2)
    json_compact = json.dumps(data, separators=(',', ':'))
    zon_str = zon.encode(data)

    toon_str = load_toon_if_exists(json_path)

    item = {
        'name': name,
        'bytes_json_formatted': len(json_formatted),
        'bytes_json_compact': len(json_compact),
        'bytes_zon': len(zon_str) if zon_str is not None else None,
        'bytes_toon': len(toon_str) if toon_str is not None else None,
        'tokens': {},
        'data': data,
    }

    encodings = {
        'gpt-4o (o200k)': 'o200k_base',
        'claude-3.5 (anthropic)': 'cl100k_base',
        'llama-3 (meta)': 'cl100k_base'
    }
    
    for enc_name, enc_id in encodings.items():
        item['tokens'][enc_name] = {
            'json_formatted': count_tokens(json_formatted, enc_id),
            'json_compact': count_tokens(json_compact, enc_id),
            'zon': count_tokens(zon_str, enc_id),
            'toon': count_tokens(toon_str, enc_id) if toon_str is not None else None,
        }

    return item


def human(n):
    """Format bytes to human-readable string.
    
    Args:
        n: Number of bytes.
        
    Returns:
        Formatted string (e.g., "1.5 KB").
    """
    for u in ('B','KB','MB'):
        if n is None:
            return 'N/A'
        if n < 1024:
            return f"{n:.1f} {u}"
        n /= 1024
    return f"{n:.1f} GB"


def print_table(items):
    """Print the benchmark results table.
    
    Args:
        items: List of analyzed dataset items.
    """
    header = f"{'Dataset':<25} | {'Records':>7} | {'JSON Size':>10} | {'ZON Size':>10} | {'Compression':>11} | {'JSON tk':>9} | {'ZON tk':>9}"
    print('\n' + '='*len(header))
    print('  UNIFIED BENCHMARK - JSON vs ZON')
    print('='*len(header) + '\n')
    print(header)
    print('-'*len(header))

    for it in items:
        name = it['name']
        json_b = it['bytes_json_compact']
        zon_b = it['bytes_zon']
        toon_b = it['bytes_toon']

        data = it.get('data')
        rec_count = 1
        if isinstance(data, dict):
            rec_count = 0
            for v in data.values():
                if isinstance(v, list):
                    rec_count = len(v)
                    break
            if rec_count == 0:
                rec_count = 1
        elif isinstance(data, list):
            rec_count = len(data)
        
        if name == 'hikes':
            rec_count = 1

        compression_val = (1 - zon_b / json_b) * 100 if (zon_b and json_b) else None
        if compression_val is None:
            compression_display = 'N/A'
        else:
            sign = '+' if compression_val >= 0 else '-'
            compression_display = f"{sign}{abs(compression_val):.1f}%"

        json_tk = it['tokens'].get('o200k_base', {}).get('json_compact')
        zon_tk = it['tokens'].get('o200k_base', {}).get('zon')

        json_tk_display = str(json_tk) if json_tk is not None else 'N/A'
        zon_tk_display = str(zon_tk) if zon_tk is not None else 'N/A'

        print(f"{name:<25} | {rec_count:7} | {human(json_b):>10} | {human(zon_b):>10} | {compression_display:>11} | {json_tk_display:>9} | {zon_tk_display:>9}")

    print('\n')


def main():
    """Run unified benchmark."""
    json_files = sorted([p for p in DATA_DIR.glob('*.json')])
    items = []
    for jf in json_files:
        try:
            items.append(analyze_dataset(jf))
        except Exception as e:
            print(f"Error analyzing {jf.name}: {e}")

    print_table(items)

    print('SUMMARY')
    total_json = sum(i['bytes_json_compact'] for i in items)
    total_zon = sum(i['bytes_zon'] for i in items if i['bytes_zon'] is not None)
    print(f"Total JSON (compact) size: {human(total_json)}")
    print(f"Total ZON size: {human(total_zon)}")
    if total_json:
        print(f"Overall compression: {(1 - total_zon/total_json)*100:.1f}%")

    if tiktoken:
        print('\n📊 Token Efficiency by Tokenizer:')
        
        for tokenizer_name in ['gpt-4o (o200k)', 'claude-3.5 (anthropic)', 'llama-3 (meta)']:
            print(f'\n{tokenizer_name.upper()}:')
            header = f"{'Dataset':<20} | {'JSON tk':>8} | {'ZON tk':>8} | {'TOON tk':>8} | {'ZON Savings':>12}"
            print(header)
            print('-' * len(header))
            
            for it in items:
                tokens = it['tokens'].get(tokenizer_name, {})
                json_t = tokens.get('json_compact')
                zon_t = tokens.get('zon')
                toon_t = tokens.get('toon')
                
                if json_t and zon_t:
                    savings = ((json_t - zon_t) / json_t) * 100
                    savings_str = f"{savings:+.1f}%"
                else:
                    savings_str = ''
                
                json_display = str(json_t) if json_t else 'N/A'
                zon_display = str(zon_t) if zon_t else 'N/A'
                toon_display = str(toon_t) if toon_t else ''
                
                print(f"{it['name']:<20} | {json_display:>8} | {zon_display:>8} | {toon_display:>8} | {savings_str:>12}")
        
        print('\n\nDETAILED TOKEN COMPARISON (GPT-4o o200k):')
        header = f"{'Dataset':<20} | {'JSON tk':>8} | {'ZON tk':>8} | {'TOON tk':>8} | {'vs TOON (bytes)':>15} | {'tk diff':>9}"
        print(header)
        print('-'*len(header))
        for it in items:
            tokens = it['tokens'].get('gpt-4o (o200k)', {})
            json_t = tokens.get('json_compact')
            zon_t = tokens.get('zon')
            toon_t = tokens.get('toon')
            if it['bytes_toon']:
                vs_toon_bytes_val = (it['bytes_toon'] - it['bytes_zon']) / it['bytes_toon'] * 100
                vs_toon_bytes = f"+{vs_toon_bytes_val:.1f}%"
            else:
                vs_toon_bytes = ''

            if (zon_t is not None) and (toon_t is not None):
                tk_diff = toon_t - zon_t
                tk_diff_display = f"+{tk_diff}" if tk_diff >= 0 else str(tk_diff)
            else:
                tk_diff_display = ''

            print(f"{it['name']:<20} | {str(json_t):>8} | {str(zon_t):>8} | {str(toon_t):>8} | {vs_toon_bytes:>15} | {tk_diff_display:>9}")

        toon_items = [it for it in items if it['bytes_toon']]
        if toon_items:
            print('\nTOON Comparison (datasets with .toon files):')
            t_header = f"{'Dataset':<20} | {'Records':>7} | {'JSON Size':>10} | {'ZON Size':>10} | {'TOON Size':>10} | {'vs TOON':>9} | {'JSON tk':>8} | {'ZON tk':>8} | {'TOON tk':>8}"
            print(t_header)
            print('-'*len(t_header))
            for it in toon_items:
                data = it.get('data')
                rec_count = 1
                if isinstance(data, dict):
                    rec_count = 0
                    for v in data.values():
                        if isinstance(v, list):
                            rec_count = len(v)
                            break
                    if rec_count == 0:
                        rec_count = 1
                elif isinstance(data, list):
                    rec_count = len(data)

                vs_toon_val = (it['bytes_toon'] - it['bytes_zon']) / it['bytes_toon'] * 100
                vs_toon_str = f"+{vs_toon_val:.1f}%" if vs_toon_val >= 0 else f"{vs_toon_val:.1f}%"
                tokens = it['tokens'].get('gpt-4o (o200k)', {})
                print(f"{it['name']:<20} | {rec_count:7} | {human(it['bytes_json_compact']):>10} | {human(it['bytes_zon']):>10} | {human(it['bytes_toon']):>10} | {vs_toon_str:>9} | {str(tokens.get('json_compact')):>8} | {str(tokens.get('zon')):>8} | {str(tokens.get('toon')):>8}")

    print('\nDone.')

if __name__ == '__main__':
    main()
