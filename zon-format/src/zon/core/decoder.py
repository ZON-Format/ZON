"""ZON Decoder - Compact hybrid format decoder with table support.

Provides decoding of ZON format strings into Python data structures,
supporting table reconstruction, sparse data, and type coercion.
"""

import json
import re
from typing import List, Dict, Any, Optional, Tuple, Union
from .constants import (
    TABLE_MARKER, META_SEPARATOR,
    MAX_DOCUMENT_SIZE, MAX_LINE_LENGTH, MAX_ARRAY_LENGTH, MAX_OBJECT_KEYS, MAX_NESTING_DEPTH
)
from .exceptions import ZonDecodeError
from ..schema.inference import TypeInferrer
from .utils import parse_value

class ZonDecoder:
    """Decodes ZON format strings into Python data structures.
    
    Handles parsing of ZON's hybrid format including metadata headers,
    tables (standard, delta, sparse), and inline object notation.
    """
    
    def __init__(self, strict: bool = True, type_coercion: bool = False):
        """Initialize the ZON decoder.
        
        Args:
            strict: If True, enforces strict validation of table structure
            type_coercion: If True, attempts to coerce types based on inference
        """
        self.strict = strict
        self.type_coercion = type_coercion
        self.current_line = 0
        self.type_inferrer = TypeInferrer()

    def decode(self, zon_str: str, **kwargs) -> Any:
        """Decode a ZON string into a Python object.
        
        Args:
            zon_str: The ZON string to decode
            **kwargs: Optional overrides for strict and type_coercion
            
        Returns:
            Decoded Python object (dict, list, or primitive)
        """
        strict = kwargs.get('strict', self.strict)
        type_coercion = kwargs.get('type_coercion', self.type_coercion)
        
        original_strict = self.strict
        original_type_coercion = self.type_coercion
        
        if 'strict' in kwargs:
            self.strict = strict
        if 'type_coercion' in kwargs:
            self.type_coercion = type_coercion
            
        try:
            return self._decode_internal(zon_str)
        finally:
            self.strict = original_strict
            self.type_coercion = original_type_coercion

    def _decode_internal(self, zon_str: str) -> Any:
        """Internal decoding logic handling line-by-line parsing.
        
        Args:
            zon_str: ZON string to decode
            
        Returns:
            Decoded object
            
        Raises:
            ZonDecodeError: If decoding fails or limits are exceeded
        """
        if not zon_str:
            return {}

        if len(zon_str) > MAX_DOCUMENT_SIZE:
            raise ZonDecodeError(
                f"Document size exceeds maximum ({MAX_DOCUMENT_SIZE} bytes)",
                code='E301'
            )

        lines = zon_str.split('\n')
        if not lines:
            return {}

        if len(lines) == 1 and lines[0].strip().startswith('['):
            return self._parse_zon_node(lines[0])

        metadata: Dict[str, Any] = {}
        tables: Dict[str, Dict] = {}
        current_table: Optional[Dict] = None
        current_table_name: Optional[str] = None
        pending_dictionaries: Dict[str, List[str]] = {}

        for line_idx, line in enumerate(lines):
            self.current_line = line_idx + 1
            trimmed_line = line.rstrip()

            if len(trimmed_line) > MAX_LINE_LENGTH:
                raise ZonDecodeError(
                    f"Line length exceeds maximum ({MAX_LINE_LENGTH} chars)",
                    code='E302',
                    line=self.current_line
                )

            if not trimmed_line:
                if current_table is not None and current_table['row_index'] < current_table['expected_rows']:
                    pass
                else:
                    continue

            if trimmed_line.startswith(TABLE_MARKER):
                current_table_name, current_table = self._parse_table_header(trimmed_line)
                current_table['dictionaries'] = pending_dictionaries.copy()
                pending_dictionaries = {}
                tables[current_table_name] = current_table
                continue

            processed_as_row = False
            if current_table is not None and current_table['row_index'] < current_table['expected_rows']:
                row = self._parse_table_row(trimmed_line, current_table)
                current_table['rows'].append(row)

                if current_table['row_index'] >= current_table['expected_rows']:
                    current_table = None
                processed_as_row = True

            if not processed_as_row:
                sep_index = self._find_delimiter(trimmed_line, META_SEPARATOR)
                if sep_index != -1:
                    key = trimmed_line[:sep_index].strip()
                    val = trimmed_line[sep_index + 1:].strip()

                    dict_match = re.match(r'^(.+)\[(\d+)\]$', key)
                    if dict_match:
                        col = dict_match.group(1)
                        vals = self._split_by_delimiter(val, ',')
                        parsed_vals = [str(parse_value(v)) for v in vals]
                        pending_dictionaries[col] = parsed_vals
                        continue

                    if val.startswith(TABLE_MARKER):
                        _, table_info = self._parse_table_header(val)
                        current_table_name = key
                        current_table = table_info
                        current_table['dictionaries'] = pending_dictionaries.copy()
                        pending_dictionaries = {}
                        tables[current_table_name] = current_table
                    else:
                        current_table = None
                        
                        if val.startswith('{') or val.startswith('['):
                             metadata[key] = self._parse_zon_node(val)
                        else:
                             metadata[key] = parse_value(val)
                
                elif trimmed_line.endswith('}') or trimmed_line.endswith(']'):
                     match = re.match(r'^([a-zA-Z0-9_\-\.]+)(\{|\[)', trimmed_line)
                     if match:
                         key = match.group(1)
                         val_start = match.start(2)
                         val = trimmed_line[val_start:]
                         metadata[key] = self._parse_zon_node(val)

        for table_name, table in tables.items():
            if self.strict and len(table['rows']) != table['expected_rows']:
                raise ZonDecodeError(
                    f"Row count mismatch in table '{table_name}': expected {table['expected_rows']}, got {len(table['rows'])}",
                    code='E001',
                    context=f"Table: {table_name}"
                )

            metadata[table_name] = self._reconstruct_table(table)

        result = self._unflatten(metadata)

        if len(result) == 1 and 'data' in result and isinstance(result['data'], list):
            return result['data']

        return result

    def _parse_table_header(self, line: str) -> Tuple[str, Dict]:
        """Parse a table header line.
        
        Supports various header formats including named tables, anonymous tables,
        and legacy formats.
        
        Args:
            line: Header line string
            
        Returns:
            Tuple of (table_name, table_info_dict)
            
        Raises:
            ZonDecodeError: If header format is invalid
        """
        v2_named_pattern = r'^@(\w+)\((\d+)\)(\[\w+\])*:(.*)$'
        v2_named_match = re.match(v2_named_pattern, line)

        if v2_named_match:
            table_name = v2_named_match.group(1)
            count = int(v2_named_match.group(2))
            omitted_str = v2_named_match.group(3) or ''
            cols_str = v2_named_match.group(4)
            return table_name, self._create_table_info(count, omitted_str, cols_str)

        v2_value_pattern = r'^@\((\d+)\)(\[\w+\])*:(.*)$'
        v2_value_match = re.match(v2_value_pattern, line)

        if v2_value_match:
            count = int(v2_value_match.group(1))
            omitted_str = v2_value_match.group(2) or ''
            cols_str = v2_value_match.group(3)
            return 'data', self._create_table_info(count, omitted_str, cols_str)

        v2_pattern = r'^@(\d+)(\[\w+\])*:(.*)$'
        v2_match = re.match(v2_pattern, line)

        if v2_match:
            count = int(v2_match.group(1))
            omitted_str = v2_match.group(2) or ''
            cols_str = v2_match.group(3)
            return 'data', self._create_table_info(count, omitted_str, cols_str)

        v1_pattern = r'^@(\w+)\((\d+)\):(.*)$'
        v1_match = re.match(v1_pattern, line)

        if v1_match:
            table_name = v1_match.group(1)
            count = int(v1_match.group(2))
            cols_str = v1_match.group(3)
            return table_name, self._create_table_info(count, '', cols_str)

        raise ZonDecodeError(f"Invalid table header: {line}")

    def _create_table_info(self, count: int, omitted_str: str, cols_str: str) -> Dict:
        """Create a dictionary holding table state and metadata.
        
        Args:
            count: Expected row count
            omitted_str: String containing omitted column definitions
            cols_str: String containing column definitions
            
        Returns:
            Table info dictionary
        """
        omitted_cols = []
        if omitted_str:
            for m in re.finditer(r'\[(\w+)\]', omitted_str):
                omitted_cols.append(m.group(1))

        if not cols_str:
            raw_cols = []
        else:
            raw_cols = [c.strip() for c in cols_str.split(',')]
        cols = []
        delta_cols = set()

        for rc in raw_cols:
            if rc.endswith(':delta'):
                col_name = rc[:-6]
                delta_cols.add(col_name)
                cols.append(col_name)
            else:
                cols.append(rc)

        return {
            'cols': cols,
            'omitted_cols': omitted_cols,
            'rows': [],
            'prev_vals': {col: None for col in cols},
            'row_index': 0,
            'expected_rows': count,
            'delta_cols': delta_cols,
            'dictionaries': {}
        }

    def _parse_table_row(self, line: str, table: Dict) -> Dict:
        """Parse a single table row.
        
        Handles standard values, delta encoding, dictionary lookups, and sparse fields.
        
        Args:
            line: Row string
            table: Table info dictionary
            
        Returns:
            Parsed row dictionary
            
        Raises:
            ZonDecodeError: If field count mismatch in strict mode
        """
        tokens = self._split_by_delimiter(line, ',')
        
        core_field_count = len(tokens)
        
        if self.strict and core_field_count < len(table['cols']):
             raise ZonDecodeError(
                f"Field count mismatch on row {table['row_index'] + 1}: expected {len(table['cols'])} fields, got {core_field_count}",
                code='E002',
                line=self.current_line,
                context=line[:50] + ('...' if len(line) > 50 else '')
            )

        while len(tokens) < len(table['cols']):
            tokens.append('')

        row: Dict[str, Any] = {}
        token_idx = 0

        for col in table['cols']:
            if token_idx < len(tokens):
                tok = tokens[token_idx]
                
                if col in table['delta_cols']:
                    val = parse_value(tok)
                    if table['row_index'] > 0:
                        prev = table['prev_vals'][col]
                        if isinstance(val, (int, float)) and isinstance(prev, (int, float)):
                            val = prev + val
                    table['prev_vals'][col] = val
                    if val is not None or tok.strip().lower() == 'null':
                        row[col] = val
                else:
                    if col in table['dictionaries']:
                        val = parse_value(tok)
                        if isinstance(val, int) and 0 <= val < len(table['dictionaries'][col]):
                            v = parse_value(table['dictionaries'][col][val])
                            row[col] = v
                        else:
                            v = self._parse_zon_node(tok)
                            if v is not None or tok.strip().lower() == 'null':
                                row[col] = v
                    else:
                        v = self._parse_zon_node(tok)
                        if v is not None or tok.strip().lower() == 'null':
                            row[col] = v
                
                token_idx += 1

        while token_idx < len(tokens):
            tok = tokens[token_idx]
            if ':' in tok and not self._is_url(tok) and not self._is_timestamp(tok):
                colon_idx = tok.index(':')
                key = tok[:colon_idx].strip()
                val = tok[colon_idx + 1:].strip()
                if re.match(r'^[a-zA-Z0-9_\-\.]+$', key):
                    row[key] = self._parse_zon_node(val)
            token_idx += 1

        if table['omitted_cols']:
            for col in table['omitted_cols']:
                row[col] = table['row_index'] + 1

        table['row_index'] += 1
        return row

    def _is_url(self, s: str) -> bool:
        """Check if string looks like a URL."""
        return s.startswith('http://') or s.startswith('https://') or s.startswith('/')

    def _is_timestamp(self, s: str) -> bool:
        """Check if string looks like a timestamp."""
        return bool(re.match(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}', s)) or bool(re.match(r'^\d{2}:\d{2}:\d{2}', s))

    def _reconstruct_table(self, table: Dict) -> List[Dict]:
        """Reconstruct full table from table info and rows."""
        return [self._unflatten(row) for row in table['rows']]

    def _parse_zon_node(self, text: str, depth: int = 0) -> Any:
        """Parse a ZON node (object, array, or primitive).
        
        Args:
            text: String to parse
            depth: Current nesting depth
            
        Returns:
            Parsed Python object
            
        Raises:
            ZonDecodeError: If nesting depth or size limits exceeded
        """
        if depth > MAX_NESTING_DEPTH:
            raise ZonDecodeError(f'Maximum nesting depth exceeded ({MAX_NESTING_DEPTH})')

        trimmed = text.strip()
        if not trimmed:
            return None

        if trimmed.startswith('{') and trimmed.endswith('}'):
            content = trimmed[1:-1].strip()
            if not content:
                return {}

            obj: Dict[str, Any] = {}
            pairs = self._split_by_delimiter(content, ',')

            if len(pairs) > MAX_OBJECT_KEYS:
                raise ZonDecodeError(
                    f"Object key count exceeds maximum ({MAX_OBJECT_KEYS} keys)",
                    code='E304'
                )

            for pair in pairs:
                match = re.match(r'^([a-zA-Z0-9_\-\.]+)(\{|\[)', pair)
                if match:
                    key_str = match.group(1)
                    val_str = pair[match.end(1):]
                    key = parse_value(key_str)
                    val = self._parse_zon_node(val_str, depth + 1)
                    obj[key] = val
                    continue

                if ':' not in pair:
                    continue

                colon_pos = self._find_delimiter(pair, ':')
                if colon_pos == -1:
                    continue

                key_str = pair[:colon_pos].strip()
                val_str = pair[colon_pos + 1:].strip()

                key = parse_value(key_str)
                val = self._parse_zon_node(val_str, depth + 1)
                obj[key] = val

            return obj

        if trimmed.startswith('[') and trimmed.endswith(']'):
            content = trimmed[1:-1].strip()
            if not content:
                return []

            items = self._split_by_delimiter(content, ',')

            if len(items) > MAX_ARRAY_LENGTH:
                raise ZonDecodeError(
                    f"Array length exceeds maximum ({MAX_ARRAY_LENGTH} items)",
                    code='E303'
                )

            return [self._parse_zon_node(item, depth + 1) for item in items]

        return parse_value(trimmed)

    def _find_delimiter(self, text: str, delim: str) -> int:
        """Find index of delimiter, respecting quotes and nesting.
        
        Args:
            text: Text to search
            delim: Delimiter character
            
        Returns:
            Index of delimiter or -1 if not found
        """
        in_quote = False
        quote_char = None
        depth = 0

        i = 0
        while i < len(text):
            char = text[i]
            if char == '\\' and i + 1 < len(text):
                i += 2
                continue

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
            i += 1
        return -1

    def _split_by_delimiter(self, text: str, delim: str) -> List[str]:
        """Split text by delimiter, respecting quotes and nesting.
        
        Args:
            text: Text to split
            delim: Delimiter character
            
        Returns:
            List of split parts
        """
        if not text:
            return ['']

        parts: List[str] = []
        current: List[str] = []
        in_quote = False
        quote_char = None
        depth = 0

        i = 0
        while i < len(text):
            char = text[i]
            if char == '\\' and i + 1 < len(text):
                current.append(char)
                current.append(text[i + 1])
                i += 2
                continue

            if char == '"':
                in_quote = not in_quote
                current.append(char)
            elif not in_quote:
                if char in ['{', '[']:
                    depth += 1
                    current.append(char)
                elif char in ['}', ']']:
                    depth -= 1
                    current.append(char)
                elif char == delim and depth == 0:
                    parts.append(''.join(current))
                    current = []
                else:
                    current.append(char)
            else:
                current.append(char)
            i += 1

        parts.append(''.join(current))

        return parts

    def _unflatten(self, d: Dict) -> Dict:
        """Expand dot-notation keys into nested dictionaries/lists.
        
        Args:
            d: Dictionary with potentially flat keys
            
        Returns:
            Nested dictionary structure
        """
        result: Any = {}

        for key, value in d.items():
            if '.' not in key:
                result[key] = value
                continue

            parts = key.split('.')
            if any(p in ['__proto__', 'constructor', 'prototype'] for p in parts):
                continue

            target: Any = result
            for i, part in enumerate(parts[:-1]):
                next_part = parts[i + 1]

                if next_part.isdigit():
                    idx = int(next_part)
                    if part not in target:
                        target[part] = []
                    while len(target[part]) <= idx:
                        target[part].append({})
                    target = target[part][idx]
                    parts.pop(i + 1)
                    break
                else:
                    if part not in target:
                        target[part] = {}
                    if isinstance(target[part], dict):
                        target = target[part]
                    else:
                        break

            final_key = parts[-1]
            if not final_key.isdigit():
                target[final_key] = value

        return result

def decode(data: str, strict: bool = True, options: Dict[str, bool] = None) -> Any:
    """Decode ZON format string (convenience function).
    
    Args:
        data: ZON string to decode
        strict: If True, enforces strict validation
        options: Optional dict with decoding options
        
    Returns:
        Decoded Python object
    """
    opts = options or {}
    return ZonDecoder(strict=strict, type_coercion=opts.get('type_coercion', False)).decode(data)
