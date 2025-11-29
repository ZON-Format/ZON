# ZON Syntax Cheatsheet

Copyright (c) 2025 ZON-FORMAT (Roni Bhakta)

Quick reference for ZON format syntax. Cross-referenced with actual implementation in v1.0.3.

## Basic Types

### Primitives

```zon
# String (unquoted when safe)
name:Alice

# Number
score:98.5
count:42

# Boolean (T/F)
active:T
disabled:F

# Null
value:null
```

### Objects

```zon
# Simple object
name:ZON Format
version:1.0.3
active:T
score:98.5
```

**JSON equivalent:**
```json
{
  "name": "ZON Format",
  "version": "1.0.3",
  "active": true,
  "score": 98.5
}
```

### Nested Objects

```zon
# Nested quoted
config:"{database:{host:localhost,port:5432},cache:{ttl:3600,enabled:T}}"
```

**JSON equivalent:**
```json
{
  "config": {
    "database": { "host": "localhost", "port": 5432 },
    "cache": { "ttl": 3600, "enabled": true }
  }
}
```

---

## Arrays

### Primitive Arrays (Inline)

```zon
tags:"[python,llm,zon]"
numbers:"[1,2,3,4,5]"
flags:"[T,F,T]"
```

### Tabular Arrays (Uniform Objects)

**Most efficient form - ZON's specialty**

```zon
users:@(3):active,id,name,role
T,1,Alice,admin
T,2,Bob,user
F,3,Carol,guest
```

**Breakdown:**
- `@(3)` = 3 rows
- `:active,id,name,role` = column headers
- Data rows follow

**JSON equivalent:**
```json
{
  "users": [
    { "id": 1, "name": "Alice", "role": "admin", "active": true },
    { "id": 2, "name": "Bob", "role": "user", "active": true },
    { "id": 3, "name": "Carol", "role": "guest", "active": false }
  ]
}
```

### Mixed / Non-Uniform Arrays

```zon
# Quoted as JSON array
items:"[{id:1,name:Alice},{id:2,name:Bob,role:admin}]"
```

### Empty Containers

```zon
# Empty object
metadata:"{}"

# Empty array
tags:"[]"
```

---

## Quoting Rules

### When Strings NEED Quotes

1. **Contains special characters**:
   - Commas: `"hello, world"`
   - Colons: `"key:value"`
   - Brackets: `"[test]"`
   - Braces: `"{test}"`

2. **Looks like a literal**:
   - `"true"` (string, not boolean)
   - `"123"` (string, not number)
   - `"false"` (string, not boolean)
   - `"null"` (string, not null)

3. **Leading/trailing spaces**:
   - `" padded "`

4. **Empty string**:
   - `""` (MUST quote, otherwise parses as `null`)

### Safe Unquoted Strings

```zon
# Alphanumeric + dash, underscore, dot
name:john-doe
file:data_v1.json
host:api.example.com
```

---

## Table Headers

### Basic Header (without count)

```zon
users:@:id,name,active
1,Alice,T
2,Bob,F
```

### Full Header (with count)

```zon
users:@(2):id,name,active
1,Alice,T
2,Bob,F
```

**Best practice**: Always include count `@(N)` for explicit schema

---

## Type Conversions

| ZON | Python | Notes |
|-----|--------|-------|
| `T` | `True` | Boolean true |
| `F` | `False` | Boolean false |
| `null` | `None` | Null value |
| `42` | `42` | Number (integer) |
| `3.14` | `3.14` | Number (float) |  
| `hello` | `"hello"` | Unquoted string |
| `"hello"` | `"hello"` | Quoted string |

---

## Common Patterns

### Config with nested data

```zon
environment:production
version:"1.0.3"
database:"{host:db.example.com,port:5432,ssl:T}"
features:"{darkMode:F,betaAccess:T}"
```

### Mixed structure (tables + metadata)

```zon
created:"2025-11-28"
total:150
users:@(3):id,name,status
1,Alice,active
2,Bob,inactive
3,Carol,active
```

### Root-level table

```zon
@(2):id,name,active
1,Alice,T
2,Bob,F
```

---

##  Escape Sequences

Within quoted strings:
- `\"` - Double quote
- `\\` - Backslash
- `\n` - Newline
- `\r` - Carriage return
- `\t` - Tab

**Example:**
```zon
message:"Line 1\nLine 2"
path:"C:\\Users\\data"
```

---

## Complete Example

**JSON:**
```json
{
  "metadata": { "version": "1.0.3", "env": "production" },
  "users": [
    { "id": 1, "name": "Alice", "active": true, "loginCount": 42 },
    { "id": 2, "name": "Bob", "active": true, "loginCount": 17 },
    { "id": 3, "name": "Carol", "active": false, "loginCount": 3 }
  ],
  "config": { "database": { "host": "localhost", "port": 5432 } }
}
```

**ZON:**
```zon
metadata:"{version:1.0.3,env:production}"
users:@(3):active,id,loginCount,name
T,1,42,Alice
T,2,17,Bob
F,3,3,Carol
config:"{database:{host:localhost,port:5432}}"
```

**Token count:**
- JSON (formatted): 151 tokens
- ZON: 87 tokens  
- **Savings: 42% fewer tokens**

---

## Tips for LLMs

1. **Use code blocks**: Wrap ZON in ` ```zon` for syntax highlighting
2. **No hints needed**: Format is self-documenting
3. **Explicit headers**: `@(N)` count helps LLMs validate
4. **Column names**: Listed once, clear schema

**Example prompt:**
````
Here's the data in ZON format:

```zon
users:@(3):id,name,active
1,Alice,T
2,Bob,F
3,Carol,T
```

Question: How many active users are there?
````

---

## Quick Comparison

| Feature | JSON | TOON | ZON |
|---------|------|------|-----|
| **Uniform arrays** | Verbose | Tabular | Tabular |
| **Nested objects** | Native | Quoted | Quoted |
| **Booleans** | `true`/`false` | `true`/`false` | `T`/`F` |
| **Null** | `null` | `null` | `null` |
| **Headers** | No | `[N]{fields}` | `@(N):fields` |
| **LLM accuracy** | 91.7% | 100% | **100%** ✅ |
| **Tokens (unified)** | 28,042 | 20,988 | **19,995** 👑 |

---

**See also:**
- [Format Specification](./SPEC.md) - Formal grammar
- [API Reference](./api-reference.md) - encode/decode functions
- [LLM Best Practices](./llm-best-practices.md) - Usage guide
