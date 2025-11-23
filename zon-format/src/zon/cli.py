import argparse
import sys
import json
import os
from .encoder import encode
from .decoder import decode

def main():
    parser = argparse.ArgumentParser(description="ZON CLI")
    parser.add_argument("file", nargs="?", type=argparse.FileType("r"), default=sys.stdin, help="Input file (JSON)")
    parser.add_argument("-o", "--output", type=str, help="Output file (ZON)")
    parser.add_argument("--stats", action="store_true", help="Show compression stats")
    
    args = parser.parse_args()
    
    # Read Input
    try:
        data = json.load(args.file)
    except json.JSONDecodeError:
        print("Error: Invalid JSON input", file=sys.stderr)
        sys.exit(1)
        
    if not isinstance(data, list):
        print("Error: Input must be a list of objects", file=sys.stderr)
        sys.exit(1)

    # Encode
    zon_output = encode(data)
    
    # Output
    if args.output:
        with open(args.output, "w") as f:
            f.write(zon_output)
    else:
        print(zon_output)
        
    # Stats
    if args.stats:
        input_size = len(json.dumps(data))
        output_size = len(zon_output)
        ratio = (1 - (output_size / input_size)) * 100
        print(f"\nStats:")
        print(f"JSON Size: {input_size} bytes")
        print(f"ZON Size:  {output_size} bytes")
        print(f"Compression: {ratio:.2f}%")

if __name__ == "__main__":
    main()
