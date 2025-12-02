# LLM Best Practices

**Version:** 1.1.0

## Overview

Tips and best practices for using ZON with Large Language Models.

---

## 1. Always Include Examples

LLMs learn better from examples than rules:

**❌ Bad:**
```python
prompt = "Respond in ZON format"
```

**✅ Good:**
```python
prompt = """
Respond in ZON format. Example:

users:@(2):id,name,role
1,Alice,admin
2,Bob,user

Now list 3 products:
"""
```

---

## 2. Use Schema Validation

Validate LLM outputs to catch errors:

```python
from zon import validate, zon

schema = zon.object({
    'name': zon.string(),
    'age': zon.number(),
    'role': zon.enum(['admin', 'user'])
})

result = validate(llm_output, schema)
if not result.success:
    # Retry or provide feedback
    print(f"Validation failed: {result.error}")
```

---

## 3. Enable Type Coercion for LLM Outputs

LLMs often return stringified values:

```python
from zon import decode

# Enable type coercion
data = decode(llm_output, enable_type_coercion=True)
```

---

## 4. Token Efficiency Matters

ZON saves 30-50% tokens vs JSON:

```python
from zon import encode, count_tokens
import json

# Compare token counts
json_str = json.dumps(data, indent=2)
zon_str = encode(data)

print(f"JSON: {count_tokens(json_str)} tokens")
print(f"ZON:  {count_tokens(zon_str)} tokens")
```

---

## 5. Handle Parsing Errors Gracefully

```python
from zon import decode, ZonDecodeError

try:
    data = decode(llm_output)
except ZonDecodeError as e:
    # Feed error back to LLM for self-correction
    error_msg = f"Invalid ZON: {e.message}. Please fix."
    llm_output = retry_with_feedback(error_msg)
```

---

## 6. Use Streaming for Large Outputs

```python
from zon import ZonStreamDecoder

decoder = ZonStreamDecoder()

for chunk in llm_stream():
    objects = decoder.feed(chunk)
    for obj in objects:
        process(obj)
```

---

## 7. Optimize Field Ordering

Place important fields first:

```python
from zon import encode

# Default (alphabetical): active,age,email,id,name,role
data = encode(users)

# Better: id,name,role,age,email,active
# (Prioritize retrieval fields)
```

---

## See Also

- [Schema Validation](schema-validation.md)
- [Integrations](integrations.md)
- [API Reference](api-reference.md)
