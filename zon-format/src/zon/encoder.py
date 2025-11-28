"""
ZON Encoder v1.0.3 - Compact Hybrid Format

Breaking changes from v1.0.2:
- Compact header syntax (@count: instead of @data(count):)
- Sequential ID omission ([col] notation) - DISABLED for LLM accuracy
- Sparse table encoding for semi-uniform data
- Adaptive format selection based on data complexity
- Circular reference detection
- Improved number formatting (NaN/Infinity → null, no scientific notation)
- Better string handling for newlines and empty strings
"""

import json
import re
import math
from typing import List, Dict, Any, Tuple, Optional, Set
from .constants import (
    TABLE_MARKER, META_SEPARATOR, GAS_TOKEN, LIQUID_TOKEN, 
    DEFAULT_ANCHOR_INTERVAL
)
from .exceptions import ZonEncodeError


class ZonEncoder:
    def __init__(self, anchor_interval: int = DEFAULT_ANCHOR_INTERVAL):
        self.anchor_interval = anchor_interval
        self._safe_str_re = re.compile(r'^[a-zA-Z0-9_\-\.]+$')

    def encode(self, data: Any) -> str:
        """
        Encode data to ZON v1.0.3 ClearText format.
        
        Args:
            data: Input data (list or dict)
            
        Returns:
            ZON-encoded string in ClearText format
            
        Raises:
            ZonEncodeError: If circular reference detected
        """
        # 1. Root Promotion: Separate metadata from stream
        stream_data, metadata, stream_key = self._extract_primary_stream(data)

        # Fallback for simple/empty data
        if not stream_data and (not metadata or len(metadata) == 0):
            return json.dumps(data, separators=(',', ':'))

        output: List[str] = []

        # Special case: Detect schema uniformity for lists of dicts
        if isinstance(data, list) and len(data) > 0 and all(isinstance(item, dict) and not isinstance(item, list) for item in data):
            # Calculate irregularity score
            irregularity_score = self._calculate_irregularity(data)
            
            # If highly irregular (>60% keys differ), use list format
            if irregularity_score > 0.6:
                return self._format_zon_node(data)
            
            # Otherwise use table format (even if semi-uniform)
            # The sparse table encoding will handle optional fields efficiently

        # 1. Root Promotion: Extract primary stream into table
        # If stream_key is None (pure list input), use default key
        final_stream_key = stream_key
        if stream_data and stream_key is None:
            final_stream_key = "data"

        # 3. Write Metadata (YAML-like)
        if metadata and len(metadata) > 0:
            output.extend(self._write_metadata(metadata))

        # 4. Write Table (if multi-item stream exists)
        if stream_data and final_stream_key:
            if output:  # Add blank line separator
                output.append("")
            output.extend(self._write_table(stream_data, final_stream_key))

        return "\n".join(output)

    def _extract_primary_stream(self, data: Any) -> Tuple[Optional[List], Dict, Optional[str]]:
        """
        Root Promotion Algorithm: Find the main table in the JSON.
        """
        if isinstance(data, list):
            # Only promote to table if it contains objects
            if len(data) > 0 and isinstance(data[0], dict) and data[0] is not None:
                return data, {}, None
            return None, {}, None  # Treat as simple value

        if isinstance(data, dict):
            # Find largest list of objects
            candidates: List[Tuple[str, List, int]] = []
            
            for k, v in data.items():
                if isinstance(v, list) and len(v) > 0:
                    # Check if list contains objects (tabular candidate)
                    if isinstance(v[0], dict) and not isinstance(v[0], list):
                        # Score = Rows * Cols
                        score = len(v) * len(v[0].keys())
                        candidates.append((k, v, score))

            if candidates:
                candidates.sort(key=lambda x: x[2], reverse=True)
                key, stream, _ = candidates[0]
                meta: Dict[str, Any] = {}
                
                for k, v in data.items():
                    if k != key:
                        meta[k] = v
                
                return stream, meta, key

        return None, data if isinstance(data, dict) else {}, None

    def _write_metadata(self, metadata: Dict) -> List[str]:
        """
        Write metadata in YAML-like format.
        """
        lines: List[str] = []
        flattened = self._flatten(metadata)

        sorted_keys = sorted(flattened.keys())
        for key in sorted_keys:
            value = flattened[key]
            val_str = self._format_value(value)
            lines.append(f"{key}{META_SEPARATOR}{val_str}")

        return lines

    def _write_table(self, stream: List[Dict], key: str) -> List[str]:
        """
        Write table in v1.0.3 compact format with adaptive encoding.
        """
        if not stream or len(stream) == 0:
            return []

        lines: List[str] = []
        flat_stream = [self._flatten(row) for row in stream]

        # Get all column names
        all_keys_set: Set[str] = set()
        for d in flat_stream:
            all_keys_set.update(d.keys())
        cols = sorted(list(all_keys_set))

        # Analyze column sparsity
        column_stats = self._analyze_column_sparsity(flat_stream, cols)
        core_columns = [c['name'] for c in column_stats if c['presence'] >= 0.7]
        optional_columns = [c['name'] for c in column_stats if c['presence'] < 0.7]

        # Decide encoding strategy
        use_sparse_encoding = len(optional_columns) > 0 and len(optional_columns) <= 5

        if use_sparse_encoding:
            return self._write_sparse_table(flat_stream, core_columns, optional_columns, len(stream), key)
        else:
            return self._write_standard_table(flat_stream, cols, len(stream), key)

    def _write_standard_table(self, flat_stream: List[Dict], cols: List[str], row_count: int, key: str) -> List[str]:
        """
        Write standard compact table (v1.0.3 format).
        """
        lines: List[str] = []

        # Detect sequential columns to omit (DISABLED in v1.0.3 for LLM accuracy)
        omitted_cols = self._analyze_sequential_columns(flat_stream, cols)

        # Build compact header: key:@(count)[omitted]: columns or @count[omitted]: columns
        if key and key != 'data':
            header = f"{key}{META_SEPARATOR}{TABLE_MARKER}({row_count})"
        else:
            header = f"{TABLE_MARKER}{row_count}"

        if omitted_cols:
            header += ''.join(f"[{c}]" for c in omitted_cols)

        # Filter out omitted columns
        visible_cols = [c for c in cols if c not in omitted_cols]
        header += f"{META_SEPARATOR}{','.join(visible_cols)}"
        lines.append(header)

        # Write rows (without omitted columns)
        for row in flat_stream:
            tokens: List[str] = []
            for col in visible_cols:
                val = row.get(col)
                # Use "null" for undefined/null to preserve type
                if val is None:
                    tokens.append('null')
                else:
                    tokens.append(self._format_value(val))
            lines.append(','.join(tokens))

        return lines

    def _write_sparse_table(
        self,
        flat_stream: List[Dict],
        core_columns: List[str],
        optional_columns: List[str],
        row_count: int,
        key: str
    ) -> List[str]:
        """
        Write sparse table for semi-uniform data (v1.0.3).
        """
        lines: List[str] = []

        # Detect sequential columns in core columns
        omitted_cols = self._analyze_sequential_columns(flat_stream, core_columns)

        # Build header: key:@(count)[omitted]: core_columns
        if key and key != 'data':
            header = f"{key}{META_SEPARATOR}{TABLE_MARKER}({row_count})"
        else:
            header = f"{TABLE_MARKER}{row_count}"

        if omitted_cols:
            header += ''.join(f"[{c}]" for c in omitted_cols)

        visible_core_columns = [c for c in core_columns if c not in omitted_cols]
        header += f"{META_SEPARATOR}{','.join(visible_core_columns)}"
        lines.append(header)

        # Write rows: core columns + optional fields as key:value
        for row in flat_stream:
            tokens: List[str] = []

            # Core columns (fixed positions)
            for col in visible_core_columns:
                tokens.append(self._format_value(row.get(col)))

            # Optional columns (append as key:value if present)
            for col in optional_columns:
                if col in row and row[col] is not None:
                    val = self._format_value(row[col])
                    tokens.append(f"{col}:{val}")

            lines.append(','.join(tokens))

        return lines

    def _analyze_column_sparsity(self, data: List[Dict], cols: List[str]) -> List[Dict]:
        """
        Analyze column sparsity to determine core vs optional.
        A column is considered "present" if it exists in the row (even if None).
        """
        result = []
        for col in cols:
            # Count rows where the column KEY exists (regardless of value)
            presence_count = sum(1 for row in data if col in row)
            result.append({
                'name': col,
                'presence': presence_count / len(data) if data else 0
            })
        return result

    def _analyze_sequential_columns(self, data: List[Dict], cols: List[str]) -> List[str]:
        """
        Detect sequential columns (1, 2, 3, ..., N) for omission.
        
        NOTE: Disabled in v1.0.3 to improve LLM retrieval accuracy.
        Implicit columns like [id] were being missed by LLMs.
        Now all columns are explicit.
        """
        return []  # Disable omission for now

    def _analyze_columns(self, data: List[Dict], cols: List[str]) -> Dict[str, Dict]:
        """
        Analyze columns for compression opportunities.
        """
        analysis: Dict[str, Dict] = {}

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
                    diffs = [nums[i] - nums[i - 1] for i in range(1, len(nums))]
                    unique_diffs = set(diffs)
                    if len(unique_diffs) == 1:
                        result['is_sequential'] = True
                        result['step'] = list(unique_diffs)[0]
                except:
                    pass

            # Check for repetition
            if len(vals) > 1:
                try:
                    unique = set(json.dumps(v, sort_keys=True) for v in vals)
                    if len(unique) < len(vals):
                        result['has_repetition'] = True
                except:
                    pass

            analysis[col] = result

        return analysis

    def _calculate_irregularity(self, data: List[Dict]) -> float:
        """
        Calculate irregularity score for array of objects.
        Returns 0.0 (perfectly uniform) to 1.0 (completely different schemas).
        """
        if not data:
            return 0.0

        # Get all unique keys across all objects
        all_keys: Set[str] = set()
        key_sets: List[Set[str]] = []
        
        for item in data:
            keys = set(item.keys())
            key_sets.append(keys)
            all_keys.update(keys)

        total_keys = len(all_keys)
        if total_keys == 0:
            return 0.0

        # Calculate key overlap score
        # For each pair of objects, measure how many keys they share
        total_overlap = 0.0
        comparisons = 0

        for i in range(len(key_sets)):
            for j in range(i + 1, len(key_sets)):
                keys1 = key_sets[i]
                keys2 = key_sets[j]
                
                # Count shared keys
                shared = len(keys1 & keys2)
                
                # Jaccard similarity: shared / (size1 + size2 - shared)
                union = len(keys1) + len(keys2) - shared
                similarity = shared / union if union > 0 else 1.0
                
                total_overlap += similarity
                comparisons += 1

        if comparisons == 0:
            return 0.0  # Single object

        avg_similarity = total_overlap / comparisons
        irregularity = 1 - avg_similarity  # 0 = all same, 1 = all different

        return irregularity

    def _csv_quote(self, s: str) -> str:
        """
        Quote a string for CSV (RFC 4180).
        Escapes quotes by doubling them (" -> "") and wraps in double quotes.
        """
        escaped = s.replace('"', '""')
        return f'"{escaped}"'

    def _format_zon_node(self, val: Any, visited: Optional[set] = None) -> str:
        """
        Format nested structure using YAML-like ZON syntax:
        - Dict: {key:val,key:val}
        - List: [val,val]
        """
        if visited is None:
            visited = set()
            
        if isinstance(val, (dict, list)):
            val_id = id(val)
            if val_id in visited:
                raise ZonEncodeError('Circular reference detected')
            visited.add(val_id)

        if isinstance(val, dict):
            if not val:
                return "{}"
            items: List[str] = []
            for k, v in val.items():
                # Format key (unquoted if simple)
                k_str = str(k)
                # Keys are usually simple, but quote if needed
                if any(c in k_str for c in [',', ':', '{', '}', '[', ']', '"']):
                    k_str = json.dumps(k_str)

                # Format value recursively
                v_str = self._format_zon_node(v, visited.copy())
                items.append(f"{k_str}:{v_str}")
            return "{" + ",".join(items) + "}"
            
        elif isinstance(val, list):
            if not val:
                return "[]"
            return "[" + ",".join(self._format_zon_node(item, visited.copy()) for item in val) + "]"
            
        # Primitives
        if val is None:
            return "null"
        if val is True:
            return "T"
        if val is False:
            return "F"
        if isinstance(val, (int, float)):
            # Handle special values
            if isinstance(val, float):
                if math.isnan(val) or math.isinf(val):
                    return "null"
                    
            # Preserve exact numeric representation
            if isinstance(val, float) and not isinstance(val, bool):
                s = str(val)
                # Ensure floats always have decimal point
                if '.' not in s and 'e' not in s.lower():
                    s += '.0'
                return s
            else:
                return str(val)
            
        # String handling - only quote if necessary
        s = str(val)

        # CRITICAL FIX: Always JSON-stringify strings with newlines to prevent line breaks in ZON
        if '\n' in s or '\r' in s:
            return json.dumps(s)

        # Quote empty strings or whitespace-only strings to prevent them being parsed as null
        if not s.strip():
            return json.dumps(s)

        # Quote strings that look like reserved words or numbers to prevent type confusion
        if s in ['T', 'F', 'null', 'true', 'false']:
            return json.dumps(s)

        # Quote if it looks like a number (to preserve string type)
        if re.match(r'^-?\d+(\.\d+)?$', s):
            return json.dumps(s)

        # Quote if contains structural delimiters
        if any(c in s for c in [',', ':', '{', '}', '[', ']', '"']):
            return json.dumps(s)

        return s

    def _format_value(self, val: Any) -> str:
        """
        Format a value with minimal quoting.
        v1.0.3 Optimization: Smart date detection and relaxed string quoting
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
            # Handle special values
            if isinstance(val, float):
                if not math.isfinite(val):
                    return "null"  # NaN, Infinity, -Infinity → null
            
            # Canonical number formatting - avoid scientific notation
            if isinstance(val, int):
                return str(val)
            
            # Float handling
            if isinstance(val, float) and val.is_integer():
                # Float that looks like integer (e.g., 42.0)
                s = str(val)
                if 'e' in s.lower():
                    # Convert from scientific notation
                    return str(int(val)) + '.0'
                return s
            
            # For floats with fractional parts
            s = str(val)
            
            # Check if it's in scientific notation
            if 'e' in s.lower():
                # Convert to fixed-point notation
                parts = s.lower().split('e')
                mantissa = float(parts[0])
                exponent = int(parts[1])
                
                if exponent >= 0:
                    # Positive exponent - multiply
                    result = mantissa * (10 ** exponent)
                    s = str(result)
                    if '.' not in s:
                        s += '.0'
                else:
                    # Negative exponent - use format
                    s = format(val, f'.{abs(exponent) + 6}f').rstrip('0')
                    # Make sure we have at least one decimal place
                    if s.endswith('.'):
                        s += '0'
            
            return s

        if isinstance(val, (list, dict)):
            # Use ZON-style formatting for complex types
            # ZON structures are self-delimiting ({}, []) and should NOT be quoted
            # unless they are meant to be strings (which is handled by string path)
            return self._format_zon_node(val)

        # String formatting with v1.0.3 optimizations
        s = str(val)

        # CRITICAL FIX: Always JSON-stringify strings with newlines to prevent line breaks in ZON
        if '\n' in s or '\r' in s:
            return self._csv_quote(json.dumps(s))

        # OPTIMIZATION 1: ISO Date Detection
        # Dates like "2025-01-01" or "2025-01-01T10:00:00Z" are unambiguous
        # No need to quote - LLMs recognize ISO 8601 format universally
        if self._is_iso_date(s):
            return s

        # OPTIMIZATION 2: Smarter Number Detection
        # Only quote actual numbers, not complex patterns like IPs or alphanumeric IDs
        needs_type_protection = self._needs_type_protection(s)

        if needs_type_protection:
            # Wrap in quotes (JSON style) then CSV quote
            return self._csv_quote(json.dumps(s))

        # Check if it needs CSV quoting (delimiters)
        if self._needs_quotes(s):
            return self._csv_quote(s)

        return s

    def _is_iso_date(self, s: str) -> bool:
        """
        Check if string is an ISO 8601 date/datetime.
        Examples: "2025-01-01", "2025-01-01T10:00:00Z", "2025-01-01T10:00:00+05:30"
        """
        # ISO 8601 full datetime with timezone
        if re.match(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(Z|[+-]\d{2}:\d{2})$', s):
            return True
        # ISO 8601 date only
        if re.match(r'^\d{4}-\d{2}-\d{2}$', s):
            return True
        # Simple time
        if re.match(r'^\d{2}:\d{2}:\d{2}$', s):
            return True
        return False

    def _needs_type_protection(self, s: str) -> bool:
        """
        Determine if string needs type protection (quoting to preserve as string).
        v1.0.3: More precise - only protect actual numbers, not complex patterns.
        """
        s_lower = s.lower()
        
        # Reserved words
        if s_lower in ['t', 'f', 'true', 'false', 'null', 'none', 'nil']:
            return True
        
        # Gas/Liquid tokens
        if s in [GAS_TOKEN, LIQUID_TOKEN]:
            return True
        
        # Leading/trailing whitespace must be preserved
        if s.strip() != s:
            return True
        
        # Control characters need JSON escaping
        if any(c in s for c in ['\n', '\r', '\t']):
            return True

        # Pure integer: "123" or "-456"
        if re.match(r'^-?\d+$', s):
            return True

        # Pure decimal: "3.14" or "-2.5"
        if re.match(r'^-?\d+\.\d+$', s):
            return True

        # Scientific notation: "1e5", "2.5e-3"
        if re.match(r'^-?\d+(\.\d+)?[eE][+-]?\d+$', s):
            return True

        # OPTIMIZATION 2: Complex patterns DON'T need quoting
        # Examples that should NOT be quoted:
        # - "192.168.1.1" (IP address - dots distinguish from number)
        # - "u123" (alphanumeric ID - letter prefix)
        # - "v1.0.3" (version string)
        # - "2025-01-01" (date - handled by _is_iso_date above)
        
        # If it starts/ends with digit but has non-numeric chars, check carefully
        if s and (s[0].isdigit() or s[-1].isdigit()):
            # Try parsing - if it parses cleanly and matches, it's a number
            try:
                num = float(s)
                if str(num) == s:
                    return True  # It's actually a pure number like "3.14159"
            except ValueError:
                pass
            # Otherwise it's a complex pattern like "192.168.1.1" - NO PROTECTION

        return False

    def _needs_quotes(self, s: str) -> bool:
        """
        Determine if a string needs quotes.
        """
        if not s:
            return True

        # Reserved tokens need quoting
        if s in ['T', 'F', 'null', GAS_TOKEN, LIQUID_TOKEN]:
            return True

        # Quote if it looks like a number (to preserve string type)
        if re.match(r'^-?\d+$', s):
            return True
        try:
            float(s)
            return True
        except ValueError:
            pass

        # Quote if leading/trailing whitespace (preserved)
        if s.strip() != s:
            return True

        # Only quote if contains delimiter or control chars
        if any(c in s for c in [',', '\n', '\r', '\t', '"', '[', ']', '|', ';', ':']):
            return True

        return False

    def _flatten(
        self,
        d: Any,
        parent: str = '',
        sep: str = '.',
        max_depth: int = 0,
        current_depth: int = 0,
        visited: Optional[set] = None
    ) -> Dict:
        """
        Flatten nested dictionary with depth limit.
        """
        if visited is None:
            visited = set()
            
        if isinstance(d, dict):
            d_id = id(d)
            if d_id in visited:
                raise ZonEncodeError('Circular reference detected')
            visited.add(d_id)

        if not isinstance(d, dict) or d is None or isinstance(d, list):
            return {parent: d} if parent else {}

        items: List[Tuple[str, Any]] = []
        for k, v in d.items():
            new_key = f"{parent}{sep}{k}" if parent else k

            # DEPTH LIMIT: Stop flattening beyond max_depth
            if isinstance(v, dict) and v is not None and not isinstance(v, list) and current_depth < max_depth:
                # Recursively flatten this level
                flattened = self._flatten(v, new_key, sep, max_depth, current_depth + 1, visited.copy())
                items.extend(flattened.items())
            else:
                # Keep as-is: primitives or objects beyond depth limit
                items.append((new_key, v))

        return dict(items)


def encode(data: Any, anchor_interval: int = DEFAULT_ANCHOR_INTERVAL) -> str:
    """
    Convenience function to encode data to ZON v1.0.3 format.
    
    Args:
        data: Input data
        anchor_interval: Interval for anchor rows (legacy, unused in v1.0.3)
        
    Returns:
        ZON-encoded string in ClearText format
        
    Raises:
        ZonEncodeError: If circular reference detected
    """
    return ZonEncoder(anchor_interval).encode(data)
