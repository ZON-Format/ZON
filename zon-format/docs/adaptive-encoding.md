# Adaptive Encoding Guide

**New in ZON v1.2.0**

Adaptive encoding automatically analyzes your data structure and selects the optimal encoding strategy for your use case.

## Quick Start

```python
from zon import encode_adaptive, AdaptiveEncodeOptions, recommend_mode

# Simple usage - uses compact mode by default
output = encode_adaptive(data)

# Explicit mode selection
output = encode_adaptive(data, AdaptiveEncodeOptions(mode='readable'))

# Get recommendation for your data
recommendation = recommend_mode(data)
print(f"Recommended mode: {recommendation['mode']}")
```

## Encoding Modes

ZON provides three encoding modes optimized for different scenarios:

### Compact Mode (Default)

**Best for:** Production APIs, cost-sensitive LLM workflows

**Features:**
- Maximum token compression
- Uses `T`/`F` for booleans (saves tokens)
- Dictionary compression for repeated values
- Table format for uniform data

**Example:**
```python
data = [
    {"id": 1, "name": "Alice", "active": True},
    {"id": 2, "name": "Bob", "active": False}
]

output = encode_adaptive(data, AdaptiveEncodeOptions(mode='compact'))
# Result:
# @2:active,id,name
# T,1,Alice
# F,2,Bob
```

### LLM-Optimized Mode

**Best for:** AI workflows, LLM comprehension

**Features:**
- Balances token efficiency with clarity
- Uses `true`/`false` (more readable for LLMs)
- Disables dictionary compression (shows actual values)
- Type coercion enabled for consistency

**Example:**
```python
output = encode_adaptive(data, AdaptiveEncodeOptions(mode='llm-optimized'))
# Result:
# @2:active,id,name
# true,1,Alice
# false,2,Bob
```

### Readable Mode

**Best for:** Configuration files, debugging, human editing

**Features:**
- Human-friendly formatting
- Proper indentation (configurable)
- Clear structure
- Great for version control

**Example:**
```python
data = {
    "config": {
        "database": {"host": "localhost", "port": 5432}
    }
}

output = encode_adaptive(
    data, 
    AdaptiveEncodeOptions(mode='readable', indent=2)
)
# Result: Properly indented, easy to read
```

## Data Complexity Analysis

The `DataComplexityAnalyzer` examines your data and provides metrics:

```python
from zon import DataComplexityAnalyzer

analyzer = DataComplexityAnalyzer()
result = analyzer.analyze(data)

print(f"Nesting depth: {result.nesting}")
print(f"Irregularity: {result.irregularity:.2%}")
print(f"Array size: {result.array_size}")
print(f"Recommendation: {result.recommendation}")
print(f"Confidence: {result.confidence:.2%}")
```

### Metrics Explained

- **Nesting**: Maximum depth of nested structures
- **Irregularity**: How much object shapes vary (0.0 = uniform, 1.0 = highly irregular)
- **Field Count**: Total unique fields across all objects
- **Array Size**: Size of largest array
- **Array Density**: Proportion of arrays vs objects

## Mode Recommendation

The `recommend_mode()` function analyzes your data and suggests the best mode:

```python
recommendation = recommend_mode(data)

# Returns:
{
    'mode': 'compact',           # Suggested mode
    'confidence': 0.95,          # Confidence level (0-1)
    'reason': 'Large uniform...', # Explanation
    'metrics': {                  # Analysis metrics
        'nesting': 2,
        'irregularity': 0.15,
        'field_count': 4,
        'array_size': 10
    }
}
```

### Recommendation Logic

- **Uniform arrays** (low irregularity, size ≥ 3) → `compact` mode
- **Deep nesting** (depth > 4) → `readable` mode
- **High irregularity** (> 70%) → `llm-optimized` mode
- **Mixed structures** → `llm-optimized` mode

## Advanced Options

### Custom Configuration

```python
options = AdaptiveEncodeOptions(
    mode='compact',
    complexity_threshold=0.6,      # Irregularity threshold
    max_nesting_for_table=3,       # Max depth for tables
    indent=2,                       # Indentation (readable mode)
    debug=True                      # Enable debug output
)

result = encode_adaptive(data, options)

# With debug=True, get detailed information
print(result.metrics)      # Complexity metrics
print(result.mode_used)    # Actual mode used
print(result.decisions)    # Encoding decisions made
```

### Override Encoding Settings

```python
options = AdaptiveEncodeOptions(
    mode='compact',
    enable_dict_compression=False,  # Disable dictionary compression
    enable_type_coercion=True       # Enable type coercion
)
```

## Use Cases

### 1. Cost-Sensitive LLM Applications

```python
# Minimize token usage for large datasets
from zon import encode_adaptive

# Compact mode saves ~30-50% tokens vs JSON
zon_data = encode_adaptive(large_dataset)

response = openai.ChatCompletion.create(
    model="gpt-4",
    messages=[
        {"role": "user", "content": f"Analyze:\n{zon_data}"}
    ]
)
```

### 2. Configuration Files

```python
# Human-readable config files
config = {
    "database": {...},
    "features": {...}
}

# Save as readable ZON
with open('config.zonf', 'w') as f:
    f.write(encode_adaptive(
        config, 
        AdaptiveEncodeOptions(mode='readable')
    ))
```

### 3. Data Analysis Pipelines

```python
# Let ZON choose the best format
for dataset in datasets:
    recommendation = recommend_mode(dataset)
    
    if recommendation['confidence'] > 0.8:
        mode = recommendation['mode']
    else:
        mode = 'llm-optimized'  # Safe default
    
    output = encode_adaptive(
        dataset, 
        AdaptiveEncodeOptions(mode=mode)
    )
```

## Best Practices

### 1. Use Compact Mode for Production

```python
# Default compact mode for API responses
output = encode_adaptive(data)
```

### 2. Use Readable Mode for Development

```python
# Debug with readable formatting
if DEBUG:
    output = encode_adaptive(data, AdaptiveEncodeOptions(mode='readable'))
else:
    output = encode_adaptive(data)  # compact
```

### 3. Let ZON Recommend

```python
# For unknown data structures
recommendation = recommend_mode(data)
if recommendation['confidence'] > 0.7:
    mode = recommendation['mode']
else:
    mode = 'compact'  # Safe fallback

output = encode_adaptive(data, AdaptiveEncodeOptions(mode=mode))
```

### 4. Enable Debug During Development

```python
result = encode_adaptive(
    data, 
    AdaptiveEncodeOptions(mode='compact', debug=True)
)

# Review decisions
for decision in result.decisions:
    print(f"  - {decision}")
```

## Performance Comparison

| Data Type | Compact | LLM-Optimized | Readable |
|-----------|---------|---------------|----------|
| Uniform arrays | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| Nested objects | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Mixed data | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| Config files | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

## Migration from v1.1.0

Existing code using `zon.encode()` continues to work unchanged:

```python
# Old code (still works)
output = zon.encode(data)

# New adaptive encoding
output = zon.encode_adaptive(data)  # Better results!
```

The adaptive encoding is backward compatible and produces output that can be decoded with any ZON decoder.

## See Also

- [API Reference](./api-reference.md)
- [Syntax Cheatsheet](./syntax-cheatsheet.md)
- [LLM Best Practices](./llm-best-practices.md)
