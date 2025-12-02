# CLI Guide

**Version:** 1.1.0

## Installation

The `zon` command is installed automatically with the package:

**Using pip:**
```bash
pip install zon-format
```

**Using UV (faster):**
```bash
uv pip install zon-format
# or
uv add zon-format
```

**Verify installation:**
```bash
zon --version
# zon-format 1.1.0
```

---

## Commands

### `encode`

Convert JSON to ZON format.

**Usage:**
```bash
zon encode <input_file> [-o <output_file>]
```

**Examples:**
```bash
# Encode JSON file
zon encode data.json > data.zonf

# Encode with output file
zon encode data.json -o data.zonf

# Encode from stdin
cat data.json | zon encode > data.zonf
```

---

### `decode`

Convert ZON to JSON format.

**Usage:**
```bash
zon decode <input_file> [-o <output_file>]
```

**Examples:**
```bash
# Decode ZON file
zon decode data.zonf > data.json

# Decode with output file
zon decode data.zonf -o data.json

# Decode from stdin
cat data.zonf | zon decode > data.json
```

---

### `validate`

Validate ZON file structure.

**Usage:**
```bash
zon validate <input_file>
```

**Example:**
```bash
zon validate data.zonf
# ✅ Valid ZON format
# 📊 3 tables, 150 total rows
```

---

### `stats`

Show compression statistics.

**Usage:**
```bash
zon stats <json_file>
```

**Example:**
```bash
zon stats users.json

# 📊 ZON Statistics
# ==================
# Original JSON:  2,842 bytes (939 tokens)
# ZON Format:     1,399 bytes (513 tokens)
# Compression:    50.8% size reduction
# Token Savings:  45.4% fewer tokens
```

---

### `format`

Canonicalize ZON output.

**Usage:**
```bash
zon format <input_file>
```

**Purpose:** Ensures consistent formatting for diffs.

**Example:**
```bash
zon format data.zonf > canonical.zonf
```

---

## File Extensions

### `.zonf`

The conventional file extension for ZON files:

```bash
# Encode
zon encode users.json > users.zonf

# Decode
zon decode users.zonf > users.json
```

---

## Pipe Usage

### Chain Commands

```bash
# Compress multiple files
for file in *.json; do
    zon encode "$file" > "${file%.json}.zonf"
done

# Validate all ZON files
find . -name "*.zonf" -exec zon validate {} \;

# Convert ZON to JSON for processing
zon decode data.zonf | jq '.users[] | select(.active == true)'
```

---

## Options

### Common Options

| Option | Description |
|--------|-------------|
| `-h, --help` | Show help message |
| `-v, --version` | Show version |
| `-o, --output` | Output file (instead of stdout) |
| `--pretty` | Pretty-print JSON output |

### Encoding Options

| Option | Description |
|--------|-------------|
| `--no-dict` | Disable dictionary compression |
| `--no-delta` | Disable delta encoding |
| `--coerce` | Enable type coercion |

**Example:**
```bash
# Encode without dictionary compression
zon encode --no-dict data.json > data.zonf

# Encode with type coercion
zon encode --coerce llm_output.json > output.zonf
```

### Decoding Options

| Option | Description |
|--------|-------------|
| `--no-strict` | Disable strict validation |
| `--coerce` | Enable type coercion |

**Example:**
```bash
# Decode with relaxed validation
zon decode --no-strict data.zonf > data.json

# Decode with type coercion
zon decode --coerce llm_output.zonf > data.json
```

---

## Examples

### Convert API Response

```bash
# Fetch API data and convert to ZON
curl https://api.example.com/users | zon encode > users.zonf

# Later, decode for processing
zon decode users.zonf | python process.py
```

### Compress LLM Context

```bash
# Before: Large JSON context
cat context.json
# 15,234 bytes

# After: Compressed ZON
zon encode context.json > context.zonf
cat context.zonf
# 8,912 bytes (41.5% savings)
```

### Validate LLM Output

```bash
# LLM generates ZON
llm_generate.sh > output.zonf

# Validate format
zon validate output.zonf
# ✅ Valid

# Convert to JSON
zon decode output.zonf > output.json
```

---

## See Also

- [API Reference](api-reference.md) - Python API
- [LLM Best Practices](llm-best-practices.md) - Using ZON with LLMs
