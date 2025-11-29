# Zero Overhead Notation (ZON) Format

[![PyPI version](https://img.shields.io/pypi/v/zon-format.svg)](https://pypi.org/project/zon-format/)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-93%2F93%20passing-brightgreen.svg)](#quality--testing)
[![License](https://img.shields.io/badge/license-Apache%202.0-green.svg)](LICENSE)

**Zero Overhead Notation** - A compact, human-readable way to encode JSON for LLMs.

**File Extension:** `.zonf` | **Media Type:** `text/zon` | **Encoding:** UTF-8

ZON is a token-efficient serialization format designed for LLM workflows. It achieves 35-50% token reduction vs JSON through tabular encoding, single-character primitives, and intelligent compression while maintaining 100% data fidelity.

> [!TIP]
> The ZON format is stable, but it's also an evolving concept. There's no finalization yet, so your input is valuable. Contribute to the spec or share your feedback to help shape its future.

---

## Table of Contents

- [Why ZON?](#why-zon)
- [Key Features](#key-features)
- [Installation & Quick Start](#installation--quick-start)
- [Format Overview](#format-overview)
- [API Reference](#api-reference)
- [Security & Data Types](#security--data-types)
- [Benchmarks](#benchmarks)

---

## Why ZON?

AI is becoming cheaper and more accessible, but larger context windows allow for larger data inputs as well. **LLM tokens still cost money** – and standard JSON is verbose and token-expensive:

```json
{
  "context": {
    "task": "Our favorite hikes together",
    "location": "Boulder",
    "season": "spring_2025"
  },
  "friends": ["ana", "luis", "sam"],
  "hikes": [
    {
      "id": 1,
      "name": "Blue Lake Trail",
      "distanceKm": 7.5,
      "elevationGain": 320,
      "companion": "ana",
      "wasSunny": true
    },
    ...
  ]
}
```

ZON conveys the same information with **fewer tokens** – using compact table format with explicit headers:

```
context:"{task:Our favorite hikes together,location:Boulder,season:spring_2025}"
friends:"[ana,luis,sam]"
hikes:@(3):companion,distanceKm,elevationGain,id,name,wasSunny
ana,7.5,320,1,Blue Lake Trail,T
luis,9.2,540,2,Ridge Overlook,F
sam,5.1,180,3,Wildflower Loop,T
```

---

## Key Features

- 🎯 **100% LLM Accuracy**: Achieves perfect retrieval with self-explanatory structure
- 💾 **Most Token-Efficient**: 15-35% fewer tokens than JSON across all tokenizers
- 🎯 **JSON Data Model**: Encodes the same objects, arrays, and primitives as JSON with deterministic, lossless round-trips
- 📐 **Minimal Syntax**: Explicit headers (`@(N)` for count, column list) eliminate ambiguity for LLMs
- 🧺 **Tabular Arrays**: Uniform arrays collapse into tables that declare fields once and stream row values
- 🔢 **Canonical Numbers**: No scientific notation (1000000, not 1e6), NaN/Infinity → null
- 🌳 **Deep Nesting**: Handles complex nested structures efficiently
- 🔒 **Security Limits**: Automatic DOS prevention (100MB docs, 1M arrays, 100K keys)
- ✅ **Production Ready**: 93/93 tests pass, all datasets verified, zero data loss

---

## Installation & Quick Start

### From PyPI (Recommended)

```bash
pip install zon-format
```

### Basic Usage

```python
import zon

# Your data
data = {
    "users": [
        {"id": 1, "name": "Alice", "role": "admin", "active": True},
        {"id": 2, "name": "Bob", "role": "user", "active": True}
    ]
}

# Encode to ZON
encoded = zon.encode(data)
print(encoded)
# users:@(2):active,id,name,role
# T,1,Alice,admin
# T,2,Bob,user

# Decode back
decoded = zon.decode(encoded)
assert decoded == data  # ✓ Lossless!
```

### Decode Options

```python
import zon

# Strict mode (default) - validates table structure
data = zon.decode(zon_string)

# Non-strict mode - allows row/field count mismatches
data = zon.decode(zon_string, strict=False)
```

### Error Handling

```python
from zon import decode, ZonDecodeError

try:
    data = decode(invalid_zon)
except ZonDecodeError as e:
    print(e.code)     # "E001" (row count) or "E002" (field count)
    print(e.message)  # Detailed error message
    print(e.context)  # Context information
```

---

## Format Overview

ZON auto-selects the optimal representation for your data.

### Tabular Arrays

Best for arrays of objects with consistent structure:

```
users:@(3):active,id,name,role
T,1,Alice,Admin
T,2,Bob,User
F,3,Carol,Guest
```

- `@(3)` = row count
- Column names listed once
- Data rows follow

### Nested Objects

Best for configuration and nested structures:

```
config:"{database:{host:db.example.com,port:5432},features:{darkMode:T}}"
```

### Compression Tokens

| Token | Meaning | JSON Equivalent |
|-------|---------|-----------------|
| `T` | Boolean true | `true` |
| `F` | Boolean false | `false` |
| `null` | Null value | `null` |

---

## API Reference

### `zon.encode(data)`

Encodes a Python object to ZON format.

**Parameters:**
- `data` (Any): The input data to encode. Must be JSON-serializable.

**Returns:**
- `str`: The ZON-encoded string.

**Raises:**
- `ZonEncodeError`: If circular reference detected.

**Example:**
```python
import zon
data = {"id": 1, "name": "Alice"}
zon_str = zon.encode(data)
```

### `zon.decode(zon_str, strict=True)`

Decodes a ZON-formatted string back to Python object.

**Parameters:**
- `zon_str` (str): The ZON-encoded string to decode.
- `strict` (bool): If True (default), validates table structure.

**Returns:**
- `Any`: The decoded Python object (dict or list).

**Raises:**
- `ZonDecodeError`: On validation errors or security limit violations.

**Error Codes:**
- `E001`: Row count mismatch (table has fewer/more rows than declared)
- `E002`: Field count mismatch (row has fewer fields than columns)
- `E301`: Document size exceeds 100MB
- `E302`: Line length exceeds 1MB
- `E303`: Array length exceeds 1M items
- `E304`: Object key count exceeds 100K

---

## Security & Data Types

### Eval-Safe Design

ZON is **immune to code injection attacks**:

✅ **No eval()** - Pure data format, zero code execution  
✅ **No object constructors** - Unlike YAML's exploit potential  
✅ **No prototype pollution** - Dangerous keys blocked (`__proto__`, `constructor`)  
✅ **Type-safe parsing** - Numbers parsed safely, not via `eval()`

### Data Type Preservation

- ✅ **Integers**: `42` stays integer
- ✅ **Floats**: `3.14` preserves decimal
- ✅ **Booleans**: Explicit `T`/`F` (not string `"true"`/`"false"`)
- ✅ **Null**: Explicit `null` (not omitted)
- ✅ **No scientific notation**: `1000000`, not `1e6`
- ✅ **Special values normalized**: `NaN`/`Infinity` → `null`

### Security Limits (DOS Prevention)

| Limit | Maximum | Error Code |
|-------|---------|------------|
| Document size | 100 MB | E301 |
| Line length | 1 MB | E302 |
| Array length | 1M items | E303 |
| Object keys | 100K keys | E304 |
| Nesting depth | 100 levels | - |

**Protection is automatic** - no configuration required.

---

## Benchmarks

### Retrieval Accuracy

Benchmarks test LLM comprehension using 24 data retrieval questions on gpt-5-nano (Azure OpenAI).

| Format | Accuracy | Tokens | Efficiency Score |
|--------|----------|--------|------------------|
| **ZON** | **100.0%** | 19,995 | 123.2 acc%/10K 👑 |
| TOON | 100.0% | 20,988 | 118.0 acc%/10K |
| CSV | 100.0% | ~20,500 | ~117 acc%/10K |
| JSON compact | 91.7% | 27,300 | 82.1 acc%/10K |
| JSON | 91.7% | 28,042 | 78.5 acc%/10K |

> ZON achieves **100% accuracy** (vs JSON's 91.7%) while using **29% fewer tokens**.

### Token Efficiency Benchmark

**Tokenizers:** GPT-4o (o200k), Claude 3.5 (Anthropic), Llama 3 (Meta)

#### Unified Dataset
```
GPT-4o (o200k):

    ZON          ██████████░░░░░░░░░░ 522 tokens 👑
    CSV          ██████████░░░░░░░░░░ 534 tokens (+2.3%)
    JSON (cmp)   ███████████░░░░░░░░░ 589 tokens (+11.4%)
    TOON         ███████████░░░░░░░░░ 614 tokens (+17.6%)
    YAML         █████████████░░░░░░░ 728 tokens (+39.5%)
    JSON format  ████████████████████ 939 tokens (+44.4%)
    XML          ████████████████████ 1,093 tokens (+109.4%)

Claude 3.5 (Anthropic): 

    CSV          ██████████░░░░░░░░░░ 544 tokens 👑
    ZON          ██████████░░░░░░░░░░ 545 tokens (+0.2%)
    TOON         ██████████░░░░░░░░░░ 570 tokens (+4.6%)
    JSON (cmp)   ███████████░░░░░░░░░ 596 tokens (+8.6%)
    YAML         ████████████░░░░░░░░ 641 tokens (+17.6%)

Llama 3 (Meta):

    ZON          ██████████░░░░░░░░░░ 701 tokens 👑
    CSV          ██████████░░░░░░░░░░ 728 tokens (+3.9%)
    JSON (cmp)   ███████████░░░░░░░░░ 760 tokens (+7.8%)
    TOON         ███████████░░░░░░░░░ 784 tokens (+11.8%)
    YAML         █████████████░░░░░░░ 894 tokens (+27.5%)
```

#### Large Complex Nested Dataset
```
GPT-4o (o200k):

    ZON          █████░░░░░░░░░░░░░░░ 147,267 tokens 👑
    CSV          ██████░░░░░░░░░░░░░░ 165,647 tokens (+12.5%)
    JSON (cmp)   ███████░░░░░░░░░░░░░ 189,193 tokens (+28.4%)
    TOON         █████████░░░░░░░░░░░ 225,510 tokens (+53.1%)
```

### Overall Summary

| Tokenizer | ZON vs TOON | ZON vs JSON |
|-----------|-------------|-------------|
| GPT-4o | **-34.7%** fewer tokens | **-22.2%** fewer tokens |
| Claude 3.5 | **-24.4%** fewer tokens | **-19.6%** fewer tokens |
| Llama 3 | **-25.7%** fewer tokens | **-15.3%** fewer tokens |

**Key Insight:** ZON is the only format that wins or nearly wins across all models & datasets.

---

## LLM Framework Integration

### OpenAI

```python
import zon
import openai

users = [{"id": i, "name": f"User{i}", "active": True} for i in range(100)]

# Compress with ZON (saves tokens = saves money!)
zon_data = zon.encode(users)

response = openai.ChatCompletion.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": "You will receive data in ZON format."},
        {"role": "user", "content": f"Analyze this user data:\n\n{zon_data}"}
    ]
)
```

### LangChain

```python
from langchain.llms import OpenAI
import zon

products = [{"name": "Laptop", "price": 999, "rating": 4.5}, ...]
zon_products = zon.encode(products)

# Use in your LangChain prompts with fewer tokens!
```

---

## Documentation

Comprehensive guides and references are available in the [`docs/`](./docs/) directory:

### 📖 [Syntax Cheatsheet](./docs/syntax-cheatsheet.md)
Quick reference for ZON format syntax with practical examples.
- Basic types and primitives (strings, numbers, booleans, null)
- Objects and nested structures
- Arrays (tabular, inline, mixed)
- Quoting rules and escape sequences
- Complete examples with JSON comparisons

### 🔧 [API Reference](./docs/api-reference.md)
Complete API documentation for `zon-format` v1.0.3.
- `encode()` function - detailed parameters and examples
- `decode()` function - strict mode options and error handling
- Python type definitions
- Error codes and security limits

### 📘 [Complete Specification](./docs/SPEC.md)
Comprehensive formal specification including:
- Data model and encoding rules
- Security model (DOS prevention, no eval)
- Data type system and preservation guarantees
- Conformance checklists
- Media type specification (`.zonf`, `text/zon`)

### 🤖 [LLM Best Practices](./docs/llm-best-practices.md)
Guide for maximizing ZON's effectiveness in LLM applications.
- Prompting strategies for LLMs
- Common use cases (data retrieval, aggregation, filtering)
- Optimization tips for token usage
- Model-specific tips (GPT-4, Claude, Llama)
- Complete real-world examples

---

## Quality & Testing

### Test Coverage

- **Unit tests:** 93/93 passed (security, conformance, validation)
- **Roundtrip tests:** 13/13 datasets verified
- **No data loss or corruption**

### Validation (Strict Mode)

Enabled by default - validates table structure:

```python
# Strict mode (default)
data = zon.decode(zon_string)

# Non-strict mode
data = zon.decode(zon_string, strict=False)
```

---

## Links

- [PyPI Package](https://pypi.org/project/zon-format/)
- [GitHub Repository](https://github.com/ZON-Format/ZON)
- [GitHub Issues](https://github.com/ZON-Format/ZON/issues)
- [TypeScript Implementation](https://github.com/ZON-Format/zon-TS)

---

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Submit a pull request

---

## License

**Apache 2.0 License**

Copyright (c) 2025 ZON-FORMAT (Roni Bhakta)

See [LICENSE](LICENSE) for details.

---

**Made with ❤️ for the LLM community**

*ZON v1.0.3 - Token efficiency that scales with complexity*
