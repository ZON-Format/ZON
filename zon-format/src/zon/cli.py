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


def main():
    """Entry point for the ZON CLI tool.
    
    Parses command-line arguments and dispatches to the appropriate command
    handler (convert, validate, stats, or format).
    
    Raises:
        SystemExit: If no command is specified or command fails
    """
    parser = argparse.ArgumentParser(description="ZON CLI Tool")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    convert_parser = subparsers.add_parser("convert", help="Convert files to ZON")
    convert_parser.add_argument("file", help="Input file")
    convert_parser.add_argument("-o", "--output", help="Output file")
    convert_parser.add_argument("--format", choices=['json', 'csv', 'yaml'], help="Input format")
    
    validate_parser = subparsers.add_parser("validate", help="Validate ZON file")
    validate_parser.add_argument("file", help="Input ZON file")
    
    stats_parser = subparsers.add_parser("stats", help="Show compression statistics")
    stats_parser.add_argument("file", help="Input ZON file")
    
    format_parser = subparsers.add_parser("format", help="Format/Canonicalize ZON file")
    format_parser.add_argument("file", help="Input ZON file")
    
    args = parser.parse_args()
    
    if args.command == "convert":
        convert_command(args)
    elif args.command == "validate":
        validate_command(args)
    elif args.command == "stats":
        stats_command(args)
    elif args.command == "format":
        format_command(args)
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
