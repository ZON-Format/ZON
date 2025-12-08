# ZON Developer Tools

A comprehensive suite of developer utilities for working with ZON data, including helpers, validators, and pretty-printers.

## Overview

ZON provides several developer tools:

- **Helpers**: Size analysis, format comparison, schema inference
- **Validator**: Enhanced validation with linting rules
- **Pretty Printer**: Readable formatting with indentation
- **Utilities**: Data analysis, comparison, and safety checks

## Helper Functions

### size(data: Any, format: str = 'zon') -> int

Calculate the size of data in different formats.

```python
from zon import size

data = {"users": [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]}

# Get size in different formats
zon_size = size(data, 'zon')
json_size = size(data, 'json')
binary_size = size(data, 'binary')

print(f"ZON: {zon_size} bytes")
print(f"JSON: {json_size} bytes")
print(f"Binary: {binary_size} bytes")
```

**Supported Formats:**
- `'zon'`: Text ZON format
- `'json'`: JSON format
- `'binary'`: ZON-B binary format

### compare_formats(data: Any) -> Dict

Compare data size across all formats.

```python
from zon import compare_formats

data = load_dataset()
comparison = compare_formats(data)

print(comparison)
# {
#     'json': {'size': 15420, 'percentage': 100.0},
#     'zon': {'size': 10234, 'percentage': 66.4},
#     'binary': {'size': 6128, 'percentage': 39.7}
# }
```

### infer_schema(data: Any) -> Dict

Infer schema structure from data.

```python
from zon import infer_schema

data = {
    "users": [
        {"id": 1, "name": "Alice", "active": True},
        {"id": 2, "name": "Bob", "active": False}
    ],
    "total": 2
}

schema = infer_schema(data)
print(schema)
# {
#     'type': 'object',
#     'properties': {
#         'users': {
#             'type': 'array',
#             'items': {
#                 'type': 'object',
#                 'properties': {
#                     'id': {'type': 'integer'},
#                     'name': {'type': 'string'},
#                     'active': {'type': 'boolean'}
#                 }
#             }
#         },
#         'total': {'type': 'integer'}
#     }
# }
```

### analyze(data: Any) -> Dict

Comprehensive data analysis.

```python
from zon import analyze

data = {"nested": {"deeply": {"value": 123}}, "items": [1, 2, 3, 4, 5]}

analysis = analyze(data)
print(analysis)
# {
#     'depth': 3,
#     'total_keys': 4,
#     'array_count': 1,
#     'max_array_size': 5,
#     'types': {'object': 3, 'array': 1, 'integer': 6},
#     'complexity': 'moderate',
#     'recommended_format': 'zon'
# }
```

### compare(data1: Any, data2: Any) -> Dict

Deep comparison between two data structures.

```python
from zon import compare

old_data = {"name": "Alice", "age": 30}
new_data = {"name": "Alice", "age": 31, "city": "NYC"}

diff = compare(old_data, new_data)
print(diff)
# {
#     'equal': False,
#     'changes': {
#         'modified': ['age'],
#         'added': ['city'],
#         'removed': []
#     },
#     'details': {
#         'age': {'old': 30, 'new': 31},
#         'city': {'old': None, 'new': 'NYC'}
#     }
# }
```

### is_safe(data: Any, max_depth: int = 10, max_size: int = 1000000) -> bool

Check if data is safe to encode.

```python
from zon import is_safe

large_data = generate_large_dataset()

if is_safe(large_data, max_depth=5, max_size=100000):
    encoded = encode(large_data)
else:
    print("Data too large or deeply nested!")
```

## Validator

### ZonValidator

Enhanced validator with linting rules.

```python
from zon import ZonValidator, LintOptions

validator = ZonValidator()

# Validate ZON string
zon_string = "name:Alice\nage:30"
result = validator.validate(zon_string)

if result.is_valid:
    print("Valid ZON!")
else:
    for error in result.errors:
        print(f"Error at line {error.line}: {error.message}")
    for warning in result.warnings:
        print(f"Warning at line {warning.line}: {warning.message}")
```

### Validation Results

```python
class ValidationResult:
    is_valid: bool           # True if no errors
    errors: List[ValidationError]     # Syntax/semantic errors
    warnings: List[ValidationWarning] # Style warnings
    metadata: Dict           # Additional information
```

### Linting Options

```python
from zon import ZonValidator, LintOptions

options = LintOptions(
    max_depth=10,           # Maximum nesting depth
    max_fields=100,         # Maximum fields per object
    check_performance=True, # Performance checks
    strict_mode=False       # Strict parsing
)

validator = ZonValidator(options)
result = validator.validate(zon_string, options)
```

### Common Validations

```python
from zon import ZonValidator

validator = ZonValidator()

# Check syntax
result = validator.validate("invalid{syntax")
assert not result.is_valid

# Check nesting depth
deep_data = "level1:{level2:{level3:{level4:{level5:{too_deep:value}}}}}"
result = validator.validate(deep_data, LintOptions(max_depth=4))
assert len(result.warnings) > 0

# Check field count
many_fields = "\n".join([f"field{i}:value" for i in range(200)])
result = validator.validate(many_fields, LintOptions(max_fields=100))
assert len(result.warnings) > 0
```

### validate_zon() Convenience Function

```python
from zon import validate_zon

# Quick validation
is_valid = validate_zon("name:Alice\nage:30")

if is_valid:
    print("Valid!")
```

## Pretty Printer

### expand_print(zon_string: str, indent: int = 2) -> str

Format ZON with indentation and newlines.

```python
from zon import expand_print

compact = "customer:{name:Alice,address:{city:NYC,zip:10001}}"
readable = expand_print(compact, indent=2)

print(readable)
# customer:{
#   address:{
#     city:NYC
#     zip:10001
#   }
#   name:Alice
# }
```

### compact_print(zon_string: str) -> str

Remove unnecessary whitespace.

```python
from zon import compact_print

spaced = """
name: Alice
age:  30
city:    NYC
"""

compact = compact_print(spaced)
print(compact)
# name:Alice\nage:30\ncity:NYC
```

## Complete Examples

### Example 1: Data Analysis Pipeline

```python
from zon import analyze, compare_formats, infer_schema, is_safe

def analyze_dataset(data):
    """Complete data analysis."""
    
    # Check safety
    if not is_safe(data, max_depth=10, max_size=10_000_000):
        return {"error": "Data too large or deeply nested"}
    
    # Analyze structure
    analysis = analyze(data)
    
    # Compare format sizes
    formats = compare_formats(data)
    
    # Infer schema
    schema = infer_schema(data)
    
    return {
        "analysis": analysis,
        "formats": formats,
        "schema": schema,
        "recommendation": recommend_storage_format(formats)
    }

def recommend_storage_format(formats):
    """Recommend best storage format."""
    if formats['binary']['size'] < formats['zon']['size'] * 0.7:
        return 'binary'  # >30% savings
    elif formats['zon']['size'] < formats['json']['size'] * 0.8:
        return 'zon'     # >20% savings
    else:
        return 'json'    # Standard format
```

### Example 2: Data Migration Validator

```python
from zon import compare, validate_zon, encode, decode

def validate_migration(old_data, new_data):
    """Validate data migration integrity."""
    
    # Encode both versions
    old_zon = encode(old_data)
    new_zon = encode(new_data)
    
    # Validate syntax
    if not validate_zon(old_zon):
        return {"valid": False, "error": "Old data invalid"}
    if not validate_zon(new_zon):
        return {"valid": False, "error": "New data invalid"}
    
    # Compare structures
    diff = compare(old_data, new_data)
    
    # Check for data loss
    if diff['changes']['removed']:
        return {
            "valid": False,
            "error": "Data loss detected",
            "removed_fields": diff['changes']['removed']
        }
    
    return {
        "valid": True,
        "changes": diff['changes'],
        "details": diff['details']
    }
```

### Example 3: Smart Encoder

```python
from zon import (
    encode, encode_binary, encode_adaptive,
    size, analyze, AdaptiveEncodeOptions
)

def smart_encode(data):
    """Automatically choose best encoding."""
    
    # Analyze data
    analysis = analyze(data)
    
    # Check size
    data_size = size(data, 'json')
    
    # Small data: use readable format
    if data_size < 1000:
        return encode_adaptive(
            data,
            AdaptiveEncodeOptions(mode='readable')
        )
    
    # Large uniform data: use binary
    elif data_size > 100000 and analysis['complexity'] == 'low':
        return encode_binary(data)
    
    # Medium or complex: use compact
    else:
        return encode_adaptive(
            data,
            AdaptiveEncodeOptions(mode='compact')
        )
```

### Example 4: Validation Service

```python
from zon import ZonValidator, LintOptions
from flask import Flask, request, jsonify

app = Flask(__name__)
validator = ZonValidator()

@app.route('/validate', methods=['POST'])
def validate_endpoint():
    """Validate ZON data via API."""
    
    zon_string = request.data.decode('utf-8')
    
    # Get linting options from query params
    options = LintOptions(
        max_depth=int(request.args.get('max_depth', 10)),
        max_fields=int(request.args.get('max_fields', 100)),
        check_performance=request.args.get('check_perf', 'true') == 'true'
    )
    
    # Validate
    result = validator.validate(zon_string, options)
    
    return jsonify({
        'valid': result.is_valid,
        'errors': [
            {
                'line': e.line,
                'column': e.column,
                'message': e.message
            }
            for e in result.errors
        ],
        'warnings': [
            {
                'line': w.line,
                'message': w.message
            }
            for w in result.warnings
        ]
    })
```

## Performance Tips

### 1. Cache Analysis Results

```python
from functools import lru_cache
from zon import analyze

@lru_cache(maxsize=128)
def cached_analyze(data_hash):
    return analyze(data)

# Use with hash
import hashlib
data_hash = hashlib.md5(str(data).encode()).hexdigest()
result = cached_analyze(data_hash)
```

### 2. Batch Validation

```python
from zon import ZonValidator

validator = ZonValidator()

def validate_batch(zon_strings):
    """Validate multiple ZON strings efficiently."""
    results = []
    for zon_str in zon_strings:
        results.append(validator.validate(zon_str))
    return results
```

### 3. Lazy Loading

```python
from zon import size

def should_load_full_data(file_path):
    """Check size before loading."""
    # Check file size first
    file_size = os.path.getsize(file_path)
    
    if file_size > 10_000_000:  # 10MB
        return False
    
    # Load and check structure
    with open(file_path) as f:
        data = json.load(f)
    
    return is_safe(data, max_depth=10)
```

## CLI Integration

```bash
# Analyze data
zon analyze data.json --detailed

# Validate with linting
zon validate data.zonf --max-depth=5 --max-fields=50

# Format/pretty-print
zon format data.zonf --indent=4 > formatted.zonf

# Compare formats
zon compare data.json --formats=json,zon,binary
```

## Best Practices

### 1. Always Validate Before Processing

```python
from zon import validate_zon

def process_data(zon_string):
    if not validate_zon(zon_string):
        raise ValueError("Invalid ZON data")
    
    data = decode(zon_string)
    # Process data...
```

### 2. Use Analysis for Optimization

```python
from zon import analyze, encode_adaptive, AdaptiveEncodeOptions

def optimize_encoding(data):
    analysis = analyze(data)
    
    if analysis['complexity'] == 'low':
        mode = 'compact'
    elif analysis['depth'] > 5:
        mode = 'readable'
    else:
        mode = 'llm-optimized'
    
    return encode_adaptive(data, AdaptiveEncodeOptions(mode=mode))
```

### 3. Monitor Data Growth

```python
from zon import size, compare_formats

def monitor_data_growth(data, threshold_mb=10):
    sizes = compare_formats(data)
    
    for format_name, info in sizes.items():
        size_mb = info['size'] / 1_000_000
        if size_mb > threshold_mb:
            logger.warning(
                f"Data size in {format_name} exceeds {threshold_mb}MB: "
                f"{size_mb:.2f}MB"
            )
```

## Further Reading

- [API Reference](api-reference.md)
- [Binary Format](binary-format.md)
- [Adaptive Encoding](adaptive-encoding.md)
- [CLI Guide](cli-guide.md)
