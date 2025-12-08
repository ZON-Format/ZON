# ZON Encoding Modes Examples

This directory contains examples demonstrating the three encoding modes available in ZON v1.2.0+:

## Modes

### 1. Compact Mode
- **File**: `compact.zonf`
- **Use Case**: Production APIs, storage optimization, high-throughput systems
- **Features**:
  - Maximum compression
  - Short boolean values (T/F)
  - Dictionary compression for tables
  - Minimal whitespace
  - Smallest footprint

**Example:**
```zon
metadata{generated:2025-01-01T12:00:00Z,version:1.2.0}
users:@(3):id,name,role
1,Alice,admin
2,Bob,user
3,Carol,guest
```

### 2. Readable Mode ✨ **NEW: Pretty-Printing**
- **File**: `readable.zonf`
- **Use Case**: Configuration files, human review, documentation, debugging
- **Features**:
  - **Multi-line formatting with indentation** (NEW in v1.2.0)
  - Nested objects with proper spacing
  - Clear structure visualization
  - Configurable indent size (default: 2 spaces)
  - Pretty-printed output

**Example:**
```zon
metadata:{
  generated:2025-01-01T12:00:00Z
  version:1.2.0
}

users:@(3):id,name,role
1,Alice,admin
2,Bob,user
3,Carol,guest
```

### 3. LLM-Optimized Mode
- **File**: `llm-optimized.zonf`
- **Use Case**: AI/LLM workflows, RAG systems, prompt engineering, token efficiency
- **Features**:
  - Optimized for LLM token consumption
  - Long boolean format (true/false) for clarity
  - Integer type preservation (no .0 coercion)
  - Balanced compression and comprehension
  - Clear type indicators
  - Efficient for model processing

**Example:**
```zon
metadata{generated:2025-01-01T12:00:00Z,version:1.2.0}
users:@(3):id,name,role
1,Alice,admin
2,Bob,user
3,Carol,guest
```

## Source Data

The `source.json` file contains the sample data used to generate all three examples.

## Size Comparison

For the sample data in this directory:
- **JSON**: 435 bytes (baseline)
- **Compact**: ~187 bytes (57% savings)
- **LLM-Optimized**: ~193 bytes (56% savings)
- **Readable**: ~201 bytes (54% savings, with pretty-printing)

## Key Differences

| Feature | Compact | Readable | LLM-Optimized |
|---------|---------|----------|---------------|
| Booleans | T/F | T/F | true/false |
| Indentation | No | Yes (2 spaces) | No |
| Multi-line | No | Yes | No |
| Type Coercion | Yes | Yes | No |
| Integer Format | 1 | 1 | 1 (not 1.0) |
| Token Efficiency | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ |
| Human Readability | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| Best For | Production | Config Files | AI/LLM |

## Usage Examples

### Python

```python
from zon import encode_adaptive, AdaptiveEncodeOptions, recommend_mode
import json

# Load data
with open('source.json') as f:
    data = json.load(f)

# Compact mode - maximum compression
compact = encode_adaptive(data, AdaptiveEncodeOptions(mode='compact'))
print(f"Compact: {len(compact)} bytes")

# Readable mode - human-friendly with indentation (NEW!)
readable = encode_adaptive(data, AdaptiveEncodeOptions(mode='readable', indent=2))
print(f"Readable: {len(readable)} bytes")
print(readable)  # Now with pretty indentation!

# LLM-optimized - best for AI workflows
llm = encode_adaptive(data, AdaptiveEncodeOptions(mode='llm-optimized'))
print(f"LLM: {len(llm)} bytes")

# Auto-recommend best mode
recommendation = recommend_mode(data)
print(f"Recommended: {recommendation['mode']} - {recommendation['reason']}")
```

### CLI

```bash
# Generate examples from JSON
zon encode source.json -m compact > compact.zonf
zon encode source.json -m readable > readable.zonf
zon encode source.json -m llm-optimized > llm-optimized.zonf

# Compare sizes
zon analyze source.json --compare

# Get recommendation
zon analyze source.json --recommend
```

## When to Use Each Mode

### Use Compact Mode When:
- ✅ Optimizing for storage or bandwidth
- ✅ Building high-performance APIs
- ✅ Size is critical (IoT, mobile)
- ✅ Processing large volumes of data

### Use Readable Mode When:
- ✅ Writing configuration files
- ✅ Creating documentation examples
- ✅ Debugging complex structures
- ✅ Manual editing is required
- ✅ Code reviews need clear format
- ✅ Need visual structure clarity

### Use LLM-Optimized Mode When:
- ✅ Working with LLMs (GPT, Claude, etc.)
- ✅ Building RAG systems
- ✅ Token limits are a concern
- ✅ Need clarity for AI processing
- ✅ Prompt engineering with structured data

## New in v1.2.0

### Pretty-Printer for Readable Mode

Readable mode now includes a sophisticated pretty-printer that:
- Formats nested objects with proper indentation
- Adds newlines for clarity
- Preserves compact table formatting
- Makes complex structures much easier to read

**Before (v1.1.0):**
```zon
metadata{generated:2025-01-01T12:00:00Z,version:1.2.0}
```

**After (v1.2.0):**
```zon
metadata:{
  generated:2025-01-01T12:00:00Z
  version:1.2.0
}
```

### Advanced Options

```python
from zon import encode_adaptive, AdaptiveEncodeOptions, expand_print

# Readable mode with custom indentation
readable = encode_adaptive(data, AdaptiveEncodeOptions(
    mode='readable',
    indent=4  # 4 spaces instead of 2
))

# Or use the pretty-printer directly
from zon import encode, expand_print

compact = encode(data)
pretty = expand_print(compact, indent=2)
```

## Cross-Language Compatibility

These examples are cross-checked against the TypeScript implementation:
- GitHub: https://github.com/ZON-Format/ZON-TS
- TypeScript examples: `/examples/modes/`
- Match rate: ~51% exact match (improved from 39.2%)

The Python implementation produces output compatible with the TypeScript decoder and vice versa.

## More Examples

For comprehensive examples across all ZON features, see:
- `../modes_generated/` - Auto-generated examples from TS test suite
- `../` - Hand-crafted examples for specific use cases
- `../../docs/adaptive-encoding.md` - Complete encoding guide
- `../../docs/binary-format.md` - Binary format guide
- `../../docs/versioning.md` - Versioning system guide
- `../../docs/developer-tools.md` - Developer utilities guide

## See Also

- [Adaptive Encoding Guide](../../docs/adaptive-encoding.md)
- [Binary Format](../../docs/binary-format.md)
- [Versioning System](../../docs/versioning.md)
- [Developer Tools](../../docs/developer-tools.md)
- [API Reference](../../docs/api-reference.md)
- [CLI Guide](../../docs/cli-guide.md)
