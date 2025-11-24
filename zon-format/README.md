# ZON Format v8.0 (ClearText)

**Zero-Overhead Notation** - A human-readable, LLM-optimized data format that achieves **30%+ compression** over JSON while remaining visually clean and intuitive.

[![PyPI version](https://badge.fury.io/py/zon-format.svg)](https://pypi.org/project/zon-format/)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

## Why ZON?

ZON v8.0 "ClearText" combines the **readability of YAML** with the **compression efficiency** better than TOON, producing output that looks like structured documents rather than escaped protocols.

### Performance

- ✅ **31.9% smaller** than JSON on average
- ✅ **25.6% better** than TOON across benchmarks
- ✅ **Zero protocol overhead** - no pipes, markers, or complex headers
- ✅ **LLM-friendly** - readable without knowing the format

## Quick Example

**Input (JSON)**:
```json
{
  "context": "Hiking Trip",
  "friends": ["ana", "luis", "sam"],
  "hikes": [
    {"id": 1, "name": "Blue Lake Trail", "sunny": true},
    {"id": 2, "name": "Ridge Overlook", "sunny": false}
  ]
}
```

**Output (ZON v8.0)**:
```
context:Hiking Trip
friends:[ana,luis,sam]

@hikes(2):id,name,sunny
1,Blue Lake Trail,T
_,Ridge Overlook,F
```

**Size**: JSON: 201 bytes → ZON: 106 bytes (**47% smaller**)

## Installation

```bash
pip install zon-format
```

## Usage

```python
import zon

# Encode
data = {"users": [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]}
encoded = zon.encode(data)
print(encoded)
# Output:
# @users(2):id,name
# 1,Alice
# _,Bob

# Decode
decoded = zon.decode(encoded)
assert decoded == data  # Perfect roundtrip
```

## Format Reference

### Metadata (YAML-like)

```
key:value
nested.key:value
list:[item1,item2,item3]
```

- No spaces after `:` for compactness
- Dot notation for nested objects
- Minimal quoting (only when necessary)

### Tables (@table syntax)

```
@tablename(count):col1,col2,col3
val1,val2,val3
val1,val2,val3
```

- `@` marks table start
- `(count)` shows row count
- Columns separated by commas (no spaces)

### Compression Tokens

| Token | Meaning | Example |
|-------|---------|---------|
| `T` | Boolean true | `T` instead of `true` |
| `F` | Boolean false | `F` instead of `false` |

> **Note**: ZON v1.0.1 prioritizes **explicit data**. Compression tokens like `^` (repeat) and `_` (auto-increment) are disabled to ensure every row contains its full, actual data.

### Smart Quoting

Quotes are **only added when necessary**:

| Value | Encoded | Reason |
|-------|---------|--------|
| `ana` | `ana` | No special chars |
| `Blue Lake` | `Blue Lake` | Spaces OK |
| `a,b` | `"a,b"` | Contains comma (delimiter) |
| `Hello: World` | `Hello: World` | Colons OK |

## Format Comparison

### Random Users API (10 records)

**JSON** (15,026 bytes):
```json
[
  {
    "gender": "female",
    "name": {"title": "Ms", "first": "Sophia", "last": "Wilson"},
    "location": {"city": "Austin", "state": "Texas"},
    ...
  }
]
```

**TOON** (10,626 bytes):
```
results[50]{gender,name{title,first,last},location{city,state},...}
female,Ms,Sophia,Wilson,Austin,Texas,...
```

**ZON v8.0** (6,767 bytes - **55% smaller than JSON**):
```
@data(10):gender,location.city,location.state,name.first,name.last,name.title
female,Austin,Texas,Sophia,Wilson,Ms
^,^,^,Emma,Johnson,Mrs
male,Portland,Oregon,Liam,Brown,Mr
...
```

## Benchmarks

Run the comprehensive benchmark suite:

```bash
python benchmarks/generate_datasets.py  # Generate test data
python test_comprehensive.py            # Run benchmarks
```

### Results (318 records across 6 datasets)

| Dataset | Records | vs JSON | vs TOON |
|---------|---------|---------|---------|
| Random Users API | 50 | **-42.4%** | **+40.4%** |
| StackOverflow Q&A | 50 | **-43.1%** | **+41.1%** |
| JSONPlaceholder Posts | 100 | **-13.4%** | **-0.1%** |
| JSONPlaceholder Comments | 100 | **-15.4%** | **+0.0%** |
| JSONPlaceholder Users | 10 | **-40.3%** | **+36.3%** |
| GitHub Repos | 8 | **-37.1%** | **+36.0%** |
| **AVERAGE** | | **-31.9%** | **+25.6%** |

### View Encoded Samples

Compare formats side-by-side:

```bash
python benchmarks/generate_samples.py
# Generates .json, .zon, and .toon files in benchmarks/encoded_samples/
```

Open any `.zon` file to see the clean, readable output!

## How It Works

### 1. Root Promotion

ZON automatically separates **metadata** (context) from **data** (tables):

```json
{"context": "Trip", "hikes": [{...}, {...}]}
```
↓
```
context:Trip

@hikes(2):...
```


### 3. Intelligent Compression

- **Sequential IDs**: `1,_,_` (auto-increment)
- **Repetitive values**: Uses `^` token
- **Booleans**: `T`/`F` (1 byte vs 4-5 bytes)
- **No quotes**: Unless value contains `,` or control chars

## Using with LLMs

ZON is designed to be token-efficient for LLMs. When feeding ZON data to an LLM, you can use this system prompt to ensure perfect understanding:

> "Data is in ZON format. It is a CSV-like format where `T`/`F` are booleans and nested objects use `{key:val}` syntax."

**Why Explicit Data?**
ZON v1.0.1 writes every value explicitly (no "ditto" marks). This ensures that:
1. **IDs are never obscured**: Unique identifiers are always present.
2. **Context is preserved**: LLMs don't need to "look back" to resolve values.
3. **Structure is exact**: Nested objects are kept together, preserving the exact sequence of your data.

## CLI Tool

```bash
# Encode
zon encode input.json output.zon

# Decode
zon decode input.zon output.json

# Benchmark
zon benchmark data.json
```

## Development

```bash
# Install in development mode
pip install -e .

# Run tests
python -m pytest tests/

# Run benchmarks
python test_comprehensive.py
```

## Version History

### v1.0.1 (2025-11-24) - "ClearText"

- ✅ Removed protocol overhead (no more `#Z:`, pipes, or markers)
- ✅ YAML-like metadata syntax (`key:value`)
- ✅ Clean @table syntax
- ✅ Aggressive quote removal (spaces no longer trigger quoting)
- ✅ Compact array syntax: `[item1,item2,item3]`
- ✅ Optimized nested data: `{key:val}` syntax (no more JSON strings)
- ✅ 31.9% compression vs JSON, 25.6% better than TOON

### v1.0.0 (2025-11-23)

- Initial release with pipe-based protocol syntax

## License

Apache License 2.0 - see [LICENSE](LICENSE) file

## Contributing

Contributions welcome! Please open an issue or PR on GitHub.

---

**Made with ❤️ for efficient data transmission and LLM optimization**
