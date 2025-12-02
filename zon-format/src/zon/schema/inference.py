"""Type inference and coercion for ZON format values."""

import json
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

class TypeInferrer:
    """Infers and coerces data types for ZON encoding and decoding.
    
    This class provides methods to infer types from string values, coerce
    values to target types, and analyze column-level type consistency in
    tabular data.
    """
    def infer(self, value: Any) -> Dict[str, Any]:
        """Infer the type of a value and whether it can be coerced.
        
        Args:
            value: The value to analyze
            
        Returns:
            Dictionary with 'type', 'coercible', and optional 'original' keys
        """
        if isinstance(value, str):
            trimmed = value.strip()
            
            if re.match(r'^(true|false|yes|no|1|0)$', trimmed, re.IGNORECASE):
                return {'type': 'boolean', 'coercible': True, 'original': 'string'}

            if re.match(r'^-?\d+(\.\d+)?([eE][+-]?\d+)?$', trimmed):
                return {'type': 'number', 'coercible': True, 'original': 'string'}
            
            if self._is_iso_date(trimmed):
                return {'type': 'date', 'coercible': True, 'original': 'string'}
            
            if (trimmed.startswith('{') and trimmed.endswith('}')) or \
               (trimmed.startswith('[') and trimmed.endswith(']')):
                try:
                    json.loads(trimmed)
                    return {'type': 'json', 'coercible': True, 'original': 'string'}
                except json.JSONDecodeError:
                    pass
        
        return {'type': type(value).__name__, 'coercible': False}

    def coerce(self, value: Any, target_type: Dict[str, Any]) -> Any:
        """Coerce a value to a target type if possible.
        
        Args:
            value: The value to coerce
            target_type: Type information dictionary from infer()
            
        Returns:
            Coerced value or original value if coercion is not possible
        """
        if not target_type.get('coercible'):
            return value
        
        t_type = target_type.get('type')
        
        if t_type == 'number':
            try:
                if isinstance(value, str) and '.' not in value and 'e' not in value.lower():
                    return int(value)
                return float(value)
            except ValueError:
                return value
                
        if t_type == 'boolean':
            return str(value).lower() in ('true', 'yes', '1')
            
        if t_type == 'date':
            try:
                return datetime.fromisoformat(value.replace('Z', '+00:00'))
            except ValueError:
                return value
                
        if t_type == 'json':
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
                
        return value

    def infer_column_type(self, values: List[Any]) -> Dict[str, Any]:
        """Infer the predominant type for a column of values.
        
        Returns a type if at least 80% of non-null values match that type.
        
        Args:
            values: List of column values to analyze
            
        Returns:
            Dictionary with 'type', 'coercible', and 'confidence' keys
        """
        non_null_values = [v for v in values if v is not None]
        total = len(non_null_values)
        
        if total == 0:
            return {'type': 'undefined', 'coercible': False}

        boolean_count = sum(1 for v in non_null_values if self._is_boolean(v))
        if boolean_count / total >= 0.8:
            return {'type': 'boolean', 'coercible': True, 'confidence': boolean_count / total}

        number_count = sum(1 for v in non_null_values if self._is_number(v))
        if number_count / total >= 0.8:
            return {'type': 'number', 'coercible': True, 'confidence': number_count / total}

        date_count = sum(1 for v in non_null_values if self._is_date(v))
        if date_count / total >= 0.8:
            return {'type': 'date', 'coercible': True, 'confidence': date_count / total}

        json_count = sum(1 for v in non_null_values if self._is_json(v))
        if json_count / total >= 0.8:
            return {'type': 'json', 'coercible': True, 'confidence': json_count / total}
        
        return {'type': 'mixed', 'coercible': False}

    def _is_number(self, v: Any) -> bool:
        """Check if a value is a number or numeric string."""
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            return True
        if isinstance(v, str):
            return bool(re.match(r'^-?\d+(\.\d+)?([eE][+-]?\d+)?$', v.strip()))
        return False

    def _is_boolean(self, v: Any) -> bool:
        """Check if a value is a boolean or boolean-like string."""
        if isinstance(v, bool):
            return True
        if isinstance(v, str):
            return bool(re.match(r'^(true|false|yes|no|1|0)$', v.strip(), re.IGNORECASE))
        return False

    def _is_date(self, v: Any) -> bool:
        """Check if a value is a datetime or ISO 8601 date string."""
        if isinstance(v, datetime):
            return True
        if isinstance(v, str):
            return self._is_iso_date(v.strip())
        return False

    def _is_json(self, v: Any) -> bool:
        """Check if a value is a dict/list or valid JSON string."""
        if isinstance(v, (dict, list)):
            return True
        if isinstance(v, str):
            trimmed = v.strip()
            if (trimmed.startswith('{') and trimmed.endswith('}')) or \
               (trimmed.startswith('[') and trimmed.endswith(']')):
                try:
                    json.loads(trimmed)
                    return True
                except json.JSONDecodeError:
                    return False
        return False

    def _is_iso_date(self, s: str) -> bool:
        """Check if a string matches ISO 8601 date format."""
        return bool(re.match(r'^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}:\d{2}(\.\d{3})?(Z|[-+]\d{2}:?\d{2})?)?$', s))
