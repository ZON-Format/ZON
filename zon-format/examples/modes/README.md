# ZON Encoding Mode Examples

This directory contains examples demonstrating the three encoding modes available in ZON v1.2.0.

## Files

- **source.json** - Original JSON data
- **compact.zonf** - Compact mode (maximum compression)
- **readable.zonf** - Readable mode (human-friendly)
- **llm-optimized.zonf** - LLM-optimized mode (balanced)

## Mode Comparison

### Source Data (JSON)

```json
{
  "users": [
    {"id": 1, "name": "Alice Smith", "role": "admin", "active": true, ...},
    {"id": 2, "name": "Bob Jones", "role": "user", "active": true, ...},
    {"id": 3, "name": "Carol White", "role": "guest", "active": false, ...}
  ],
  "metadata": {
    "version": "1.2.0",
    "timestamp": "2024-12-07T08:00:00Z",
    "source": "demo"
  }
}
```

**Size:** 435 bytes (formatted)

### Compact Mode

```zon
metadata{source:demo,timestamp:2024-12-07T08:00:00Z,version:1.2.0}

users:@(3):active,email,id,name,role
T,alice@example.com,1,Alice Smith,admin
T,bob@example.com,2,Bob Jones,user
F,carol@example.com,3,Carol White,guest
```

**Size:** 187 bytes  
**Savings:** 57% vs JSON

**Features:**
- Uses `T`/`F` for booleans (saves tokens)
- Table format for uniform data
- Maximum compression

### LLM-Optimized Mode

```zon
metadata{source:demo,timestamp:2024-12-07T08:00:00Z,version:1.2.0}

users:@(3):active,email,id,name,role
T,alice@example.com,1.0,Alice Smith,admin
T,bob@example.com,2.0,Bob Jones,user
F,carol@example.com,3.0,Carol White,guest
```

**Size:** 193 bytes  
**Savings:** 56% vs JSON

**Features:**
- Still uses `T`/`F` (can be configured to use `true`/`false`)
- Type coercion enabled
- Balanced for LLM understanding

### Readable Mode

Similar to compact but with potential formatting improvements for human readability.

## Usage

### Generate Examples

```python
from zon import encode_adaptive, AdaptiveEncodeOptions
import json

# Load data
with open('source.json') as f:
    data = json.load(f)

# Encode in different modes
compact = encode_adaptive(data, AdaptiveEncodeOptions(mode='compact'))
readable = encode_adaptive(data, AdaptiveEncodeOptions(mode='readable'))
llm = encode_adaptive(data, AdaptiveEncodeOptions(mode='llm-optimized'))
```

### CLI Commands

```bash
# Analyze the data
zon analyze source.json --compare

# Encode in compact mode (default)
zon encode source.json -m compact > compact.zonf

# Encode in LLM-optimized mode
zon encode source.json -m llm-optimized > llm-optimized.zonf

# Encode in readable mode
zon encode source.json -m readable > readable.zonf

# Decode back to JSON
zon decode compact.zonf --pretty > output.json
```

## When to Use Each Mode

| Mode | Use Case | Best For |
|------|----------|----------|
| **compact** | Production APIs | Maximum token savings, cost-sensitive LLM workflows |
| **llm-optimized** | AI workflows | Balanced token efficiency and LLM comprehension |
| **readable** | Config files | Human editing, debugging, version control |

## See Also

- [Adaptive Encoding Guide](../../docs/adaptive-encoding.md)
- [API Reference](../../docs/api-reference.md)
- [Syntax Cheatsheet](../../docs/syntax-cheatsheet.md)
