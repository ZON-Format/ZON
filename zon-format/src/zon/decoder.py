"""
ZON Decoder v8.0 - ClearText Format

This decoder parses clean, document-style ZON with YAML-like metadata
and CSV-like tables using @table syntax.
"""

import json
import re
import csv
import io
from typing import List, Dict, Any, Optional
from .constants import *
from .exceptions import ZonDecodeError


class ZonDecoder:
    def decode(self, zon_str: str) -> Any:
        """
        Decode ZON v8.0 ClearText format to original data structure.
        
        Args:
            zon_str: ZON-encoded string
            
        Returns:
            Decoded data (list or dict)
        """
        if not zon_str:
            return {}
        
        lines = zon_str.strip().split('\n')
        if not lines:
            return {}
        
        # Special case: Root-level ZON list (irregular schema)
        # If entire input is a single line starting with [, it's a ZON list
        if len(lines) == 1 and lines[0].strip().startswith('['):
            return self._parse_zon_node(lines[0])
        
        #  Main decode loop
        metadata = {}
        tables = {}
        current_table = None
        current_table_name = None
        
        for line in lines:
            line = line.rstrip()
            
            # Skip blank lines
            if not line:
                continue
            
            # Table header: @hikes(2): id, name, sunny
            if line.startswith(TABLE_MARKER):
                current_table_name, current_table = self._parse_table_header(line)
                tables[current_table_name] = current_table
            
            # Table row (if we're in a table and haven't read all rows)
            elif current_table is not None and current_table['row_index'] < current_table['expected_rows']:
                row = self._parse_table_row(line, current_table)
                current_table['rows'].append(row)
                
                # If we've read all rows, exit table mode
                if current_table['row_index'] >= current_table['expected_rows']:
                    current_table = None
            
            # Metadata line: key: value
            elif META_SEPARATOR in line:
                current_table = None  # Exit table mode (safety)
                key, val = line.split(META_SEPARATOR, 1)
                metadata[key.strip()] = self._parse_value(val.strip())
        
        # Recombine tables into metadata
        for table_name, table in tables.items():
            metadata[table_name] = self._reconstruct_table(table)
        
        # Unflatten dotted keys
        result = self._unflatten(metadata)
        
        # Unwrap pure lists: if only key is 'data', return the list directly
        if len(result) == 1 and 'data' in result and isinstance(result['data'], list):
            return result['data']
        
        return result

    def _parse_table_header(self, line: str) -> tuple:
        """
        Parse table header line.
        
        Format: @tablename(count): col1, col2, col3
        
        Args:
            line: Header line
            
        Returns:
            (table_name, table_info dict)
        """
        # Extract: @hikes(2): id, name, sunny
        match = re.match(r'^' + re.escape(TABLE_MARKER) + r'(\w+)\((\d+)\)' + re.escape(META_SEPARATOR) + r'(.+)$', line)
        if not match:
            raise ZonDecodeError(f"Invalid table header: {line}")
        
        table_name = match.group(1)
        count = int(match.group(2))
        cols_str = match.group(3)
        
        # Parse column names
        cols = [c.strip() for c in cols_str.split(',')]
        
        return table_name, {
            'cols': cols,
            'rows': [],
            'prev_vals': {col: None for col in cols},
            'row_index': 0,
            'expected_rows': count
        }

    def _parse_table_row(self, line: str, table: Dict) -> Dict:
        """
        Parse a table row with compression token support.
        
        Args:
            line: Row line (CSV format)
            table: Table info from header
            
        Returns:
            Decoded row dictionary
        """
        # Parse CSV tokens
        tokens = list(csv.reader([line]))[0]
        
        # Pad if needed
        while len(tokens) < len(table['cols']):
            tokens.append('')
        
        row = {}
        prev_vals = table['prev_vals']
        row_idx = table['row_index']
        
        for i, (col, tok) in enumerate(zip(table['cols'], tokens)):
            # Explicit value
            val = self._parse_value(tok)
            row[col] = val
            prev_vals[col] = val
        
        table['row_index'] += 1
        return row

    def _reconstruct_table(self, table: Dict) -> List[Dict]:
        """
        Reconstruct table from parsed rows.
        
        Args:
            table: Table info with rows
            
        Returns:
            List of dictionaries
        """
        return [self._unflatten(row) for row in table['rows']]

    def _parse_zon_node(self, text: str) -> Any:
        """
        Recursive parser for YAML-like ZON nested format.
        - Dict: {key:val,key:val}
        - List: [val,val]
        """
        text = text.strip()
        if not text:
            return None
            
        # Dict: {k:v,k:v}
        if text.startswith('{') and text.endswith('}'):
            content = text[1:-1].strip()
            if not content:
                return {}
                
            obj = {}
            # Split by comma, respecting nesting
            pairs = self._split_by_delimiter(content, ',')
            
            for pair in pairs:
                if ':' not in pair:
                    continue
                    
                # Find first unquoted colon
                colon_pos = self._find_delimiter(pair, ':')
                if colon_pos == -1:
                    continue
                    
                key_str = pair[:colon_pos].strip()
                val_str = pair[colon_pos+1:].strip()
                
                key = self._parse_primitive(key_str)
                val = self._parse_zon_node(val_str)
                obj[key] = val
                
            return obj
            
        # List: [v,v]
        if text.startswith('[') and text.endswith(']'):
            content = text[1:-1].strip()
            if not content:
                return []
                
            items = self._split_by_delimiter(content, ',')
            return [self._parse_zon_node(item) for item in items]
            
        # Leaf node (primitive)
        return self._parse_primitive(text)
    
    def _find_delimiter(self, text: str, delim: str) -> int:
        """Find first occurrence of delimiter outside quotes."""
        in_quote = False
        quote_char = None
        depth = 0
        
        for i, char in enumerate(text):
            if char in ['"', "'"]:
                if not in_quote:
                    in_quote = True
                    quote_char = char
                elif char == quote_char:
                    in_quote = False
                    quote_char = None
            elif not in_quote:
                if char in ['{', '[']:
                    depth += 1
                elif char in ['}', ']']:
                    depth -= 1
                elif char == delim and depth == 0:
                    return i
        return -1
    
    def _split_by_delimiter(self, text: str, delim: str) -> list:
        """Split text by delimiter, respecting quotes and nesting."""
        parts = []
        current = []
        in_quote = False
        quote_char = None
        depth = 0
        
        for char in text:
            if char in ['"', "'"]:
                if not in_quote:
                    in_quote = True
                    quote_char = char
                elif char == quote_char:
                    in_quote = False
                    quote_char = None
                current.append(char)
            elif not in_quote:
                if char in ['{', '[']:
                    depth += 1
                    current.append(char)
                elif char in ['}', ']']:
                    depth -= 1
                    current.append(char)
                elif char == delim and depth == 0:
                    parts.append("".join(current))
                    current = []
                else:
                    current.append(char)
            else:
                current.append(char)
                
        if current:
            parts.append("".join(current))
            
        return parts

    def _parse_primitive(self, val: str) -> Any:
        """
        Parse a primitive value (T/F/null/number/string) without checking for ZON structure.
        This prevents infinite recursion.
        Supports multiple languages and cases for booleans/null.
        """
        val = val.strip()
        
        # Case-insensitive boolean and null handling (multi-language support)
        val_lower = val.lower()
        
        # Booleans - support T/F (ZON compact) and various language formats
        if val_lower in ['t', 'true']:
            return True
        if val_lower in ['f', 'false']:
            return False
        
        # Null - support various programming languages
        if val_lower in ['null', 'none', 'nil']:
            return None
        
        # Quoted string (JSON style)
        if val.startswith('"'):
            try:
                return json.loads(val)
            except json.JSONDecodeError:
                pass
            
        # Try number
        try:
            if '.' in val:
                return float(val)
            return int(val)
        except ValueError:
            pass
            
        # String
        return val

    def _parse_value(self, val: str) -> Any:
        """
        Parse a cell value. Handles primitives and delegates complex types.
        """
        val = val.strip()
        
        # Booleans
        if val == 'T':
            return True
        if val == 'F':
            return False
        
        # Null
        if val == 'null':
            return None
        
        # Quoted string (JSON style) - must check BEFORE delimiter check
        if val.startswith('"'):
            try:
                return json.loads(val)
            except json.JSONDecodeError:
                pass
        
        # Check for ZON-style nested structures (braced)
        if val.startswith('{') or val.startswith('['):
            return self._parse_zon_node(val)
            
        # Try number
        try:
            if '.' in val:
                return float(val)
            return int(val)
        except ValueError:
            pass
            
        # Double-encoded JSON string fallback (legacy support or explicit JSON)
        if val.startswith('"') and val.endswith('"'):
             try:
                 # It might be a JSON string that was double-quoted
                 # e.g. "foo,bar" -> CSV: """foo,bar""" -> unquoted: "foo,bar"
                 # If it looks like a JSON string, try to parse it
                 return json.loads(val)
             except json.JSONDecodeError:
                 pass

        return val

    def _unflatten(self, d: Dict) -> Dict:
        """
        Unflatten dictionary with dotted keys.
        
        Works with depth-limited flattening - handles both:
        - Dot notation: "meta.timestamp" -> {"meta": {"timestamp": ...}}
        - JSON objects: "meta.context" with value {"ip": "...", "user_agent": "..."}
        - Array indices: "items.0.id" -> {"items": [{"id": ...}]}
        
        Args:
            d: Flattened dictionary
            
        Returns:
            Nested dictionary
        """
        result = {}
        
        for key, value in d.items():
            # Check if key has dot notation
            if '.' not in key:
                # Simple key, just assign
                result[key] = value
                continue
                
            parts = key.split('.')
            target = result
            
            # Navigate/create nested structure
            for i, part in enumerate(parts[:-1]):
                next_part = parts[i + 1]
                
                # Check if next part is a number (array index)
                if next_part.isdigit():
                    idx = int(next_part)
                    
                    # Create array if needed
                    if part not in target:
                        target[part] = []
                    
                    # Extend array to accommodate index
                    while len(target[part]) <= idx:
                        target[part].append({})
                    
                    # Move into the indexed element
                    target = target[part][idx]
                    # Skip the numeric index in the path
                    parts.pop(i + 1)
                    break
                else:
                    # Regular nested object
                    if part not in target:
                        target[part] = {}
                    
                    # Only navigate deeper if it's a dict (not an already-parsed JSON object)
                    if isinstance(target[part], dict):
                        target = target[part]
                    else:
                        # Already has a value, can't navigate deeper
                        break
            
            # Set the final value
            final_key = parts[-1]
            if not final_key.isdigit():  # Don't use numeric index as key
                target[final_key] = value
        
        return result


def decode(data: str) -> Any:
    """
    Convenience function to decode ZON v8.0 format to original data.
    
    Args:
        data: ZON-encoded string
        
    Returns:
        Decoded data
    """
    return ZonDecoder().decode(data)
