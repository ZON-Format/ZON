# Advanced Features Guide

**Version:** 1.1.0  
**Status:** Stable

## Overview

ZON includes advanced compression and optimization features that dramatically reduce token count and improve LLM accuracy. These features are automatically applied by the encoder when beneficial.

## Table of Contents

- [Delta Encoding](#delta-encoding)
- [Dictionary Compression](#dictionary-compression)
- [Type Coercion](#type-coercion)
- [Hierarchical Sparse Encoding](#hierarchical-sparse-encoding)

---

## Delta Encoding

**Introduced:** v1.1.0  
**Purpose:** Compress sequential numeric columns

### How It Works

Instead of storing absolute values, delta encoding stores the difference from the previous value:

```
# Without delta:
ids:@(1000):id
1,2,3,4,5,...,1000

# With delta (`:delta` marker):
ids:@(1000):id:delta
1,+1,+1,+1,+1,...,+1
```

**Token Savings:** Up to 70% for sequential IDs or timestamps.

### When To Use

Delta encoding is automatically applied when ALL conditions are met:

1. Column contains **only numbers**
2. Column has **≥5 values**
3. Values are **sequential** (small deltas)

### Examples

```python
from zon import encode

# Sequential IDs
data = {
    'records': [
        {'id': i + 1, 'name': f'Record {i}'}
        for i in range(1000)
    ]
}

zon_str = encode(data)
print(zon_str)
# records:@(1000):id:delta,name
# 1,Record 0
# +1,Record 1
# +1,Record 2
# ...
```

**Timestamps:**

```python
logs = [
    {'timestamp': 1609459200, 'message': 'Started'},
    {'timestamp': 1609459260, 'message': 'Processing'},  # +60
    {'timestamp': 1609459320, 'message': 'Done'}         # +60
]

# Encoded as:
# logs:@(3):message,timestamp:delta
# Started,1609459200
# Processing,+60
# Done,+60
```

### Decoding

Delta encoding is automatically reversed during decoding:

```python
from zon import decode

zon_str = """
records:@(3):id:delta,name
1,Alice
+1,Bob
+1,Carol
"""

data = decode(zon_str)
print(data['records'])
# [
#   {'id': 1, 'name': 'Alice'},
#   {'id': 2, 'name': 'Bob'},
#   {'id': 3, 'name': 'Carol'}
# ]
```

---

## Dictionary Compression

**Introduced:** v1.0.3  
**Purpose:** Deduplicate repeated string values

### How It Works

When a column has many repeated values, ZON creates a dictionary and stores indices:

```
# Without dictionary:
shipments:@(150):status,...
pending,...
delivered,...
pending,...
in-transit,...
pending,...
...

# With dictionary:
status[3]:delivered,in-transit,pending
shipments:@(150):status,...
2,...    # "pending"
0,...    # "delivered"
2,...    # "pending"
1,...    # "in-transit"
2,...    # "pending"
...
```

### When To Use

Dictionary compression is automatically applied when:

1. Column has **≥10 values**
2. Column has **≤10 unique values**
3. **Compression ratio > 1.2x**

### Examples

```python
from zon import encode

shipments = [
    {'id': i, 'status': ['pending', 'delivered', 'in-transit'][i % 3]}
    for i in range(100)
]

zon_str = encode({'shipments': shipments})
print(zon_str)
# status[3]:delivered,in-transit,pending
# shipments:@(100):id,status
# 0,2       # id:0, status:"pending"
# 1,0       # id:1, status:"delivered"
# 2,1       # id:2, status:"in-transit"
# ...
```

### Nested Columns

Dictionary compression works with flattened nested fields:

```python
data = {
    'users': [
        {'name': 'Alice', 'address': {'city': 'NYC'}},
        {'name': 'Bob', 'address': {'city': 'LAX'}},
        {'name': 'Carol', 'address': {'city': 'NYC'}}
    ]
}

# Automatically creates dictionary for "address.city"
```

### Token Savings

Real-world examples:

| Dataset | Without Dict | With Dict | Savings |
|---------|--------------|-----------|---------|
| E-commerce orders | 45k tokens | 28k tokens | **38%** |
| Log files | 120k tokens | 65k tokens | **46%** |
| User roles | 8k tokens | 3k tokens | **63%** |

---

## Type Coercion

**Introduced:** v1.1.0  
**Purpose:** Handle "stringified" values from LLMs

### The Problem

LLMs sometimes return numbers or booleans as strings:

```json
{
  "age": "25",        // Should be number
  "active": "true"    // Should be boolean
}
```

### The Solution

Enable type coercion in the encoder:

```python
from zon import ZonEncoder

encoder = ZonEncoder(
    anchor_interval=None,          # default
    enable_dictionary=True,         # default
    enable_type_coercion=True       # ✅ Enable type coercion
)

data = {
    'users': [
        {'age': "25", 'active': "true"},   # Strings
        {'age': "30", 'active': "false"}
    ]
}

zon_str = encoder.encode(data)
print(zon_str)
# users:@(2):active,age
# T,25      # Coerced to boolean and number
# F,30
```

### How It Works

1. Analyzes entire column
2. Detects if all values are "coercible" (e.g., `"123"` → `123`)
3. Coerces entire column to the target type

### Supported Coercions

| From | To | Example |
|------|-----|---------|
| `"123"` | `123` | Number strings |
| `"true"` | `T` | Boolean strings |
| `"false"` | `F` | Boolean strings |
| `"null"` | `null` | Null strings |

### Decoder Coercion

The decoder also supports type coercion for LLM-generated ZON:

```python
from zon import decode

options = {'enable_type_coercion': True}
data = decode(llm_output, **options)
```

---

## Hierarchical Sparse Encoding

**Introduced:** v1.1.0  
**Purpose:** Efficiently encode nested objects with missing fields

### How It Works

Nested fields are flattened with dot notation:

```python
from zon import encode

data = {
    'users': [
        {'id': 1, 'profile': {'bio': 'Developer'}},
        {'id': 2, 'profile': None},
        {'id': 3, 'profile': {'bio': 'Designer'}}
    ]
}

zon_str = encode(data)
# users:@(3):id,profile.bio
# 1,Developer
# 2,null
# 3,Designer
```

### Deep Nesting

Supports up to 5 levels of nesting:

```python
data = {
    'items': [{
        'a': {'b': {'c': {'d': {'e': 'Deep!'}}}}
    }]
}

# Flattened to:
# items:@(1):a.b.c.d.e
# Deep!
```

### Sparse Columns

Missing values are preserved:

```python
data = {
    'products': [
        {'id': 1, 'meta': {'color': 'red', 'size': 'L'}},
        {'id': 2},  # No meta
        {'id': 3, 'meta': {'color': 'blue'}}  # No size
    ]
}

# Core: id, meta.color
# Sparse (inline): meta.size
# products:@(3):id,meta.color
# 1,red,meta.size:L
# 2,null
# 3,blue
```

---

## Performance Tips

1. **Delta encoding**: Best for time-series and sequential IDs
2. **Dictionary compression**: Best for categorical data (status, roles, countries)
3. **Type coercion**: Enable when dealing with LLM outputs
4. **Sparse encoding**: Automatic, no configuration needed

## See Also

- [API Reference](api-reference.md) - Full API documentation
- [SPEC.md](../SPEC.md) - Format specification
- [LLM Best Practices](llm-best-practices.md) - Using with LLMs
