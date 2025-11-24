"""
ZON Encoder v8.0 - ClearText Format

This encoder produces clean, document-style output with YAML-like metadata
and CSV-like tables using @table syntax.
"""

import json
import re
import csv
import io
from collections import Counter
from typing import List, Dict, Any, Tuple, Optional
from .constants import *


class ZonEncoder:
    def __init__(self, anchor_interval: int = DEFAULT_ANCHOR_INTERVAL):
        self.anchor_interval = anchor_interval
        self._safe_str_re = re.compile(r'^[a-zA-Z0-9_\-\.]+$')

    def encode(self, data: Any) -> str:
        """
        Encode data to ZON v8.0 ClearText format.
        
        Args:
            data: Input data (list or dict)
            
        Returns:
            ZON-encoded string in ClearText format
        """
        # 1. Root Promotion: Separate metadata from stream
        stream_data, metadata, stream_key = self._extract_primary_stream(data)
        
        # Fallback for simple/empty data
        if not stream_data and not metadata:
            return json.dumps(data, separators=(',', ':'))

        output = []
        
        # Special case: Irregular schema detection for lists of dicts
        if isinstance(data, list) and data and all(isinstance(item, dict) for item in data):
            # Check if all records have the same keys
            all_keys = [set(item.keys()) for item in data]
            if len(set(frozenset(keys) for keys in all_keys)) > 1:
                # Irregular schema - encode as list of objects to preserve exact structure
                return self._format_zon_node(data)
        
        # 1. Root Promotion: Extract primary stream into table
        # If stream_key is None (pure list input), use default key
        if stream_data and stream_key is None:
            stream_key = "data"
        
        # 2. Singleton Bypass: Flatten 1-item lists to metadata
        # DISABLED: Conflicts with depth-limited flattening
        # TODO: Fix singleton bypass to work with depth limits
        # if stream_data and len(stream_data) == 1 and stream_key:
        #     # Flatten the single item into metadata with index notation
        #     item = stream_data[0]
        #     if isinstance(item, dict):
        #         flattened = self._flatten(item, parent=f"{stream_key}.0")
        #         metadata.update(flattened)
        #         stream_data = None
        
        # 3. Write Metadata (YAML-like)
        if metadata:
            output.extend(self._write_metadata(metadata))
        
        # 4. Write Table (if multi-item stream exists)
        if stream_data and stream_key:
            if output:  # Add blank line separator
                output.append("")
            output.extend(self._write_table(stream_data, stream_key))
        
        return "\n".join(output)

    def _extract_primary_stream(self, data) -> Tuple[Optional[List], Dict, Optional[str]]:
        """
        Root Promotion Algorithm: Find the main table in the JSON.
        
        Args:
            data: Input data
            
        Returns:
            (stream_data, metadata, stream_key)
        """
        if isinstance(data, list):
            return data, {}, None  # stream_key is None for pure lists
        
        if isinstance(data, dict):
            # Find largest list of objects
            candidates = []
            for k, v in data.items():
                if isinstance(v, list) and len(v) > 0:
                    # Check if list contains objects (tabular candidate)
                    if isinstance(v[0], dict):
                        # Score = Rows * Cols
                        score = len(v) * len(v[0].keys())
                        candidates.append((k, v, score))
            
            if candidates:
                candidates.sort(key=lambda x: x[2], reverse=True)
                key, stream, _ = candidates[0]
                meta = {k: v for k, v in data.items() if k != key}
                return stream, meta, key
        
        return None, data if isinstance(data, dict) else {}, None

    def _write_metadata(self, metadata: Dict) -> List[str]:
        """
        Write metadata in YAML-like format.
        
        Args:
            metadata: Dictionary of metadata
            
        Returns:
            List of formatted lines
        """
        lines = []
        flattened = self._flatten(metadata)
        
        for key, value in sorted(flattened.items()):
            val_str = self._format_value(value)
            lines.append(f"{key}{META_SEPARATOR}{val_str}")
        
        return lines

    def _write_table(self, stream: List[Dict], key: str) -> List[str]:
        """
        Write table in @table format with compression.
        
        Args:
            stream: List of records
            key: Table name
            
        Returns:
            List of formatted lines
        """
        if not stream:
            return []
        
        lines = []
        
        # Flatten all rows
        flat_stream = [self._flatten(row) for row in stream]
        
        # Get column names
        all_keys = set().union(*(d.keys() for d in flat_stream))
        cols = sorted(list(all_keys))
        
        # Get column names
        all_keys = set().union(*(d.keys() for d in flat_stream))
        cols = sorted(list(all_keys))
        
        # Write table header
        col_names = ",".join(cols)  # No space after comma for compactness
        lines.append(f"{TABLE_MARKER}{key}({len(stream)}){META_SEPARATOR}{col_names}")
        
        # Write rows
        for row in flat_stream:
            tokens = []
            
            for col in cols:
                val = row.get(col)
                # Explicit value only - no compression tokens
                tokens.append(self._format_value(val))
            
            lines.append(",".join(tokens))
        
        return lines

    def _analyze_columns(self, data: List[Dict], cols: List[str]) -> Dict:
        """
        Analyze columns for compression opportunities.
        
        Args:
            data: Flattened stream data
            cols: Column names
            
        Returns:
            Dictionary of column analysis
        """
        analysis = {}
        
        for col in cols:
            vals = [d.get(col) for d in data]
            
            result = {
                'is_sequential': False,
                'step': 1,
                'has_repetition': False
            }
            
            # Check for sequential numbers
            nums = [v for v in vals if isinstance(v, (int, float)) and not isinstance(v, bool)]
            if len(nums) == len(vals) and len(vals) > 1:
                try:
                    diffs = [nums[i] - nums[i-1] for i in range(1, len(nums))]
                    if len(set(diffs)) == 1:
                        result['is_sequential'] = True
                        result['step'] = diffs[0]
                except:
                    pass
            
            # Check for repetition
            if len(vals) > 1:
                try:
                    unique_count = len(set(json.dumps(v, sort_keys=True) for v in vals))
                    if unique_count < len(vals):
                        result['has_repetition'] = True
                except:
                    pass
            
            analysis[col] = result
        
        return analysis

    def _format_value(self, val: Any) -> str:
        """
        Format a value with minimal quoting.
        
        Args:
            val: Value to format
            
        Returns:
            Formatted string
        """
    def _csv_quote(self, s: str) -> str:
        """
        Quote a string for CSV (RFC 4180).
        
        Escapes quotes by doubling them (" -> "") and wraps in double quotes.
        """
        escaped = s.replace('"', '""')
        return f'"{escaped}"'

    def _format_value(self, val: Any) -> str:
        """
        Format a value with minimal quoting.
        
        Args:
            val: Value to format
            
        Returns:
            Formatted string
        """
    def _format_zon_node(self, val: Any) -> str:
        """
        Format nested structure using YAML-like ZON syntax:
        - Dict: {key:val,key:val}
        - List: [val,val]
        """
        if isinstance(val, dict):
            if not val:
                return "{}"
            items = []
            for k, v in val.items():
                # Format key (unquoted if simple)
                k_str = str(k)
                # Keys are usually simple, but quote if needed
                if any(c in k_str for c in [',', ':', '{', '}', '[', ']', '"']):
                    k_str = json.dumps(k_str)
                
                # Format value recursively
                v_str = self._format_zon_node(v)
                items.append(f"{k_str}:{v_str}")
            return "{" + ",".join(items) + "}"
            
        elif isinstance(val, list):
            if not val:
                return "[]"
            return "[" + ",".join(self._format_zon_node(item) for item in val) + "]"
            
        # Primitives
        if val is None:
            return "null"
        if val is True:
            return "T"
        if val is False:
            return "F"
        if isinstance(val, (int, float)):
            # Preserve exact numeric representation
            if isinstance(val, float):
                # Ensure floats always have decimal point
                s = str(val)
                # If it's a whole number float (e.g., 127.0), Python str() gives "127.0"
                # But for some reason it might strip it, so we ensure it
                if '.' not in s and 'e' not in s.lower():
                    s += '.0'
                return s
            else:
                return str(val)
            
        # String handling - only quote if necessary
        s = str(val)
        
        # Quote strings that look like reserved words or numbers to prevent type confusion
        if s in ['T', 'F', 'null', 'true', 'false']:
            return json.dumps(s)
            
        # Quote if it looks like a number (to preserve string type)
        if s.replace('.', '', 1).replace('-', '', 1).isdigit():
            return json.dumps(s)
            
        # Quote if contains structural delimiters
        if any(c in s for c in [',', ':', '{', '}', '[', ']', '"']):
             return json.dumps(s)
             
        return s

    def _format_value(self, val: Any) -> str:
        """
        Format a value with minimal quoting.
        
        Args:
            val: Value to format
            
        Returns:
            Formatted string
        """
        if val is None:
            return "null"
        if val is True:
            return "T"
        if val is False:
            return "F"
        if isinstance(val, bool):
            return "T" if val else "F"
        if isinstance(val, (int, float)):
            # Preserve exact numeric representation
            if isinstance(val, float):
                s = str(val)
                # Ensure decimal point for whole number floats
                if '.' not in s and 'e' not in s.lower():
                    s += '.0'
                return s
            else:
                return str(val)
        
        if isinstance(val, (list, dict)):
            # Use ZON-style formatting for complex types
            # This returns a string like "k:v|k:v" or "a;b"
            # This string might contain commas, so the WHOLE thing needs to be CSV-quoted
            zon_str = self._format_zon_node(val)
            if self._needs_quotes(zon_str):
                return self._csv_quote(zon_str)
            return zon_str
        
        # String formatting
        s = str(val)
        
        # Check if it looks like a number/bool/null (needs type protection)
        # These must be encoded as JSON strings ("...") so decoder sees quotes
        needs_type_protection = False
        if s in ['T', 'F', 'null', GAS_TOKEN, LIQUID_TOKEN]:
            needs_type_protection = True
        elif s.isdigit() or (s.startswith('-') and s[1:].isdigit()):
            needs_type_protection = True
        elif s.strip() != s: # Leading/trailing whitespace
            needs_type_protection = True
        else:
            try:
                float(s)
                needs_type_protection = True
            except ValueError:
                pass
                
        if needs_type_protection:
            # Wrap in quotes (JSON style) then CSV quote
            # s="123" -> json='"123"' -> csv='"""123"""'
            return self._csv_quote(json.dumps(s))
            
        # Check if it needs CSV quoting (delimiters)
        if self._needs_quotes(s):
            return self._csv_quote(s)
            
        return s

    def _needs_quotes(self, s: str) -> bool:
        """
        Determine if a string needs quotes.
        
        Minimal quoting rules:
        - Quote only if contains comma (the delimiter)
        - Quote if contains newline, tab, or quote char
        - Quote if is a reserved token (T, F, null, _, ^)
        - Quote if contains new bracketless delimiters (|, ;, :)
        
        Spaces are fine without quotes.
        
        Args:
            s: String to check
            
        Returns:
            True if quotes needed
        """
        if not s:
            return True
        
        # Reserved tokens need quoting
        if s in ['T', 'F', 'null', GAS_TOKEN, LIQUID_TOKEN]:
            return True
        
        # Quote if it looks like a number (to preserve string type)
        # Check for integer
        if s.isdigit() or (s.startswith('-') and s[1:].isdigit()):
            return True
        # Check for float
        try:
            float(s)
            return True
        except ValueError:
            pass
            
        # Quote if leading/trailing whitespace (preserved)
        if s.strip() != s:
            return True
        
        # Only quote if contains delimiter or control chars
        # Added |, ;, : for bracketless format
        if any(c in s for c in [',', '\n', '\r', '\t', '"', '[', ']', '|', ';', ':']):
            return True
        
        return False

    def _flatten(self, d: Any, parent: str = '', sep: str = '.', max_depth: int = 0, current_depth: int = 0) -> Dict:
        """
        Flatten nested dictionary with depth limit.
        
        Only flattens up to max_depth levels to prevent unreadable 100+ column tables.
        Nested objects beyond max_depth are kept as inline JSON.
        
        Args:
            d: Data to flatten
            parent: Parent key prefix
            sep: Separator for keys
            max_depth: Maximum flattening depth (1 = only top level)
            current_depth: Current recursion depth (internal)
            
        Returns:
            Flattened dictionary
        """
        if not isinstance(d, dict):
            return {parent: d} if parent else {}
        
        items = []
        for k, v in d.items():
            new_key = f"{parent}{sep}{k}" if parent else k
            
            # DEPTH LIMIT: Stop flattening beyond max_depth
            if isinstance(v, dict) and current_depth < max_depth:
                # Recursively flatten this level
                items.extend(self._flatten(v, new_key, sep, max_depth, current_depth + 1).items())
            else:
                # Keep as-is: primitives or objects beyond depth limit
                items.append((new_key, v))
        
        return dict(items)


def encode(data: Any, anchor_interval: int = DEFAULT_ANCHOR_INTERVAL) -> str:
    """
    Convenience function to encode data to ZON v8.0 format.
    
    Args:
        data: Input data
        anchor_interval: Interval for anchor rows (legacy, unused in v8.0)
        
    Returns:
        ZON-encoded string in ClearText format
    """
    return ZonEncoder(anchor_interval).encode(data)
