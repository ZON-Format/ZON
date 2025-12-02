#!/usr/bin/env python3
"""
CSV/TSV encoder for benchmark data.
Uses Python's csv module for proper escaping.
"""

import csv
import json
from io import StringIO
from typing import Any, List, Dict


def array_to_delimited(data: List[Any], delimiter: str = ',') -> str:
    """
    Converts array of objects to delimited text format.
    
    Args:
        data: Array of objects to convert
        delimiter: Delimiter character
        
    Returns:
        Formatted string
    """
    if not isinstance(data, list) or len(data) == 0:
        return ''
    
    if not isinstance(data[0], dict):
        return delimiter.join(str(item) for item in data)
    
    all_keys = set()
    for obj in data:
        if isinstance(obj, dict):
            all_keys.update(obj.keys())
    
    headers = sorted(all_keys)
    
    output = StringIO()
    writer = csv.writer(output, delimiter=delimiter, quoting=csv.QUOTE_MINIMAL)
    
    writer.writerow(headers)
    
    for obj in data:
        row = []
        for header in headers:
            value = obj.get(header)
            
            if value is None:
                row.append('')
            elif isinstance(value, (dict, list)):
                row.append(json.dumps(value))
            else:
                row.append(str(value))
        
        writer.writerow(row)
    
    return output.getvalue().rstrip('\n')


def object_to_delimited(data: Dict[str, Any], delimiter: str = ',') -> str:
    """
    Converts object to delimited text format.
    
    Args:
        data: Object to convert
        delimiter: Delimiter character
        
    Returns:
        Formatted string
    """
    if not isinstance(data, dict):
        return str(data)
    
    parts = []
    
    for key, value in data.items():
        if isinstance(value, list) and value and isinstance(value[0], dict):
            parts.append(f'\n# {key}')
            parts.append(array_to_delimited(value, delimiter))
        elif isinstance(value, list):
            parts.append(f'{key}{delimiter}{delimiter.join(str(v) for v in value)}')
        elif isinstance(value, dict):
            parts.append(f'{key}{delimiter}"{json.dumps(value)}"')
        else:
            parts.append(f'{key}{delimiter}{value}')
    
    return '\n'.join(parts)


def encode_to_csv(data: Any) -> str:
    """
    Encodes data to CSV format.
    
    Args:
        data: Data to encode
        
    Returns:
        CSV formatted string
    """
    if isinstance(data, list):
        return array_to_delimited(data, ',')
    elif isinstance(data, dict):
        return object_to_delimited(data, ',')
    else:
        return str(data)


def encode_to_tsv(data: Any) -> str:
    """
    Encodes data to TSV format.
    
    Args:
        data: Data to encode
        
    Returns:
        TSV formatted string
    """
    if isinstance(data, list):
        return array_to_delimited(data, '\t')
    elif isinstance(data, dict):
        return object_to_delimited(data, '\t')
    else:
        return str(data)


if __name__ == "__main__":
    test_data = [
        {'id': 1, 'name': 'Alice', 'salary': 95000},
        {'id': 2, 'name': 'Bob', 'salary': 82000},
        {'id': 3, 'name': 'Charlie', 'dept': 'Engineering'}
    ]
    
    print("CSV Output:")
    print(encode_to_csv(test_data))
    print("\nTSV Output:")
    print(encode_to_tsv(test_data))
