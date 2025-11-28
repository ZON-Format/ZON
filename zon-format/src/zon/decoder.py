"""
ZON Decoder v1.0.4 - Compact Hybrid Format

Supports both v1.x and v2.0.0 formats:
- v2.0: Compact headers (@count:), sequential ID reconstruction, sparse tables
- v1.x: Legacy format (@tablename(count):) for backward compatibility
- Strict mode with E001/E002 error codes
- Security limits (document size, line length, array length, object keys)
- Nesting depth limit
"""

import json
import re
import csv
import io
from typing import List, Dict, Any, Optional, Tuple
from .constants import (
    TABLE_MARKER, META_SEPARATOR,
    MAX_DOCUMENT_SIZE, MAX_LINE_LENGTH, MAX_ARRAY_LENGTH, MAX_OBJECT_KEYS, MAX_NESTING_DEPTH
)
from .exceptions import ZonDecodeError


class ZonDecoder:
    def __init__(self, strict: bool = True):
        """
        Initialize decoder.
        
        Args:
            strict: If True, validate table structure (row count, field count)
        """
        self.strict = strict
        self.current_line = 0

    def decode(self, zon_str: str) -> Any:
        """
        Decode ZON v1.0.4 ClearText format to original data structure.
        
        Args:
            zon_str: ZON-encoded string
            
        Returns:
            Decoded data (list or dict)
            
        Raises:
            ZonDecodeError: On validation errors or security limit violations
        """
        if not zon_str:
            return {}

        # Security: Check document size
        if len(zon_str) > MAX_DOCUMENT_SIZE:
            raise ZonDecodeError(
                f"Document size exceeds maximum ({MAX_DOCUMENT_SIZE} bytes)",
                code='E301'
            )

        lines = zon_str.strip().split('\n')
        if not lines:
            return {}

        # Special case: Root-level ZON list (irregular schema)
        # If entire input is a single line starting with [, it's a ZON list
        if len(lines) == 1 and lines[0].strip().startswith('['):
            return self._parse_zon_node(lines[0])

        # Main decode loop
        metadata: Dict[str, Any] = {}
        tables: Dict[str, Dict] = {}
        current_table: Optional[Dict] = None
        current_table_name: Optional[str] = None

        for line_idx, line in enumerate(lines):
            self.current_line = line_idx + 1
            trimmed_line = line.rstrip()

            # Security: Check line length
            if len(trimmed_line) > MAX_LINE_LENGTH:
                raise ZonDecodeError(
                    f"Line length exceeds maximum ({MAX_LINE_LENGTH} chars)",
                    code='E302',
                    line=self.current_line
                )

            # Skip blank lines
            if not trimmed_line:
                continue

            # Table header (Anonymous or Legacy): @...
            if trimmed_line.startswith(TABLE_MARKER):
                current_table_name, current_table = self._parse_table_header(trimmed_line)
                tables[current_table_name] = current_table

            # Table row (if we're in a table and haven't read all rows)
            elif current_table is not None and current_table['row_index'] < current_table['expected_rows']:
                row = self._parse_table_row(trimmed_line, current_table)
                current_table['rows'].append(row)

                # If we've read all rows, exit table mode
                if current_table['row_index'] >= current_table['expected_rows']:
                    current_table = None

            # Metadata line OR Named Table (v2.1): key: @...
            elif META_SEPARATOR in trimmed_line:
                sep_index = trimmed_line.index(META_SEPARATOR)
                key = trimmed_line[:sep_index].strip()
                val = trimmed_line[sep_index + 1:].strip()

                # Check if it's a named table start: users: @(5)...
                if val.startswith(TABLE_MARKER):
                    # Parse header from value part
                    _, table_info = self._parse_table_header(val)
                    current_table_name = key
                    current_table = table_info
                    tables[current_table_name] = current_table
                else:
                    current_table = None  # Exit table mode (safety)
                    metadata[key] = self._parse_value(val)

        # Recombine tables into metadata
        for table_name, table in tables.items():
            # Strict mode: validate row count
            if self.strict and len(table['rows']) != table['expected_rows']:
                raise ZonDecodeError(
                    f"Row count mismatch in table '{table_name}': expected {table['expected_rows']}, got {len(table['rows'])}",
                    code='E001',
                    context=f"Table: {table_name}"
                )

            metadata[table_name] = self._reconstruct_table(table)

        # Unflatten dotted keys
        result = self._unflatten(metadata)

        # Unwrap pure lists: if only key is 'data', return the list directly
        if len(result) == 1 and 'data' in result and isinstance(result['data'], list):
            return result['data']

        return result

    def _parse_table_header(self, line: str) -> Tuple[str, Dict]:
        """
        Parse table header line (supports v1.x and v2.0.0 formats).
        v2.0: @count[omitted]: cols or @count: cols
        v1.x: @tablename(count): cols
        """
        # Try v2.0 format with name: @name(count)[col][col]:columns
        v2_named_pattern = r'^@(\w+)\((\d+)\)(\[\w+\])*:(.+)$'
        v2_named_match = re.match(v2_named_pattern, line)

        if v2_named_match:
            table_name = v2_named_match.group(1)
            count = int(v2_named_match.group(2))
            omitted_str = v2_named_match.group(3) or ''
            cols_str = v2_named_match.group(4)

            # Parse omitted columns
            omitted_cols: List[str] = []
            if omitted_str:
                for m in re.finditer(r'\[(\w+)\]', omitted_str):
                    omitted_cols.append(m.group(1))

            cols = [c.strip() for c in cols_str.split(',')]

            return table_name, {
                'cols': cols,
                'omitted_cols': omitted_cols,
                'rows': [],
                'prev_vals': {col: None for col in cols},
                'row_index': 0,
                'expected_rows': count
            }

        # Try v2.1 format (anonymous/value): @(count)[col]:columns
        v2_value_pattern = r'^@\((\d+)\)(\[\w+\])*:(.+)$'
        v2_value_match = re.match(v2_value_pattern, line)

        if v2_value_match:
            count = int(v2_value_match.group(1))
            omitted_str = v2_value_match.group(2) or ''
            cols_str = v2_value_match.group(3)

            # Parse omitted columns
            omitted_cols = []
            if omitted_str:
                for m in re.finditer(r'\[(\w+)\]', omitted_str):
                    omitted_cols.append(m.group(1))

            cols = [c.strip() for c in cols_str.split(',')]

            return 'data', {
                'cols': cols,
                'omitted_cols': omitted_cols,
                'rows': [],
                'prev_vals': {col: None for col in cols},
                'row_index': 0,
                'expected_rows': count
            }

        # Try v2.0 format (anonymous): @count[col][col]:columns
        v2_pattern = r'^@(\d+)(\[\w+\])*:(.+)$'
        v2_match = re.match(v2_pattern, line)

        if v2_match:
            count = int(v2_match.group(1))
            omitted_str = v2_match.group(2) or ''
            cols_str = v2_match.group(3)

            # Parse omitted columns
            omitted_cols = []
            if omitted_str:
                for m in re.finditer(r'\[(\w+)\]', omitted_str):
                    omitted_cols.append(m.group(1))

            # Parse visible columns
            cols = [c.strip() for c in cols_str.split(',')]

            return 'data', {
                'cols': cols,
                'omitted_cols': omitted_cols,
                'rows': [],
                'prev_vals': {col: None for col in cols},
                'row_index': 0,
                'expected_rows': count
            }

        # Fallback to v1.x format: @tablename(count):cols
        v1_pattern = r'^@(\w+)\((\d+)\):(.+)$'
        v1_match = re.match(v1_pattern, line)

        if not v1_match:
            raise ZonDecodeError(f"Invalid table header: {line}")

        table_name = v1_match.group(1)
        count = int(v1_match.group(2))
        cols_str = v1_match.group(3)
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
        Parse a table row with v2.0 sparse encoding support.
        """
        tokens = self._split_by_delimiter(line, ',')

        # Strict mode: validate field count (before padding)
        core_field_count = len(tokens)
        sparse_field_count = 0

        # Count sparse fields (key:value after core fields)
        for i in range(len(table['cols']), len(tokens)):
            tok = tokens[i]
            if ':' in tok and not self._is_url(tok) and not self._is_timestamp(tok):
                sparse_field_count += 1

        # In strict mode, core fields must match column count (unless we have sparse fields)
        if self.strict and core_field_count < len(table['cols']) and sparse_field_count == 0:
            raise ZonDecodeError(
                f"Field count mismatch on row {table['row_index'] + 1}: expected {len(table['cols'])} fields, got {core_field_count}",
                code='E002',
                line=self.current_line,
                context=line[:50] + ('...' if len(line) > 50 else '')
            )

        # Pad if needed
        while len(tokens) < len(table['cols']):
            tokens.append('')

        row: Dict[str, Any] = {}
        token_idx = 0

        # Parse core columns
        for col in table['cols']:
            if token_idx < len(tokens):
                tok = tokens[token_idx]
                row[col] = self._parse_value(tok)
                token_idx += 1

        # Parse optional fields (v2.0 sparse encoding: key:value)
        while token_idx < len(tokens):
            tok = tokens[token_idx]
            if ':' in tok and not self._is_url(tok) and not self._is_timestamp(tok):
                # Try to parse as key:value
                colon_idx = tok.index(':')
                key = tok[:colon_idx].strip()
                val = tok[colon_idx + 1:].strip()

                # Validate key is a simple identifier
                if re.match(r'^[a-zA-Z_]\w*$', key):
                    row[key] = self._parse_value(val)
            token_idx += 1

        # Reconstruct omitted sequential columns (v2.0)
        if 'omitted_cols' in table and table['omitted_cols']:
            for col in table['omitted_cols']:
                row[col] = table['row_index'] + 1

        table['row_index'] += 1
        return row

    def _is_url(self, s: str) -> bool:
        """Check if string is a URL."""
        return s.startswith('http://') or s.startswith('https://') or s.startswith('/')

    def _is_timestamp(self, s: str) -> bool:
        """Check if string is a timestamp with colons."""
        return bool(re.match(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}', s)) or bool(re.match(r'^\d{2}:\d{2}:\d{2}', s))

    def _reconstruct_table(self, table: Dict) -> List[Dict]:
        """Reconstruct table from parsed rows."""
        return [self._unflatten(row) for row in table['rows']]

    def _parse_zon_node(self, text: str, depth: int = 0) -> Any:
        """
        Recursive parser for YAML-like ZON nested format.
        - Dict: {key:val,key:val}
        - List: [val,val]
        """
        if depth > MAX_NESTING_DEPTH:
            raise ZonDecodeError(f'Maximum nesting depth exceeded ({MAX_NESTING_DEPTH})')

        trimmed = text.strip()
        if not trimmed:
            return None

        # Dict: {k:v,k:v}
        if trimmed.startswith('{') and trimmed.endswith('}'):
            content = trimmed[1:-1].strip()
            if not content:
                return {}

            obj: Dict[str, Any] = {}
            # Split by comma, respecting nesting
            pairs = self._split_by_delimiter(content, ',')

            # Security: Check object key count
            if len(pairs) > MAX_OBJECT_KEYS:
                raise ZonDecodeError(
                    f"Object key count exceeds maximum ({MAX_OBJECT_KEYS} keys)",
                    code='E304'
                )

            for pair in pairs:
                if ':' not in pair:
                    continue

                # Find first unquoted colon
                colon_pos = self._find_delimiter(pair, ':')
                if colon_pos == -1:
                    continue

                key_str = pair[:colon_pos].strip()
                val_str = pair[colon_pos + 1:].strip()

                key = self._parse_primitive(key_str)
                val = self._parse_zon_node(val_str, depth + 1)
                obj[key] = val

            return obj

        # List: [v,v]
        if trimmed.startswith('[') and trimmed.endswith(']'):
            content = trimmed[1:-1].strip()
            if not content:
                return []

            items = self._split_by_delimiter(content, ',')

            # Security: Check array length
            if len(items) > MAX_ARRAY_LENGTH:
                raise ZonDecodeError(
                    f"Array length exceeds maximum ({MAX_ARRAY_LENGTH} items)",
                    code='E303'
                )

            return [self._parse_zon_node(item, depth + 1) for item in items]

        # Leaf node (primitive)
        return self._parse_primitive(trimmed)

    def _find_delimiter(self, text: str, delim: str) -> int:
        """Find first occurrence of delimiter outside quotes."""
        in_quote = False
        quote_char = None
        depth = 0

        i = 0
        while i < len(text):
            char = text[i]

            # Handle escaped characters
            if char == '\\' and i + 1 < len(text):
                i += 2  # Skip next char
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
        """Split text by delimiter, respecting quotes and nesting."""
        parts: List[str] = []
        current: List[str] = []
        in_quote = False
        quote_char = None
        depth = 0

        i = 0
        while i < len(text):
            char = text[i]

            # Handle escaped characters
            if char == '\\' and i + 1 < len(text):
                current.append(char)
                current.append(text[i + 1])
                i += 2
                continue

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
                    parts.append(''.join(current))
                    current = []
                else:
                    current.append(char)
            else:
                current.append(char)
            i += 1

        if current:
            parts.append(''.join(current))

        return parts

    def _parse_primitive(self, val: str) -> Any:
        """
        Parse a primitive value (T/F/null/number/string) without checking for ZON structure.
        """
        trimmed = val.strip()

        # Case-insensitive boolean and null handling
        val_lower = trimmed.lower()

        # Booleans
        if val_lower in ['t', 'true']:
            return True
        if val_lower in ['f', 'false']:
            return False

        # Null
        if val_lower in ['null', 'none', 'nil']:
            return None

        # Quoted string (JSON style)
        if trimmed.startswith('"'):
            try:
                return json.loads(trimmed)
            except json.JSONDecodeError:
                pass

        # Try number
        if trimmed:
            try:
                # Try integer first
                if '.' not in trimmed and 'e' not in trimmed.lower():
                    return int(trimmed)
                # Then float
                return float(trimmed)
            except ValueError:
                pass

        # String
        return trimmed

    def _parse_value(self, val: str) -> Any:
        """
        Parse a cell value. Handles primitives and delegates complex types.
        """
        trimmed = val.strip()

        # Quoted string (JSON style) - must check BEFORE primitives
        if trimmed.startswith('"'):
            try:
                decoded = json.loads(trimmed)
                # If decoded value is a string that looks like a ZON structure, parse it recursively
                if isinstance(decoded, str):
                    stripped = decoded.strip()
                    if stripped.startswith('{') or stripped.startswith('['):
                        return self._parse_zon_node(stripped)
                return decoded
            except json.JSONDecodeError:
                # Fallback: CSV unquoting for metadata values
                if trimmed.startswith('"') and trimmed.endswith('"'):
                    unquoted = trimmed[1:-1].replace('""', '"')

                    # Try to parse unquoted value as JSON
                    try:
                        decoded_unquoted = json.loads(unquoted)
                        # If it's a string, check if it's a ZON node (recursive)
                        if isinstance(decoded_unquoted, str):
                            stripped = decoded_unquoted.strip()
                            if stripped.startswith('{') or stripped.startswith('['):
                                return self._parse_zon_node(stripped, 0)
                        return decoded_unquoted
                    except json.JSONDecodeError:
                        pass

                    # Check for ZON structure in unquoted string
                    stripped = unquoted.strip()
                    if stripped.startswith('{') or stripped.startswith('['):
                        return self._parse_zon_node(stripped)

                    return unquoted

        # Booleans (case-insensitive)
        val_lower = trimmed.lower()
        if val_lower in ['t', 'true']:
            return True
        if val_lower in ['f', 'false']:
            return False

        # Null (case-insensitive)
        if val_lower in ['null', 'none', 'nil']:
            return None

        # Check for ZON-style nested structures (braced)
        if trimmed.startswith('{') or trimmed.startswith('['):
            return self._parse_zon_node(trimmed, 0)

        # Try number
        if trimmed:
            try:
                # Try integer first
                if '.' not in trimmed and 'e' not in trimmed.lower():
                    return int(trimmed)
                # Then float
                return float(trimmed)
            except ValueError:
                pass

        # Double-encoded JSON string fallback
        if trimmed.startswith('"') and trimmed.endswith('"'):
            try:
                return json.loads(trimmed)
            except json.JSONDecodeError:
                pass

        return trimmed

    def _unflatten(self, d: Dict) -> Dict:
        """
        Unflatten dictionary with dotted keys.
        """
        result: Any = {}

        for key, value in d.items():
            # Check if key has dot notation
            if '.' not in key:
                # Simple key, just assign
                result[key] = value
                continue

            parts = key.split('.')

            # SECURITY: Prevent prototype pollution
            if any(p in ['__proto__', 'constructor', 'prototype'] for p in parts):
                continue

            target: Any = result

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

                    # Only navigate deeper if it's a dict
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


def decode(data: str, strict: bool = True) -> Any:
    """
    Convenience function to decode ZON v1.0.4 format to original data.
    
    Args:
        data: ZON-encoded string
        strict: If True, validate table structure (row count, field count)
        
    Returns:
        Decoded data
        
    Raises:
        ZonDecodeError: On validation errors or security limit violations
    """
    return ZonDecoder(strict=strict).decode(data)
