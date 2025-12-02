# API Reference

**Version:** 1.1.0

## Core Functions

### `encode(data, **options) -> str`

Encodes Python data to ZON format.

**Parameters:**
- `data` (any): Python object to encode
- `**options`: Optional encoding options
  - `enable_type_coercion` (bool): Enable automatic type coercion

**Returns:** ZON-formatted string

**Example:**
```python
from zon import encode

data = {
    'users': [
        {'id': 1, 'name': 'Alice'},
        {'id': 2, 'name': 'Bob'}
    ]
}

zon_str = encode(data)
print(zon_str)
# users:@(2):id,name
# 1,Alice
# 2,Bob
```

---

### `decode(zon_str, **options) -> any`

Decodes ZON format back to Python data.

**Parameters:**
- `zon_str` (str): ZON-formatted string
- `**options`: Optional decoding options
  - `strict` (bool): Validate table structure (default: `True`)
  - `enable_type_coercion` (bool): Enable type coercion

**Returns:** Original Python data structure

**Example:**
```python
from zon import decode

zon_str = """
users:@(2):id,name
1,Alice
2,Bob
"""

data = decode(zon_str)
print(data)
# {'users': [{'id': 1, 'name': 'Alice'}, {'id': 2, 'name': 'Bob'}]}
```

**Error Handling:**
```python
from zon import decode, ZonDecodeError

try:
    data = decode(invalid_zon)
except ZonDecodeError as e:
    print(e.code)    # "E001" or "E002"
    print(e.message) # Detailed error message
```

---

## Advanced Functions

### `split(data, token_limit, overlap=0.1) -> List[str]`

Splits large data into chunks based on token limit.

**Parameters:**
- `data` (any): Data to split
- `token_limit` (int): Maximum tokens per chunk
- `overlap` (float): Overlap ratio between chunks (0.0-1.0)

**Returns:** List of ZON-encoded chunks

**Example:**
```python
from zon import split

large_data = {'items': [{'id': i} for i in range(10000)]}
chunks = split(large_data, token_limit=1000, overlap=0.1)

print(f"Created {len(chunks)} chunks")
# Created 45 chunks
```

---

### `validate(zon_str, schema) -> ValidationResult`

Validates ZON data against a schema.

**Parameters:**
- `zon_str` (str): ZON data to validate
- `schema`: Schema definition

**Returns:** `ValidationResult` with `success`, and optionally `error` and `issues`

**Example:**
```python
from zon import validate, zon

# Define schema
UserSchema = zon.object({
    'name': zon.string(),
    'age': zon.number(),
    'role': zon.enum(['admin', 'user'])
})

# Validate
result = validate(llm_output, UserSchema)

if result.success:
    print("Valid!")
else:
    print(f"Error: {result.error}")
    print(f"Issues: {result.issues}")
```

---

## Classes

### `ZonEncoder`

Advanced encoder with configuration options.

**Constructor:**
```python
from zon import ZonEncoder

encoder = ZonEncoder(
    anchor_interval=None,           # Anchor interval for large tables
    enable_dictionary=True,          # Enable dictionary compression
    enable_type_coercion=False       # Enable type coercion
)
```

**Methods:**

#### `encode(data) -> str`

```python
data = {'users': [{'id': 1, 'name': 'Alice'}]}
zon_str = encoder.encode(data)
```

---

### `ZonDecoder`

Advanced decoder with configuration options.

**Constructor:**
```python
from zon import ZonDecoder

decoder = ZonDecoder(
    strict=True,                     # Validate table structure
    enable_type_coercion=False       # Enable type coercion
)
```

**Methods:**

#### `decode(zon_str) -> any`

```python
zon_str = "users:@(1):id,name\\n1,Alice"
data = decoder.decode(zon_str)
```

---

### `ZonStreamEncoder`

Stream encoder for large datasets.

**Constructor:**
```python
from zon import ZonStreamEncoder

encoder = ZonStreamEncoder()
```

**Methods:**

#### `write(data) -> str`

Incrementally encodes data.

```python
import sys

encoder = ZonStreamEncoder()

for chunk in large_dataset:
    zon_chunk = encoder.write(chunk)
    sys.stdout.write(zon_chunk)
```

---

### `ZonStreamDecoder`

Stream decoder for large datasets.

**Constructor:**
```python
from zon import ZonStreamDecoder

decoder = ZonStreamDecoder()
```

**Methods:**

#### `feed(chunk: str) -> List[any]`

```python
decoder = ZonStreamDecoder()

with open('large_file.zonf') as f:
    for line in f:
        objects = decoder.feed(line)
        for obj in objects:
            process(obj)
```

---

## Schema Types

### `zon.string()`

String type.

```python
name = zon.string().describe("User's full name")
```

### `zon.number()`

Number type (int or float).

```python
age = zon.number().min(0).max(120)
```

### `zon.boolean()`

Boolean type.

```python
active = zon.boolean().default(True)
```

### `zon.array(type)`

Array of a specific type.

```python
tags = zon.array(zon.string())
```

### `zon.object(fields)`

Object with specific fields.

```python
user = zon.object({
    'name': zon.string(),
    'age': zon.number()
})
```

### `zon.enum(values)`

Enumeration of allowed values.

```python
role = zon.enum(['admin', 'user', 'guest'])
```

---

## Exceptions

### `ZonEncodeError`

Raised when encoding fails.

```python
from zon import ZonEncodeError

try:
    encode(circular_reference)
except ZonEncodeError as e:
    print(f"Encoding failed: {e}")
```

### `ZonDecodeError`

Raised when decoding fails.

**Properties:**
- `code` (str): Error code (E001, E002, etc.)
- `message` (str): Detailed error message

```python
from zon import ZonDecodeError

try:
    decode(invalid_zon)
except ZonDecodeError as e:
    if e.code == 'E001':
        print("Row count mismatch")
    elif e.code == 'E002':
        print("Field count mismatch")
```

---

## Utility Functions

### `count_tokens(text) -> int`

Count tokens in text (uses tiktoken).

```python
from zon import count_tokens

zon_str = encode(data)
tokens = count_tokens(zon_str)
print(f"ZON: {tokens} tokens")
```

---

## See Also

- [Advanced Features](advanced-features.md) - Delta encoding, dictionaries, etc.
- [Streaming Guide](streaming-guide.md) - Stream processing
- [Schema Validation](schema-validation.md) - Validation details
