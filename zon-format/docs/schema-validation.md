# Schema Validation Guide

**Version:** 1.1.0

## Overview

ZON includes runtime schema validation to ensure LLM outputs match expected formats.

---

## Quick Start

```python
from zon import validate, zon

# Define schema
UserSchema = zon.object({
    'name': zon.string().describe("User's full name"),
    'age': zon.number().describe("Age in years"),
    'role': zon.enum(['admin', 'user']).describe("Access level"),
    'tags': zon.array(zon.string()).optional()
})

# Validate
result = validate(llm_output, UserSchema)

if result.success:
    data = result.data
else:
    print(f"Error: {result.error}")
    print(f"Issues: {result.issues}")
```

---

## Schema Types

### String

```python
name = zon.string() \
    .min_length(1) \
    .max_length(100) \
    .describe("User name")
```

### Number

```python
age = zon.number() \
    .min(0) \
    .max(120) \
    .describe("Age in years")
```

### Boolean

```python
active = zon.boolean() \
    .default(True) \
    .describe("Is active")
```

### Array

```python
tags = zon.array(zon.string()) \
    .min_items(1) \
    .describe("User tags")
```

### Object

```python
address = zon.object({
    'street': zon.string(),
    'city': zon.string(),
    'zip': zon.string()
}).describe("Mailing address")
```

### Enum

```python
role = zon.enum(['admin', 'user', 'guest']) \
    .describe("User role")
```

---

## Optional Fields

```python
schema = zon.object({
    'name': zon.string(),                    # Required
    'email': zon.string().optional(),        # Optional
    'phone': zon.string().default('N/A')    # Optional with default
})
```

---

## Generate System Prompts

```python
schema = zon.object({
    'users': zon.array(zon.object({
        'id': zon.number(),
        'name': zon.string(),
        'role': zon.enum(['admin', 'user'])
    }))
})

prompt = schema.to_prompt()
print(prompt)
# object:
#   - users: array of [object]:
#     - id: number
#     - name: string
#     - role: enum(admin, user)
```

---

## Self-Correcting LLMs

Feed validation errors back to the LLM:

```python
def query_with_validation(llm, prompt, schema, max_retries=3):
    for attempt in range(max_retries):
        output = llm.query(prompt)
        result = validate(output, schema)
        
        if result.success:
            return result.data
        
        # Feed error back to LLM
        error_msg = f"Invalid format: {result.error}. Issues: {result.issues}"
        prompt = f"{prompt}\n\nPrevious attempt failed: {error_msg}. Please fix."
    
    raise ValueError("Failed after max retries")
```

---

## See Also

- [API Reference](api-reference.md)
- [LLM Best Practices](llm-best-practices.md)
