"""Utility functions for ZON string quoting and value parsing."""

import json
import re
from typing import Any, Optional

def quote_string(s: str) -> str:
    """Quote a string value according to ZON format rules.
    
    Strings that look like numbers or boolean keywords are always quoted.
    Alphanumeric strings are left unquoted. Other strings are quoted with
    CSV-style escaping ("" for embedded quotes).
    
    Args:
        s: The string to quote
        
    Returns:
        The appropriately quoted string for ZON format
    """
    if re.match(r'^-?\d+(\.\d+)?$', s):
        return f'"{s}"'
    
    if re.match(r'^(true|false|t|f|null|none|nil)$', s, re.IGNORECASE):
        return f'"{s}"'
    
    if re.match(r'^[a-zA-Z0-9_\-\.]+$', s):
        return s
    
    json_str = json.dumps(s, ensure_ascii=False)
    inner = json_str[1:-1]
    zon_str = inner.replace('\\"', '""')
    return f'"{zon_str}"'

def parse_value(val: str) -> Any:
    """Parse a ZON value string into the appropriate Python type.
    
    Handles boolean keywords, null values, quoted strings with CSV-style
    escaping, and numeric values (int/float). Returns the original string
    if no type conversion applies.
    
    Args:
        val: The string value to parse
        
    Returns:
        The parsed value as the appropriate Python type (bool, None, str,
        int, float, or the original string)
    """
    trimmed = val.strip()
    lower = trimmed.lower()

    if lower in ('t', 'true'):
        return True
    if lower in ('f', 'false'):
        return False
    if lower in ('null', 'none', 'nil'):
        return None

    if trimmed.startswith('"'):
        try:
            return json.loads(trimmed)
        except json.JSONDecodeError:
            if trimmed.endswith('"'):
                inner = trimmed[1:-1]
                json_str = inner.replace('""', '\\"')
                return json.loads(f'"{json_str}"')

    if trimmed:
        try:
            if '.' not in trimmed and 'e' not in lower:
                return int(trimmed)
            return float(trimmed)
        except ValueError:
            pass

    return trimmed
