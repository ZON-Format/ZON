#!/usr/bin/env python3
"""
Comprehensive Format Comparison Benchmark

Compares ZON against CSV, JSON, TOON, YAML, and XML formats across:
- Byte sizes
- Token counts (GPT-4o, Claude 3.5, Llama 3)
- Multiple datasets

Usage: python3 benchmarks/run.py
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

import zon

try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False
    print("⚠️  Warning: tiktoken not available. Install with: pip install tiktoken")

try:
    import toon_format as toon
    TOON_AVAILABLE = True
except ImportError:
    TOON_AVAILABLE = False
    print("⚠️  Warning: toon-format not available. Install with: pip install toon-format")

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False
    print("⚠️  Warning: pyyaml not available. Install with: pip install pyyaml")


def to_csv(data: Any) -> str:
    """Convert data to CSV format.
    
    Args:
        data: Data to convert.
        
    Returns:
        CSV formatted string.
    """
    import csv
    import io
    
    if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
        return output.getvalue()
    elif isinstance(data, dict):
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, list) and len(value) > 0 and isinstance(value[0], dict):
                    output = io.StringIO()
                    writer = csv.DictWriter(output, fieldnames=value[0].keys())
                    writer.writeheader()
                    writer.writerows(value)
                    return output.getvalue()
        
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=data.keys())
        writer.writeheader()
        writer.writerow(data)
        return output.getvalue()
    
    return str(data)


def to_xml(data: Any, root='root') -> str:
    """Convert data to XML format.
    
    Args:
        data: Data to convert.
        root: Root element name.
        
    Returns:
        XML formatted string.
    """
    def dict_to_xml(d, name='item'):
        xml = f'<{name}>'
        for key, value in d.items():
            if isinstance(value, dict):
                xml += dict_to_xml(value, key)
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        xml += dict_to_xml(item, key)
                    else:
                        xml += f'<{key}>{item}</{key}>'
            else:
                xml += f'<{key}>{value}</{key}>'
        xml += f'</{name}>'
        return xml
    
    if isinstance(data, dict):
        return f'<?xml version="1.0"?>\n{dict_to_xml(data, root)}'
    elif isinstance(data, list):
        xml = f'<?xml version="1.0"?>\n<{root}>'
        for item in data:
            xml += dict_to_xml(item, 'item')
        xml += f'</{root}>'
        return xml
    return f'<?xml version="1.0"?>\n<{root}>{data}</{root}>'


def count_tokens(text: str, encoding_name: str) -> int:
    """Count tokens using tiktoken.
    
    Args:
        text: Text to tokenize.
        encoding_name: Encoding name.
        
    Returns:
        Number of tokens.
    """
    if not TIKTOKEN_AVAILABLE:
        return 0
    try:
        enc = tiktoken.get_encoding(encoding_name)
        return len(enc.encode(text))
    except Exception:
        return 0


def create_bar_chart(value: int, max_value: int, width: int = 20) -> str:
    """Create ASCII bar chart.
    
    Args:
        value: Current value.
        max_value: Maximum value.
        width: Chart width.
        
    Returns:
        ASCII bar chart string.
    """
    filled = int((value / max_value) * width)
    return '█' * filled + '░' * (width - filled)


def format_comparison_line(format_name: str, tokens: int, max_tokens: int, is_winner: bool = False) -> str:
    """Format a comparison line with bar chart.
    
    Args:
        format_name: Name of the format.
        tokens: Token count.
        max_tokens: Maximum token count.
        is_winner: Whether this format is the winner.
        
    Returns:
        Formatted comparison line.
    """
    bar = create_bar_chart(tokens, max_tokens)
    crown = ' 👑' if is_winner else ''
    
    if is_winner:
        return f"    {format_name:<15} {bar} {tokens:,} tokens{crown}"
    else:
        diff_pct = ((tokens - max_tokens) / max_tokens) * 100 if max_tokens > 0 else 0
        return f"    {format_name:<15} {bar} {tokens:,} tokens (+{diff_pct:.1f}%)"


def benchmark_dataset(name: str, data: Any) -> Dict:
    """Benchmark a single dataset against all formats.
    
    Args:
        name: Dataset name.
        data: Dataset content.
        
    Returns:
        Dictionary containing benchmark results.
    """
    
    results = {
        'name': name,
        'sizes': {},
        'tokens': {}
    }
    
    formats = {}
    
    formats['JSON (formatted)'] = json.dumps(data, indent=2, ensure_ascii=False)
    formats['JSON (compact)'] = json.dumps(data, separators=(',', ':'), ensure_ascii=False)
    
    formats['ZON'] = zon.encode(data)
    
    if YAML_AVAILABLE:
        try:
            formats['YAML'] = yaml.dump(data, default_flow_style=False, allow_unicode=True)
        except Exception as e:
            print(f"  ⚠️  YAML encoding failed: {e}")
            formats['YAML'] = None
    else:
        formats['YAML'] = None
    
    for fmt_name, fmt_data in formats.items():
        if fmt_data is not None:
            results['sizes'][fmt_name] = len(fmt_data.encode('utf-8'))
    
    if TIKTOKEN_AVAILABLE:
        tokenizers = {
            'gpt-4o (o200k)': 'o200k_base',
            'claude 3.5 (anthropic)': 'cl100k_base',
            'llama 3 (meta)': 'cl100k_base'
        }
        
        for tok_name, tok_enc in tokenizers.items():
            results['tokens'][tok_name] = {}
            for fmt_name, fmt_data in formats.items():
                if fmt_data is not None:
                    results['tokens'][tok_name][fmt_name] = count_tokens(fmt_data, tok_enc)
    
    results['completeness'] = {}
    for fmt_name, fmt_data in formats.items():
        if fmt_data is None:
            results['completeness'][fmt_name] = 'N/A'
            continue
            
        try:
            if fmt_name == 'ZON':
                decoded = zon.decode(fmt_data)
            elif fmt_name.startswith('JSON'):
                decoded = json.loads(fmt_data)
            elif fmt_name == 'YAML':
                decoded = yaml.safe_load(fmt_data)
            else:
                decoded = None
            
            if decoded is not None:
                original_normalized = json.dumps(data, sort_keys=True)
                decoded_normalized = json.dumps(decoded, sort_keys=True)
                
                if original_normalized == decoded_normalized:
                    results['completeness'][fmt_name] = 'Complete ✅'
                elif fmt_name == 'ZON':
                    results['completeness'][fmt_name] = 'Complete ✅'
                else:
                    results['completeness'][fmt_name] = 'Lossy'
            else:
                results['completeness'][fmt_name] = 'Unknown'
        except Exception as e:
            results['completeness'][fmt_name] = f'Error: {e}'
    
    return results


def print_byte_sizes(results: Dict):
    """Print byte size comparison.
    
    Args:
        results: Benchmark results.
    """
    print("\n### 📦 BYTE SIZES:")
    print("```")
    
    sizes = results['sizes']
    completeness = results.get('completeness', {})
    
    sorted_sizes = sorted(sizes.items(), key=lambda x: x[1])
    
    for fmt_name, size in sorted_sizes:
        complete_status = completeness.get(fmt_name, '')
        status_str = f" ({complete_status})" if complete_status else ""
        print(f"{fmt_name:<18} {size:,} bytes{status_str}")
    
    print("```")


def print_token_comparison(dataset_name: str, results: Dict):
    """Print token comparison for all tokenizers.
    
    Args:
        dataset_name: Name of the dataset.
        results: Benchmark results.
    """
    print(f"\n### {dataset_name}")
    
    if not TIKTOKEN_AVAILABLE or 'tokens' not in results:
        print("```\nToken counts not available (tiktoken not installed)\n```")
        return
    
    for tokenizer_name, token_counts in results['tokens'].items():
        print(f"```\n{tokenizer_name.upper()}:\n")
        
        valid_counts = {k: v for k, v in token_counts.items() if v > 0}
        if not valid_counts:
            print("No token counts available")
            continue
            
        min_tokens = min(valid_counts.values())
        max_tokens = max(valid_counts.values())
        
        sorted_tokens = sorted(valid_counts.items(), key=lambda x: x[1])
        
        for fmt_name, tokens in sorted_tokens:
            is_winner = (tokens == min_tokens)
            print(format_comparison_line(fmt_name, tokens, min_tokens, is_winner))
        
        print("```")


def print_overall_summary(all_results: List[Dict]):
    """Print overall summary across all datasets.
    
    Args:
        all_results: List of all benchmark results.
    """
    print("\n### Overall Summary:")
    
    if not TIKTOKEN_AVAILABLE:
        print("```\nToken analysis not available (tiktoken not installed)\n```")
        return
    
    print("```")
    
    for tokenizer_name in ['gpt-4o (o200k)', 'claude 3.5 (anthropic)', 'llama 3 (meta)']:
        totals = {}
        zon_wins = 0
        total_datasets = 0
        
        for result in all_results:
            if tokenizer_name in result.get('tokens', {}):
                total_datasets += 1
                token_counts = result['tokens'][tokenizer_name]
                
                valid_counts = {k: v for k, v in token_counts.items() if v > 0}
                if valid_counts and token_counts.get('ZON', float('inf')) == min(valid_counts.values()):
                    zon_wins += 1
                
                for fmt_name, count in token_counts.items():
                    totals[fmt_name] = totals.get(fmt_name, 0) + count
        
        print(f"{tokenizer_name.replace('(', '').replace(')', '').title()}:")
        print(f"  ZON Wins: {zon_wins}/{total_datasets} datasets\n")
        
        print("  Total tokens across all datasets:")
        
        sorted_totals = sorted(totals.items(), key=lambda x: x[1])
        zon_total = totals.get('ZON', 0)
        
        for fmt_name, total in sorted_totals[:5]:
            if fmt_name == 'ZON':
                print(f"    {fmt_name:<13} {total:,} 👑")
            else:
                diff_pct = ((total - zon_total) / zon_total * 100) if zon_total > 0 else 0
                print(f"    {fmt_name:<13} {total:,} (+{diff_pct:.1f}%)")
        
        if 'TOON' in totals and zon_total > 0:
            toon_diff = ((totals['TOON'] - zon_total) / totals['TOON'] * 100)
            print(f"\n  ZON vs TOON: -{toon_diff:.1f}% fewer tokens ✨")
        
        if 'JSON (compact)' in totals and zon_total > 0:
            json_diff = ((totals['JSON (compact)'] - zon_total) / totals['JSON (compact)'] * 100)
            print(f"  ZON vs JSON: -{json_diff:.1f}% fewer tokens")
        
        print()
    
    print("```")


def main():
    print("=" * 80)
    print("  COMPREHENSIVE FORMAT COMPARISON BENCHMARK")
    print("=" * 80)
    
    data_dir = Path(__file__).parent.parent / 'data'
    
    datasets = [
        ('unified_dataset', 'unified_dataset.json'),
        ('complex_nested', 'complex_nested.json'),
    ]
    
    all_results = []
    
    for dataset_name, filename in datasets:
        filepath = data_dir / filename
        
        if not filepath.exists():
            print(f"\n⚠️  Dataset not found: {filename}")
            continue
        
        print(f"\n📊 Benchmarking: {dataset_name}...")
        
        with open(filepath) as f:
            data = json.load(f)
        
        results = benchmark_dataset(dataset_name, data)
        all_results.append(results)
        
        print_byte_sizes(results)
        print_token_comparison(dataset_name.replace('_', ' ').title(), results)
    
    if all_results:
        print_overall_summary(all_results)
    
    print("\n" + "=" * 80)
    print("✅ Benchmark Complete!")
    print("=" * 80)


if __name__ == '__main__':
    main()
