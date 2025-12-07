"""Helper Utilities for ZON

Useful functions for working with ZON data.
"""

import json
from typing import Any, Dict, Literal
from ..core.encoder import encode
from ..core.decoder import decode
from ..binary import encode_binary


def size(data: Any, format: Literal['zon', 'binary', 'json'] = 'zon') -> int:
    """Calculate the encoded size of data in different formats.
    
    Args:
        data: Data to measure
        format: Format to use ('zon', 'binary', or 'json')
        
    Returns:
        Size in bytes
        
    Example:
        >>> data = {"name": "Alice", "age": 30}
        >>> size(data, 'zon')
        45
        >>> size(data, 'json')
        28
    """
    if format == 'zon':
        return len(encode(data).encode('utf-8'))
    elif format == 'binary':
        return len(encode_binary(data))
    elif format == 'json':
        return len(json.dumps(data, separators=(',', ':')).encode('utf-8'))
    else:
        raise ValueError(f"Unknown format: {format}")


def compare_formats(data: Any) -> Dict[str, Any]:
    """Compare sizes across all formats.
    
    Args:
        data: Data to compare
        
    Returns:
        Dictionary with sizes and savings percentages
        
    Example:
        >>> data = [{"id": i, "value": i*2} for i in range(10)]
        >>> result = compare_formats(data)
        >>> result['savings']['zon_vs_json']
        35.5
    """
    zon_size = size(data, 'zon')
    binary_size = size(data, 'binary')
    json_size = size(data, 'json')
    
    def calc_savings(smaller: int, larger: int) -> float:
        if larger == 0:
            return 0.0
        if smaller == 0:
            return 100.0
        return (1 - smaller / larger) * 100
    
    return {
        'zon': zon_size,
        'binary': binary_size,
        'json': json_size,
        'savings': {
            'zon_vs_json': calc_savings(zon_size, json_size),
            'binary_vs_json': calc_savings(binary_size, json_size),
            'binary_vs_zon': calc_savings(binary_size, zon_size)
        }
    }


def infer_schema(data: Any) -> Dict[str, Any]:
    """Infer a basic schema structure from sample data.
    
    Args:
        data: Data to analyze
        
    Returns:
        Simple schema representation
        
    Example:
        >>> data = {"name": "Alice", "age": 30}
        >>> schema = infer_schema(data)
        >>> schema['type']
        'object'
    """
    if data is None:
        return {'type': 'null'}
    
    if isinstance(data, bool):
        return {'type': 'boolean'}
    
    if isinstance(data, int):
        return {'type': 'integer'}
    
    if isinstance(data, float):
        return {'type': 'number'}
    
    if isinstance(data, str):
        return {'type': 'string'}
    
    if isinstance(data, list):
        if len(data) == 0:
            return {'type': 'array', 'items': {'type': 'any'}}
        
        item_schema = infer_schema(data[0])
        return {'type': 'array', 'items': item_schema}
    
    if isinstance(data, dict):
        properties = {}
        for key, value in data.items():
            properties[key] = infer_schema(value)
        
        return {
            'type': 'object',
            'properties': properties
        }
    
    return {'type': 'any'}


def analyze(data: Any) -> Dict[str, Any]:
    """Analyze data structure complexity.
    
    Args:
        data: Data to analyze
        
    Returns:
        Analysis results with metrics
        
    Example:
        >>> data = {"users": [{"id": 1}] * 5}
        >>> stats = analyze(data)
        >>> stats['depth']
        3
    """
    def get_depth(obj: Any, current_depth: int = 0) -> int:
        if not isinstance(obj, (dict, list)):
            return current_depth
        
        if isinstance(obj, list):
            if not obj:
                return current_depth + 1
            return max(get_depth(item, current_depth + 1) for item in obj)
        
        if isinstance(obj, dict):
            if not obj:
                return current_depth + 1
            return max(get_depth(value, current_depth + 1) for value in obj.values())
        
        return current_depth
    
    def count_fields(obj: Any) -> int:
        if isinstance(obj, dict):
            count = len(obj)
            for value in obj.values():
                count += count_fields(value)
            return count
        elif isinstance(obj, list):
            return sum(count_fields(item) for item in obj)
        return 0
    
    return {
        'depth': get_depth(data),
        'field_count': count_fields(data),
        'type': type(data).__name__
    }


def compare(data1: Any, data2: Any) -> Dict[str, Any]:
    """Compare two data structures.
    
    Args:
        data1: First data structure
        data2: Second data structure
        
    Returns:
        Comparison results
        
    Example:
        >>> data1 = {"name": "Alice"}
        >>> data2 = {"name": "Bob"}
        >>> result = compare(data1, data2)
        >>> result['equal']
        False
    """
    return {
        'equal': data1 == data2,
        'data1_type': type(data1).__name__,
        'data2_type': type(data2).__name__,
        'data1_size': size(data1, 'zon'),
        'data2_size': size(data2, 'zon')
    }


def is_safe(data: Any, max_depth: int = 10, max_size: int = 1000000) -> Dict[str, Any]:
    """Check if data is safe to encode (not too deep or large).
    
    Args:
        data: Data to check
        max_depth: Maximum allowed nesting depth
        max_size: Maximum allowed size in bytes
        
    Returns:
        Safety check results
        
    Example:
        >>> data = {"test": "value"}
        >>> result = is_safe(data)
        >>> result['safe']
        True
    """
    try:
        stats = analyze(data)
        depth = stats['depth']
        
        encoded_size = size(data, 'zon')
        
        safe = depth <= max_depth and encoded_size <= max_size
        
        return {
            'safe': safe,
            'depth': depth,
            'max_depth': max_depth,
            'size': encoded_size,
            'max_size': max_size,
            'warnings': []
        }
    except Exception as e:
        return {
            'safe': False,
            'error': str(e),
            'warnings': ['Failed to analyze data']
        }
