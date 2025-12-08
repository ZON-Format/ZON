"""Command-line interface for ZON format conversion and validation."""

import argparse
import sys
import json
import os
import csv
from typing import Any, List, Dict
from .core.encoder import encode
from .core.decoder import decode
from .core.exceptions import ZonDecodeError
from .core.adaptive import encode_adaptive, recommend_mode, AdaptiveEncodeOptions
from .core.analyzer import DataComplexityAnalyzer

def convert_command(args):
    """Convert files from various formats (JSON, CSV, YAML) to ZON format.
    
    Args:
        args: Parsed command-line arguments containing:
            - file: Input file path
            - output: Optional output file path (stdout if not specified)
            - format: Optional format type ('json', 'csv', 'yaml')
    
    Raises:
        SystemExit: If file reading or conversion fails
    """
    input_file = args.file
    output_file = args.output
    format_type = args.format
    
    if not format_type:
        ext = os.path.splitext(input_file)[1].lower()
        if ext == '.json':
            format_type = 'json'
        elif ext == '.csv':
            format_type = 'csv'
        elif ext in ['.yaml', '.yml']:
            format_type = 'yaml'
        else:
            format_type = 'json'

    data: Any = None
    
    try:
        if format_type == 'json':
            with open(input_file, 'r') as f:
                data = json.load(f)
        elif format_type == 'csv':
            with open(input_file, 'r') as f:
                reader = csv.DictReader(f)
                data = list(reader)
                for row in data:
                    for k, v in row.items():
                        if v.lower() == 'true': row[k] = True
                        elif v.lower() == 'false': row[k] = False
                        elif v.isdigit(): row[k] = int(v)
        elif format_type == 'yaml':
            try:
                import yaml
                with open(input_file, 'r') as f:
                    data = yaml.safe_load(f)
            except ImportError:
                print("Error: PyYAML not installed. Install with `pip install PyYAML` to support YAML.", file=sys.stderr)
                sys.exit(1)
    except Exception as e:
        print(f"Error reading input file: {e}", file=sys.stderr)
        sys.exit(1)

    zon_output = encode(data)
    
    if output_file:
        with open(output_file, 'w') as f:
            f.write(zon_output)
    else:
        print(zon_output)

def validate_command(args):
    """Validate a ZON file for syntax correctness.
    
    Args:
        args: Parsed command-line arguments containing file path
    
    Raises:
        SystemExit: If validation fails or file cannot be read
    """
    input_file = args.file
    try:
        with open(input_file, 'r') as f:
            content = f.read()
        decode(content)
        print("✅ Valid ZON file")
    except ZonDecodeError as e:
        print(f"❌ Invalid ZON file: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)

def stats_command(args):
    """Display compression statistics comparing ZON size to JSON size.
    
    Args:
        args: Parsed command-line arguments containing file path
    
    Raises:
        SystemExit: If file cannot be read or decoded
    """
    input_file = args.file
    try:
        with open(input_file, 'r') as f:
            content = f.read()
        
        data = decode(content)
        json_str = json.dumps(data, separators=(',', ':'))
        
        zon_size = len(content)
        json_size = len(json_str)
        savings = (1 - (zon_size / json_size)) * 100
        
        print("\n📊 ZON File Statistics")
        print(f"Size:      {zon_size:,} bytes")
        print(f"JSON Size: {json_size:,} bytes")
        print(f"Savings:   {savings:.2f}%")
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

def format_command(args):
    """Format and canonicalize a ZON file through round-trip encoding.
    
    Args:
        args: Parsed command-line arguments containing file path
    
    Raises:
        SystemExit: If file cannot be read or decoded
    """
    input_file = args.file
    try:
        with open(input_file, 'r') as f:
            content = f.read()
        
        data = decode(content)
        formatted = encode(data)
        
        print(formatted)
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

def analyze_command(args):
    """Analyze data complexity and recommend optimal encoding mode.
    
    Args:
        args: Parsed command-line arguments containing file path
    
    Raises:
        SystemExit: If file cannot be read or parsed
    """
    input_file = args.file
    try:
        # Try to read as JSON first, then as ZON
        with open(input_file, 'r') as f:
            content = f.read()
        
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            try:
                data = decode(content)
            except ZonDecodeError:
                print("Error: File is neither valid JSON nor ZON", file=sys.stderr)
                sys.exit(1)
        
        # Analyze the data
        analyzer = DataComplexityAnalyzer()
        result = analyzer.analyze(data)
        recommendation = recommend_mode(data)
        
        print("\n🔍 Data Complexity Analysis")
        print("=" * 50)
        print(f"\nStructure Metrics:")
        print(f"  Nesting depth:    {result.nesting}")
        print(f"  Irregularity:     {result.irregularity:.2%}")
        print(f"  Field count:      {result.field_count}")
        print(f"  Largest array:    {result.array_size}")
        print(f"  Array density:    {result.array_density:.2%}")
        print(f"  Avg fields/obj:   {result.avg_fields_per_object:.1f}")
        
        print(f"\nRecommendation:")
        print(f"  Mode:             {recommendation['mode']}")
        print(f"  Confidence:       {recommendation['confidence']:.2%}")
        print(f"  Reason:           {recommendation['reason']}")
        
        # Show size comparison if requested
        if args.compare:
            zon_compact = encode_adaptive(data, AdaptiveEncodeOptions(mode='compact'))
            zon_readable = encode_adaptive(data, AdaptiveEncodeOptions(mode='readable'))
            zon_llm = encode_adaptive(data, AdaptiveEncodeOptions(mode='llm-optimized'))
            json_str = json.dumps(data, separators=(',', ':'))
            
            print(f"\nSize Comparison:")
            print(f"  Compact mode:      {len(zon_compact):,} bytes")
            print(f"  LLM-optimized:     {len(zon_llm):,} bytes")
            print(f"  Readable mode:     {len(zon_readable):,} bytes")
            print(f"  JSON (compact):    {len(json_str):,} bytes")
            
            savings = (1 - (len(zon_compact) / len(json_str))) * 100
            print(f"  Best savings:      {savings:.1f}%")
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

def encode_command(args):
    """Encode JSON to ZON format with adaptive mode selection.
    
    Args:
        args: Parsed command-line arguments
    
    Raises:
        SystemExit: If file cannot be read or encoding fails
    """
    input_file = args.file
    mode = args.mode or 'compact'
    output_file = args.output
    
    try:
        with open(input_file, 'r') as f:
            data = json.load(f)
        
        options = AdaptiveEncodeOptions(
            mode=mode,
            indent=args.indent
        )
        
        output = encode_adaptive(data, options)
        
        if output_file:
            with open(output_file, 'w') as f:
                f.write(output)
        else:
            print(output)
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

def decode_command(args):
    """Decode ZON back to JSON format.
    
    Args:
        args: Parsed command-line arguments
    
    Raises:
        SystemExit: If file cannot be read or decoding fails
    """
    input_file = args.file
    output_file = args.output
    
    try:
        with open(input_file, 'r') as f:
            content = f.read()
        
        data = decode(content)
        json_str = json.dumps(data, indent=2 if args.pretty else None)
        
        if output_file:
            with open(output_file, 'w') as f:
                f.write(json_str)
        else:
            print(json_str)
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    """Entry point for the ZON CLI tool.
    
    Parses command-line arguments and dispatches to the appropriate command
    handler.
    
    Raises:
        SystemExit: If no command is specified or command fails
    """
    parser = argparse.ArgumentParser(description="ZON CLI Tool v1.2.0")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Encode command (new in v1.2.0)
    encode_parser = subparsers.add_parser("encode", help="Encode JSON to ZON")
    encode_parser.add_argument("file", help="Input JSON file")
    encode_parser.add_argument("-o", "--output", help="Output file")
    encode_parser.add_argument("-m", "--mode", choices=['compact', 'readable', 'llm-optimized'], 
                              help="Encoding mode (default: compact)")
    encode_parser.add_argument("--indent", type=int, default=2, help="Indentation for readable mode")
    
    # Decode command (new in v1.2.0)
    decode_parser = subparsers.add_parser("decode", help="Decode ZON to JSON")
    decode_parser.add_argument("file", help="Input ZON file")
    decode_parser.add_argument("-o", "--output", help="Output file")
    decode_parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    
    # Convert command (legacy)
    convert_parser = subparsers.add_parser("convert", help="Convert files to ZON")
    convert_parser.add_argument("file", help="Input file")
    convert_parser.add_argument("-o", "--output", help="Output file")
    convert_parser.add_argument("--format", choices=['json', 'csv', 'yaml'], help="Input format")
    
    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Validate ZON file")
    validate_parser.add_argument("file", help="Input ZON file")
    
    # Stats command
    stats_parser = subparsers.add_parser("stats", help="Show compression statistics")
    stats_parser.add_argument("file", help="Input ZON file")
    
    # Format command
    format_parser = subparsers.add_parser("format", help="Format/Canonicalize ZON file")
    format_parser.add_argument("file", help="Input ZON file")
    
    # Analyze command (new in v1.2.0)
    analyze_parser = subparsers.add_parser("analyze", help="Analyze data complexity")
    analyze_parser.add_argument("file", help="Input file (JSON or ZON)")
    analyze_parser.add_argument("--compare", action="store_true", 
                               help="Show size comparison across modes")
    
    args = parser.parse_args()
    
    if args.command == "encode":
        encode_command(args)
    elif args.command == "decode":
        decode_command(args)
    elif args.command == "convert":
        convert_command(args)
    elif args.command == "validate":
        validate_command(args)
    elif args.command == "stats":
        stats_command(args)
    elif args.command == "format":
        format_command(args)
    elif args.command == "analyze":
        analyze_command(args)
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
