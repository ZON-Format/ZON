"""ZON Encoder - Compact hybrid format encoder with table optimization.

Provides encoding of Python data structures to ZON format with support for:
- Table-based compression for homogenous data
- Delta encoding for sequential numeric values
- Dictionary compression for repeated string values
- Sparse encoding for columns with missing values
- Type coercion for consistent data representation
"""

import json
import re
import math
from typing import List, Dict, Any, Tuple, Optional, Set, Union
from .constants import (
    TABLE_MARKER, META_SEPARATOR, GAS_TOKEN, LIQUID_TOKEN, 
    DEFAULT_ANCHOR_INTERVAL
)
from .exceptions import ZonEncodeError
from ..schema.inference import TypeInferrer
from .utils import quote_string
from .types import SparseMode
from ..llm.optimizer import LLMOptimizer

class ZonEncoder:
    """Encodes Python data structures to ZON format.
    
    The encoder automatically selects optimal encoding strategies based on
    data structure and patterns, including table compression, delta encoding,
    dictionary compression, and sparse encoding.
    """
    
    def __init__(
        self, 
        anchor_interval: int = DEFAULT_ANCHOR_INTERVAL,
        enable_dict_compression: bool = True,
        enable_type_coercion: bool = False,
        use_long_booleans: bool = False
    ):
        """Initialize the ZON encoder.
        
        Args:
            anchor_interval: Interval for anchor points in streams
            enable_dict_compression: Enable dictionary compression for repeated values
            enable_type_coercion: Enable type coercion for string values
            use_long_booleans: Use 'true'/'false' instead of 'T'/'F' for LLM clarity
        """
        self.anchor_interval = anchor_interval
        self._safe_str_re = re.compile(r'^[a-zA-Z0-9_\-\.]+$')
        self.enable_dict_compression = enable_dict_compression
        self.enable_type_coercion = enable_type_coercion
        self.use_long_booleans = use_long_booleans
        self.type_inferrer = TypeInferrer()

    def encode(self, data: Any) -> str:
        """Encode data to ZON format.
        
        Automatically selects the optimal encoding strategy based on data
        structure. For homogeneous lists of objects, encodes as table. For
        irregular data or deeply nested structures, uses inline notation.
        
        Args:
            data: Python data structure to encode
            
        Returns:
            ZON-encoded string
        """
        stream_data, metadata, stream_key = self._extract_primary_stream(data)

        if not stream_data and (not metadata or len(metadata) == 0):
            if isinstance(data, (dict, list)):
                return self._format_zon_node(data)
            return json.dumps(data, separators=(',', ':'), ensure_ascii=False)

        output: List[str] = []

        if isinstance(data, list) and len(data) > 0 and all(isinstance(item, dict) and not isinstance(item, list) for item in data):
            irregularity_score = self._calculate_irregularity(data)
            
            if irregularity_score > 0.6:
                return self._format_zon_node(data)

        final_stream_key = stream_key
        if stream_data and stream_key is None:
            final_stream_key = "data"

        if metadata and len(metadata) > 0:
            output.extend(self._write_metadata(metadata))

        if stream_data and final_stream_key:
            if output:
                output.append("")
            output.extend(self._write_table(stream_data, final_stream_key))

        return "\n".join(output)

    def _extract_primary_stream(self, data: Any) -> Tuple[Optional[List], Dict, Optional[str]]:
        """Extract the primary stream data from input.
        
        For lists of objects, returns the list as the stream. For dicts containing
        a large list of objects, extracts that list as the stream and other keys
        as metadata.
        
        Args:
            data: Input data structure
            
        Returns:
            Tuple of (stream_data, metadata, stream_key)
        """
        if isinstance(data, list):
            if len(data) > 0 and isinstance(data[0], dict) and data[0] is not None:
                return data, {}, None
            return None, {}, None

        if isinstance(data, dict):
            candidates: List[Tuple[str, List, int]] = []
            
            for k, v in data.items():
                if isinstance(v, list) and len(v) > 0:
                    if isinstance(v[0], dict) and not isinstance(v[0], list):
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
        """Write metadata lines in key:value format.
        
        Args:
            metadata: Dictionary of metadata to encode
            
        Returns:
            List of encoded metadata lines
        """
        lines: List[str] = []
        sorted_keys = sorted(metadata.keys())
        
        for key in sorted_keys:
            val = metadata[key]
            
            if isinstance(val, (dict, list)) and val is not None:
                val_str = self._format_zon_node(val)
                if val_str.startswith('{') or val_str.startswith('['):
                    lines.append(f"{key}{val_str}")
                else:
                    lines.append(f"{key}{META_SEPARATOR}{val_str}")
            else:
                val_str = self._format_value(val)
                lines.append(f"{key}{META_SEPARATOR}{val_str}")

        return lines

    def _analyze_optimal_sparse_mode(self, values: List[Any]) -> SparseMode:
        """Analyze values to determine optimal sparse encoding mode.
        
        Args:
            values: List of values to analyze
            
        Returns:
            Recommended SparseMode
        """
        if len(values) < 5:
            return SparseMode.NONE

        is_numeric = True
        for val in values:
            if not isinstance(val, (int, float)) or isinstance(val, bool):
                is_numeric = False
                break
        
        if is_numeric:
            return SparseMode.DELTA

        return SparseMode.NONE

    def _encode_delta_column(self, values: List[Union[int, float]]) -> str:
        """Encode numeric values using delta encoding.
        
        Args:
            values: List of numeric values
            
        Returns:
            Delta-encoded string representation
        """
        if not values:
            return ''
        
        deltas: List[str] = [str(values[0])]
        for i in range(1, len(values)):
            delta = values[i] - values[i - 1]
            if isinstance(delta, float):
                delta = round(delta, 10)
                if delta.is_integer():
                    delta = int(delta)
            
            deltas.append(f"+{delta}" if delta >= 0 else str(delta))
        
        return "".join(deltas)

    def _write_table(self, stream: List[Dict], key: str) -> List[str]:
        """Write a table from a stream of dict objects.
        
        Analyzes the data structure and selects the optimal encoding strategy:
        dictionary compression, delta encoding, sparse encoding, or standard table.
        
        Args:
            stream: List of dict objects to encode as a table
            key: Table key/name
            
        Returns:
            List of ZON table lines
        """
        if not stream:
            return []

        lines: List[str] = []
        flat_stream = [self._flatten(row, '', '.', 5) for row in stream]

        all_keys_set: Set[str] = set()
        for d in flat_stream:
            all_keys_set.update(d.keys())
        cols = sorted(list(all_keys_set))

        if self.enable_type_coercion:
            for col in cols:
                values = [row.get(col) for row in flat_stream]
                inferred = self.type_inferrer.infer_column_type(values)
                
                if inferred.get('coercible'):
                    for row in flat_stream:
                        if col in row and row[col] is not None:
                            row[col] = self.type_inferrer.coerce(row[col], inferred)

        dictionaries = self._detect_dictionaries(flat_stream, cols) if self.enable_dict_compression else {}

        if dictionaries:
            return self._write_dictionary_table(flat_stream, cols, dictionaries, len(stream), key)

        column_stats = self._analyze_column_sparsity(flat_stream, cols)
        core_columns = [c['name'] for c in column_stats if c['presence'] >= 0.7]
        optional_columns = [c['name'] for c in column_stats if c['presence'] < 0.7]

        delta_columns: List[str] = []
        regular_core_columns: List[str] = []
        
        for col in core_columns:
            values = [row.get(col) for row in flat_stream]
            mode = self._analyze_optimal_sparse_mode(values)
            if mode == SparseMode.DELTA:
                delta_columns.append(col)
            else:
                regular_core_columns.append(col)

        if delta_columns:
            return self._write_delta_table(flat_stream, regular_core_columns, delta_columns, optional_columns, len(stream), key)

        use_sparse_encoding = len(optional_columns) > 0

        if use_sparse_encoding:
            return self._write_sparse_table(flat_stream, core_columns, optional_columns, len(stream), key)
        else:
            return self._write_standard_table(flat_stream, cols, len(stream), key)

    def _write_delta_table(
        self,
        flat_stream: List[Dict],
        regular_cols: List[str],
        delta_cols: List[str],
        optional_cols: List[str],
        row_count: int,
        key: str
    ) -> List[str]:
        """Write a table with delta-encoded numeric columns.
        
        Args:
            flat_stream: Flattened stream data
            regular_cols: Regular columns (not delta-encoded)
            delta_cols: Columns to encode with delta encoding
            optional_cols: Sparse/optional columns  
            row_count: Number of rows
            key: Table key/name
            
        Returns:
            List of ZON table lines with delta encoding
        """
        lines: List[str] = []
        
        if key and key != 'data':
            header = f"{key}{META_SEPARATOR}{TABLE_MARKER}({row_count})"
        else:
            header = f"{TABLE_MARKER}{row_count}"

        delta_defs = [f"{c}:delta" for c in delta_cols]
        all_cols = delta_defs + regular_cols
        
        header += f"{META_SEPARATOR}{','.join(all_cols)}"
        lines.append(header)

        for i in range(row_count):
            row = flat_stream[i]
            tokens: List[str] = []

            for col in delta_cols:
                val = row.get(col)
                if i == 0:
                    tokens.append(str(val))
                else:
                    prev = flat_stream[i-1].get(col)
                    diff = val - prev
                    if isinstance(diff, float):
                        diff = round(diff, 10)
                        if diff.is_integer():
                            diff = int(diff)
                    tokens.append(f"+{diff}" if diff >= 0 else str(diff))

            for col in regular_cols:
                if col not in row:
                    tokens.append('')
                elif row[col] is None:
                    tokens.append('null')
                else:
                    tokens.append(self._format_value(row[col]))

            for col in optional_cols:
                if col in row and row[col] is not None:
                    val = self._format_value(row[col])
                    tokens.append(f"{col}:{val}")

            lines.append(','.join(tokens))

        return lines

    def _write_standard_table(self, flat_stream: List[Dict], cols: List[str], row_count: int, key: str) -> List[str]:
        """Write a standard table without special encoding.
        
        Args:
            flat_stream: Flattened stream data
            cols: Column names
            row_count: Number of rows
            key: Table key/name
            
        Returns:
            List of ZON table lines
        """
        lines: List[str] = []
        omitted_cols = self._analyze_sequential_columns(flat_stream, cols)

        if key and key != 'data':
            header = f"{key}{META_SEPARATOR}{TABLE_MARKER}({row_count})"
        else:
            header = f"{TABLE_MARKER}{row_count}"

        if omitted_cols:
            header += ''.join(f"[{c}]" for c in omitted_cols)

        visible_cols = [c for c in cols if c not in omitted_cols]
        header += f"{META_SEPARATOR}{','.join(visible_cols)}"
        lines.append(header)

        for row in flat_stream:
            tokens: List[str] = []
            for col in visible_cols:
                if col not in row:
                    tokens.append('')
                elif row[col] is None:
                    tokens.append('null')
                else:
                    tokens.append(self._format_value(row[col]))
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
        """Write a table with sparse encoding for optional columns.
        
        Core columns appear in every row. Optional columns only appear when
        present, using key:value notation.
        
        Args:
            flat_stream: Flattened stream data
            core_columns: Columns present in most rows (>= 70%)
            optional_columns: Columns present in few rows (< 70%)
            row_count: Number of rows
            key: Table key/name
            
        Returns:
            List of ZON table lines with sparse encoding
        """
        lines: List[str] = []
        omitted_cols = self._analyze_sequential_columns(flat_stream, core_columns)

        if key and key != 'data':
            header = f"{key}{META_SEPARATOR}{TABLE_MARKER}({row_count})"
        else:
            header = f"{TABLE_MARKER}{row_count}"

        if omitted_cols:
            header += ''.join(f"[{c}]" for c in omitted_cols)

        visible_core_columns = [c for c in core_columns if c not in omitted_cols]
        header += f"{META_SEPARATOR}{','.join(visible_core_columns)}"
        lines.append(header)

        for row in flat_stream:
            tokens: List[str] = []

            for col in visible_core_columns:
                tokens.append(self._format_value(row.get(col)))

            for col in optional_columns:
                if col in row:
                    val = self._format_value(row[col])
                    tokens.append(f"{col}:{val}")

            lines.append(','.join(tokens))

        return lines

    def _analyze_column_sparsity(self, data: List[Dict], cols: List[str]) -> List[Dict]:
        """Analyze how frequently each column appears in the data.
        
        Args:
            data: List of dict objects
            cols: Column names to analyze
            
        Returns:
            List of dicts with 'name' and 'presence' (0.0 to 1.0) for each column
        """
        result = []
        for col in cols:
            presence_count = sum(1 for row in data if col in row and row[col] is not None)
            result.append({
                'name': col,
                'presence': presence_count / len(data) if data else 0
            })
        return result

    def _analyze_sequential_columns(self, data: List[Dict], cols: List[str]) -> List[str]:
        """Analyze columns for sequential patterns (placeholder implementation).
        
        Args:
            data: List of dict objects
            cols: Column names to analyze
            
        Returns:
            List of column names with sequential patterns (currently always empty)
        """
        return []

    def _detect_dictionaries(self, data: List[Dict], cols: List[str]) -> Dict[str, List[str]]:
        """Detect columns suitable for dictionary compression.
        
        Identifies string columns with high repetition rates where dictionary
        encoding (replacing values with indices) would save tokens.
        
        Args:
            data: List of dict objects
            cols: Column names to analyze
            
        Returns:
            Dict mapping column names to their unique value lists (dictionaries)
        """
        dictionaries: Dict[str, List[str]] = {}

        for col in cols:
            values = [row.get(col) for row in data if isinstance(row.get(col), str)]
            if len(values) < len(data) * 0.8:
                continue

            unique_values = sorted(list(set(values)))
            if not values:
                continue
                
            repetition_rate = 1 - (len(unique_values) / len(values))
            avg_length = sum(len(v) for v in unique_values) / len(unique_values)

            current_tokens = len(values) * avg_length
            ref_cost = 1 if len(unique_values) < 10 else (2 if len(unique_values) < 100 else 3)
            
            values_length = sum(len(v) for v in unique_values)
            definition_overhead = len(col) + 4 + values_length + (len(unique_values) - 1)
            
            dict_tokens = values_length + (len(values) * ref_cost) + definition_overhead
            savings = (current_tokens - dict_tokens) / current_tokens if current_tokens > 0 else 0

            threshold = 0.1 if len(values) < 20 else 0.2

            if savings > threshold and len(unique_values) < len(values) / 2 and len(unique_values) <= 50:
                dictionaries[col] = unique_values

        return dictionaries

    def _write_dictionary_table(
        self,
        flat_stream: List[Dict],
        cols: List[str],
        dictionaries: Dict[str, List[str]],
        row_count: int,
        key: str
    ) -> List[str]:
        """Write a table with dictionary-compressed columns.
        
        Dictionary columns are replaced with numeric indices, with dictionary
        definitions appearing before the table header.
        
        Args:
            flat_stream: Flattened stream data
            cols: All column names
            dictionaries: Dict mapping column names to value lists
            row_count: Number of rows
            key: Table key/name
            
        Returns:
            List of ZON lines (dictionary definitions + table)
        """
        lines: List[str] = []

        for col, values in dictionaries.items():
            lines.append(f"{col}[{len(values)}]:{','.join(values)}")

        dict_cols = list(dictionaries.keys())
        regular_cols = [c for c in cols if c not in dictionaries]
        all_cols = dict_cols + regular_cols

        if key and key != 'data':
            header = f"{key}{META_SEPARATOR}{TABLE_MARKER}({row_count})"
        else:
            header = f"{TABLE_MARKER}{row_count}"
        header += f"{META_SEPARATOR}{','.join(all_cols)}"
        lines.append(header)

        for row in flat_stream:
            tokens: List[str] = []

            for col in dict_cols:
                value = row.get(col)
                if value in dictionaries[col]:
                    index = dictionaries[col].index(value)
                    tokens.append(str(index))
                else:
                    tokens.append(self._format_value(value))

            for col in regular_cols:
                if col not in row:
                    tokens.append('')
                elif row[col] is None:
                    tokens.append('null')
                else:
                    tokens.append(self._format_value(row[col]))

            lines.append(','.join(tokens))

        return lines

    def _calculate_irregularity(self, data: List[Dict]) -> float:
        """Calculate irregularity score for a list of objects.
        
        Measures how inconsistent object structures are based on key overlap.
        Higher scores (closer to 1.0) indicate very different structures.
        
        Args:
            data: List of dict objects
            
        Returns:
            Irregularity score from 0.0 (identical structures) to 1.0 (no overlap)
        """
        if not data:
            return 0.0

        all_keys: Set[str] = set()
        key_sets: List[Set[str]] = []
        
        for item in data:
            keys = set(item.keys())
            key_sets.append(keys)
            all_keys.update(keys)

        total_keys = len(all_keys)
        if total_keys == 0:
            return 0.0

        total_overlap = 0.0
        comparisons = 0

        for i in range(len(key_sets)):
            for j in range(i + 1, len(key_sets)):
                keys1 = key_sets[i]
                keys2 = key_sets[j]
                
                shared = len(keys1 & keys2)
                union = len(keys1) + len(keys2) - shared
                similarity = shared / union if union > 0 else 1.0
                
                total_overlap += similarity
                comparisons += 1

        if comparisons == 0:
            return 0.0

        avg_similarity = total_overlap / comparisons
        irregularity = 1 - avg_similarity

        return irregularity

    def _format_zon_node(self, val: Any, visited: Optional[set] = None) -> str:
        """Format a value as an inline ZON node (object or array notation).
        
        Args:
            val: Value to format
            visited: Set of visited object IDs for circular reference detection
            
        Returns:
            ZON inline notation string
            
        Raises:
            ZonEncodeError: If circular reference is detected
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
            keys = sorted(val.keys())
            items: List[str] = []
            for k in keys:
                v = val[k]
                k_str = str(k)
                if re.search(r'[,:\{\}\[\]"]', k_str):
                    k_str = json.dumps(k_str)

                v_str = self._format_zon_node(v, visited.copy())
                
                if v_str.startswith('{') or v_str.startswith('['):
                    items.append(f"{k_str}{v_str}")
                else:
                    items.append(f"{k_str}:{v_str}")
            return "{" + ",".join(items) + "}"
            
        if isinstance(val, list):
            if not val:
                return "[]"
            return "[" + ",".join(self._format_zon_node(item, visited.copy()) for item in val) + "]"
            
        if val is None:
            return "null"
        if val is True:
            return "T"
        if val is False:
            return "F"
        if isinstance(val, (int, float)):
            return self._format_value(val)

        s = str(val)

        if '\n' in s or '\r' in s:
            return json.dumps(s, ensure_ascii=False)

        if self.type_inferrer._is_iso_date(s):
            return s

        if self._needs_type_protection(s):
            return json.dumps(s, ensure_ascii=False)

        if not s.strip():
            return json.dumps(s, ensure_ascii=False)

        if re.search(r'[,\{\}\[\]"]', s):
            return json.dumps(s, ensure_ascii=False)

        return s

    def _format_value(self, val: Any) -> str:
        """Format a value for use in ZON table cells or metadata.
        
        Args:
            val: Value to format
            
        Returns:
            ZON-formatted string representation
        """
        if val is None:
            return "null"
        if isinstance(val, bool):
            if self.use_long_booleans:
                return "true" if val else "false"
            else:
                return "T" if val else "F"
        if isinstance(val, (int, float)):
            if isinstance(val, float):
                if not math.isfinite(val):
                    return "null"
            
            
            if isinstance(val, int):
                return str(val)
            
            if isinstance(val, float):
                if val.is_integer():
                    return f"{int(val)}.0"
                else:
                    s = str(val)
                    if 'e' in s.lower():
                        parts = re.split(r'[eE]', s)
                        mantissa = float(parts[0])
                        exponent = int(parts[1])
                        
                        if exponent >= 0:
                            result = mantissa * (10 ** exponent)
                            s = str(result)
                            if '.' not in s:
                                s += '.0'
                        else:
                            pass
                    return s

        if isinstance(val, (list, dict)):
            return self._format_zon_node(val)

        s = str(val)

        if '\n' in s or '\r' in s:
            return json.dumps(s, ensure_ascii=False)

        if self.type_inferrer._is_iso_date(s):
            return s

        if self._needs_type_protection(s):
            return quote_string(s)

        if self._needs_quotes(s):
            return quote_string(s)

        return s

    def _needs_type_protection(self, s: str) -> bool:
        """Check if a string needs quoting to prevent misinterpretation.
        
        Args:
            s: String to check
            
        Returns:
            True if the string would be misinterpreted without quotes
        """
        s_lower = s.lower()
        
        if s_lower in ['t', 'f', 'true', 'false', 'null', 'none', 'nil']:
            return True
        
        if s in [GAS_TOKEN, LIQUID_TOKEN]:
            return True
        
        if s.strip() != s:
            return True
        
        if any(ord(c) <= 0x1F for c in s):
            return True

        if re.match(r'^-?\d+$', s):
            return True

        if re.match(r'^-?\d+\.\d+$', s):
            return True

        if re.match(r'^-?\d+(\.\d+)?[eE][+-]?\d+$', s):
            return True
        
        if s and (s[0].isdigit() or s[-1].isdigit()):
            try:
                num = float(s)
                if str(num) == s:
                    return True
            except ValueError:
                pass

        return False

    def _needs_quotes(self, s: str) -> bool:
        """Check if a string needs quoting in ZON format.
        
        Args:
            s: String to check
            
        Returns:
            True if the string requires quotes
        """
        if not s:
            return True

        if s in ['T', 'F', 'null', GAS_TOKEN, LIQUID_TOKEN]:
            return True

        if re.match(r'^-?\d+$', s):
            return True
        try:
            float(s)
            return True
        except ValueError:
            pass

        if s.strip() != s:
            return True

        if re.match(r'^[+-]?(\d|\.\d)', s):
             return True

        if re.search(r'[,:}\n\r\t"\[\]|;]', s):
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
        """Flatten nested dict to dot-notation keys.
        
        Args:
            d: Dictionary to flatten
            parent: Parent key prefix
            sep: Separator for nested keys
            max_depth: Maximum nesting depth to flatten
            current_depth: Current depth in recursion
            visited: Set of visited object IDs for circular reference detection
            
        Returns:
            Flattened dictionary with dot-notation keys
            
        Raises:
            ZonEncodeError: If circular reference is detected
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

            if isinstance(v, dict) and v and v is not None and not isinstance(v, list) and current_depth < max_depth:
                flattened = self._flatten(v, new_key, sep, max_depth, current_depth + 1, visited.copy())
                items.extend(flattened.items())
            else:
                items.append((new_key, v))
        return dict(items)


def encode(data: Any, anchor_interval: int = DEFAULT_ANCHOR_INTERVAL, options: Dict[str, bool] = None) -> str:
    """Encode data to ZON format (convenience function).
    
    Args:
        data: Python data structure to encode
        anchor_interval: Interval for anchor points in streams
        options: Optional dict with encoding options (e.g., {'type_coercion': True})
        
    Returns:
        ZON-encoded string
    """
    opts = options or {}
    return ZonEncoder(
        anchor_interval, 
        enable_dict_compression=True, 
        enable_type_coercion=opts.get('type_coercion', False)
    ).encode(data)

def encode_llm(data: Any, context: Dict[str, Any]) -> str:
    """Encode data optimized for LLM consumption.
    
    Applies LLM-specific optimizations based on the task context, such as
    field ordering for better comprehension and type coercion for consistency.
    
    Args:
        data: Python data structure to encode
        context: Context dict with 'task' key ('generation', 'analysis', 'retrieval')
        
    Returns:
        ZON-encoded string optimized for LLM processing
    """
    processed_data = data

    if context.get('task') in ('generation', 'analysis'):
        optimizer = LLMOptimizer()
        if isinstance(data, list):
            processed_data = optimizer.optimize_field_order(data)
        elif isinstance(data, dict) and data is not None:
            new_data = data.copy()
            for key in new_data:
                if isinstance(new_data[key], list):
                    new_data[key] = optimizer.optimize_field_order(new_data[key])
            processed_data = new_data

    enable_dict = True
    enable_type_coercion = True

    if context.get('task') == 'retrieval':
        enable_type_coercion = True

    encoder = ZonEncoder(
        DEFAULT_ANCHOR_INTERVAL, 
        enable_dict_compression=enable_dict, 
        enable_type_coercion=enable_type_coercion
    )
    return encoder.encode(processed_data)
