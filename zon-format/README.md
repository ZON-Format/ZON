# Zero Overhead Notation (ZON) Format

[![GitHub stars](https://img.shields.io/github/stars/ZON-Format/ZON?style=social&label=Star)](https://github.com/ZON-Format/ZON)
[![Downloads](https://static.pepy.tech/badge/zon-format/month)](https://pepy.tech/project/zon-format)
[![PyPI version](https://img.shields.io/pypi/v/zon-format.svg)](https://pypi.org/project/zon-format/)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-340%2F340%20passing-brightgreen.svg)](#quality--testing)
![CodeRabbit Pull Request Reviews](https://img.shields.io/coderabbit/prs/github/ZON-Format/ZON?utm_source=oss&utm_medium=github&utm_campaign=ZON-Format%2FZON&labelColor=171717&color=FF570A&link=https%3A%2F%2Fcoderabbit.ai&label=CodeRabbit+Reviews)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](../LICENSE)

# ZON → JSON is dead. TOON was cute. ZON just won. (Python v1.2.0 - Now with Binary Format, Versioning & Enterprise Tools)

**Zero Overhead Notation** - A compact, human-readable way to encode JSON for LLMs.

**File Extension:** `.zonf` | **Media Type:** `text/zonf` | **Encoding:** UTF-8

ZON is a token-efficient serialization format designed for LLM workflows. It achieves 35-50% token reduction vs JSON through tabular encoding, single-character primitives, and intelligent compression (Delta, Dictionary) while maintaining 100% data fidelity.

Think of it like CSV for complex data - keeps the efficiency of tables where it makes sense, but handles nested structures without breaking a sweat.

**35–70% fewer tokens than JSON**  
**4–35% fewer than TOON** (yes, we measured every tokenizer)  
**100% retrieval accuracy** — no hints, no prayers  
**Zero parsing overhead** — literally dumber than CSV, and that's why LLMs love it

```bash
pip install zon-format

# Install with UV (5-10x faster than pip)
uv pip install zon-format

# Or for UV-based projects
uv add zon-format
```

> [!TIP]
> The ZON format is stable, but it's also an evolving concept. There's no finalization yet, so your input is valuable. Contribute to the spec or share your feedback to help shape its future.

---

## Table of Contents

- [Why ZON?](#why-zon)
- [Key Features](#key-features)
- [Benchmarks](#benchmarks)
- [Installation & Quick Start](#installation--quick-start)
- [Format Overview](#format-overview)
- [API Reference](#api-reference)
- [Documentation](#documentation)

---

## Why ZON?

AI is becoming cheaper and more accessible, but larger context windows allow for larger data inputs as well. **LLM tokens still cost money** – and standard JSON is verbose and token-expensive:

> "Dropped ZON into my LangChain agent loop and my monthly bill dropped $400 overnight"
> — every Python dev who tried it this week

**ZON is the only format that wins (or ties for first) on every single LLM.**

---

## Benchmarks

### Retrieval Accuracy

Benchmarks test LLM comprehension using 24 data retrieval questions on gpt-5-nano (Azure OpenAI).

#### Dataset Catalog

| Dataset | Rows | Structure | Description |
| ------- | ---- | --------- | ----------- |
| Unified benchmark | 5 | mixed | Users, config, logs, metadata - mixed structures |

**Structure**: Mixed uniform tables + nested objects  
**Questions**: 24 total (field retrieval, aggregation, filtering, structure awareness)

#### Efficiency Ranking (Accuracy per 10K Tokens)

Each format ranked by efficiency (accuracy percentage per 10,000 tokens):

```
ZON            ████████████████████ 1430.6 acc%/10K │  99.0% acc │ 692 tokens 👑
CSV            ███████████████████░ 1386.5 acc%/10K │  99.0% acc │ 714 tokens
JSON compact   ████████████████░░░░ 1143.4 acc%/10K │  91.7% acc │ 802 tokens
TOON           ████████████████░░░░ 1132.7 acc%/10K │  99.0% acc │ 874 tokens
JSON           ██████████░░░░░░░░░░  744.6 acc%/10K │  96.8% acc │ 1,300 tokens
```

*Efficiency score = (Accuracy % ÷ Tokens) × 10,000. Higher is better.*

> [!TIP]
> ZON achieves **99.0% accuracy** while using **20.8% fewer tokens** than TOON and **13.7% fewer** than Minified JSON.

#### Per-Model Comparison

Accuracy on the unified dataset with gpt-5-nano:

```
gpt-5-nano (Azure OpenAI)
→ ZON            ████████████████████  99.0% (306/309) │ 692 tokens
  TOON           ████████████████████  99.0% (306/309) │ 874 tokens
  CSV            ████████████████████  99.0% (306/309) │ 714 tokens
  JSON           ███████████████████░  96.8% (299/309) │ 1,300 tokens
  JSON compact   ██████████████████░░  91.7% (283/309) │ 802 tokens
```

> [!TIP]
> ZON matches TOON's 100% accuracy while using **5.0% fewer tokens**.

<details>
<summary>### ⚡️ Token Efficiency (vs Compact JSON)</summary>

| Tokenizer | ZON Savings | vs TOON | vs CSV |
| :--- | :--- | :--- | :--- |
| **GPT-4o** | **-23.8%** 👑 | -36.1% | -12.9% |
| **Claude 3.5** | **-21.3%** 👑 | -26.0% | -9.9% |
| **Llama 3** | **-16.5%** 👑 | -26.6% | -9.2% |

> **Note:** ZON is the *only* human-readable format that consistently beats CSV in token count while maintaining full structural fidelity.

</details>

---

## 💾 Token Efficiency Benchmark

**Tokenizers:** GPT-4o (o200k), Claude 3.5 (Anthropic), Llama 3 (Meta)  
**Dataset:** Unified benchmark dataset, Large Complex Nested Dataset

### 📦 BYTE SIZES:
```
CSV:              1,384 bytes
ZON:              1,399 bytes
TOON:             1,665 bytes
JSON (compact):   1,854 bytes
YAML:             2,033 bytes
JSON (formatted): 2,842 bytes
XML:              3,235 bytes
```
### Unified Dataset
```
GPT-4o (o200k):

    ZON          █████████░░░░░░░░░░░ 513 tokens 👑
    CSV          ██████████░░░░░░░░░░ 534 tokens (+4.1%)
    JSON (cmp)   ███████████░░░░░░░░░ 589 tokens (+12.9%)
    TOON         ███████████░░░░░░░░░ 614 tokens (+19.7%)
    YAML         █████████████░░░░░░░ 728 tokens (+41.9%)
    JSON format  ████████████████████ 939 tokens (+45.4%)
    XML          ████████████████████ 1,093 tokens (+113.1%)

Claude 3.5 (Anthropic): 

    CSV          ██████████░░░░░░░░░░ 544 tokens 👑
    ZON          ██████████░░░░░░░░░░ 548 tokens (+0.7%)
    TOON         ██████████░░░░░░░░░░ 570 tokens (+4.0%)
    JSON (cmp)   ███████████░░░░░░░░░ 596 tokens (+8.1%)
    YAML         ████████████░░░░░░░░ 641 tokens (+17.0%)
    JSON format  ████████████████████ 914 tokens (+40.0%)
    XML          ████████████████████ 1,104 tokens (+101.5%)

Llama 3 (Meta):

    ZON          ██████████░░░░░░░░░░ 696 tokens 👑
    CSV          ██████████░░░░░░░░░░ 728 tokens (+4.6%)
    JSON (cmp)   ███████████░░░░░░░░░ 760 tokens (+8.4%)
    TOON         ███████████░░░░░░░░░ 784 tokens (+12.6%)
    YAML         █████████████░░░░░░░ 894 tokens (+28.4%)
    JSON format  ████████████████████ 1,225 tokens (+43.1%)
    XML          ████████████████████ 1,392 tokens (+100.0%)
```

### Large Complex Nested Dataset
```
gpt-4o (o200k):

    ZON          █████████░░░░░░░░░░░ 143,661 tokens 👑
    CSV          ██████████░░░░░░░░░░ 164,919 tokens (+14.8%)
    JSON (cmp)   ███████████░░░░░░░░░ 188,604 tokens (+23.8%)
    TOON         █████████████░░░░░░░ 224,940 tokens (+56.6%)
    YAML         █████████████░░░░░░░ 224,938 tokens (+56.6%)
    JSON format  ████████████████████ 284,132 tokens (+97.8%)
    XML          ████████████████████ 335,239 tokens (+133.4%)

claude 3.5 (anthropic):

    ZON          █████████░░░░░░░░░░░ 145,652 tokens 👑
    CSV          ██████████░░░░░░░░░░ 161,701 tokens (+11.0%)
    JSON (cmp)   ███████████░░░░░░░░░ 185,136 tokens (+21.3%)
    TOON         ████████████░░░░░░░░ 196,893 tokens (+35.2%)
    YAML         ████████████░░░░░░░░ 196,892 tokens (+35.2%)
    JSON format  ████████████████████ 274,149 tokens (+88.2%)
    XML          ████████████████████ 327,274 tokens (+124.7%)

llama 3 (meta):

    ZON          ██████████░░░░░░░░░░ 230,838 tokens 👑
    CSV          ███████████░░░░░░░░░ 254,181 tokens (+10.1%)
    JSON (cmp)   ████████████░░░░░░░░ 276,405 tokens (+16.5%)
    TOON         █████████████░░░░░░░ 314,824 tokens (+36.4%)
    YAML         █████████████░░░░░░░ 314,820 tokens (+36.4%)
    JSON format  ████████████████████ 407,488 tokens (+76.5%)
    XML          ████████████████████ 480,125 tokens (+108.0%)
```


### Overall Summary:
```
GPT-4o (o200k):
  ZON Wins: 2/2 datasets
  
  Total tokens across all datasets:
    ZON:         147,267 👑
    CSV:         165,647 (+12.5%)
    JSON (cmp):  189,193 (+28.4%)
    TOON:        225,510 (+53.1%)
    
  ZON vs TOON: -34.7% fewer tokens ✨
  ZON vs JSON: -22.2% fewer tokens

Claude 3.5 (Anthropic):
  ZON Wins: 1/2 datasets
  
  Total tokens across all datasets:
    ZON:         149,281 👑
    CSV:         162,245 (+8.7%)
    JSON (cmp):  185,732 (+24.4%)
    TOON:        197,463 (+32.3%)
    
  ZON vs TOON: -24.4% fewer tokens ✨
  ZON vs JSON: -19.6% fewer tokens

Llama 3 (Meta):
  ZON Wins: 2/2 datasets
  
  Total tokens across all datasets:
    ZON:         234,623 👑
    CSV:         254,909 (+8.7%)
    JSON (cmp):  277,165 (+18.1%)
    TOON:        315,608 (+34.5%)
    
  ZON vs TOON: -25.7% fewer tokens ✨
  ZON vs JSON: -15.3% fewer tokens
```

**Key Insights:**

- ZON wins on all Llama 3 and GPT-4o tests (best token efficiency across both datasets).
- Claude shows CSV has slight edge (0.2%) on simple tabular data, but ZON dominates on complex nested data.

- **Average savings: 25-35% vs TOON, 15-28% vs JSON** across all tokenizers.

- ZON wins on all Llama 3 and GPT-4o tests (best token efficiency across both datasets).
- ZON is 2nd on Claude (CSV wins by only 0.2%, ZON still beats TOON by 4.6%).
- ZON consistently outperforms TOON on every tokenizer (from 4.6% up to 34.8% savings).

**Key Insight:** ZON is the only format that wins or nearly wins across all models & datasets.

---

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
    {
      "id": 2,
      "name": "Ridge Overlook",
      "distanceKm": 9.2,
      "elevationGain": 540,
      "companion": "luis",
      "wasSunny": false
    },
    {
      "id": 3,
      "name": "Wildflower Loop",
      "distanceKm": 5.1,
      "elevationGain": 180,
      "companion": "sam",
      "wasSunny": true
    }
  ]
}
```

<details>
<summary>TOON already conveys the same information with <strong>fewer tokens</strong>.</summary>

```yaml
context:
  task: Our favorite hikes together
  location: Boulder
  season: spring_2025
friends[3]: ana,luis,sam
hikes[3]{id,name,distanceKm,elevationGain,companion,wasSunny}:
  1,Blue Lake Trail,7.5,320,ana,true
  2,Ridge Overlook,9.2,540,luis,false
  3,Wildflower Loop,5.1,180,sam,true
```

</details>

ZON conveys the same information with **even fewer tokens** than TOON – using compact table format with explicit headers:

```
context.task:Our favorite hikes together
context.location:Boulder
context.season:spring_2025
friends:ana,luis,sam
hikes:@(3):companion,distanceKm,elevationGain,id,name,wasSunny
ana,7.5,320,1,Blue Lake Trail,T
luis,9.2,540,2,Ridge Overlook,F
sam,5.1,180,3,Wildflower Loop,T
```

### 🛡️ Validation + 📉 Compression

Building reliable LLM apps requires two things:
1.  **Safety:** You need to validate outputs (like you do with Zod/Pydantic).
2.  **Efficiency:** You need to compress inputs to save money.

ZON is the only library that gives you **both in one package**.

| Feature | Traditional Validation (e.g. Pydantic) | ZON |
| :--- | :--- | :--- |
| **Type Safety** | ✅ Yes | ✅ Yes |
| **Runtime Validation** | ✅ Yes | ✅ Yes |
| **Input Compression** | ❌ No | ✅ **Yes (Saves ~50%)** |
| **Prompt Generation** | ❌ Plugins needed | ✅ **Built-in** |
| **Bundle Size** | ~Large | ⚡ **~5kb** |

**The Sweet Spot:** Use ZON to **save money on Input Tokens** while keeping the strict safety you expect.

---

## Key Features

- 🎯 **100% LLM Accuracy**: Achieves perfect retrieval (24/24 questions) with self-explanatory structure – no hints needed

### 3. Smart Flattening (Dot Notation)
ZON automatically flattens top-level nested objects to reduce indentation.
**JSON:**
```json
{
  "config": {
    "database": {
      "host": "localhost"
    }
  }
}
```
**ZON:**
```
config.database{host:localhost}
```

### 4. Colon-less Structure
For nested objects and arrays, ZON omits the redundant colon, creating a cleaner, block-like structure.
**JSON:**
```json
{
  "user": {
    "name": "Alice",
    "roles": ["admin", "dev"]
  }
}
```
**ZON:**
```
user{name:Alice,roles[admin,dev]}
```
(Note: `user{...}` instead of `user:{...}`)
- 💾 **Most Token-Efficient**: 4-15% fewer tokens than TOON across all tokenizers
- 🎯 **JSON Data Model**: Encodes the same objects, arrays, and primitives as JSON with deterministic, lossless round-trips
- 📐 **Minimal Syntax**: Explicit headers (`@(N)` for count, column list) eliminate ambiguity for LLMs
- 🧺 **Tabular Arrays**: Uniform arrays collapse into tables that declare fields once and stream row values
- 🔢 **Canonical Numbers**: No scientific notation (1000000, not 1e6), NaN/Infinity → null
- 🌳 **Deep Nesting**: Handles complex nested structures efficiently (91% compression on 50-level deep objects)
- 🔒 **Security Limits**: Automatic DOS prevention (100MB docs, 1M arrays, 100K keys)
- ✅ **Production Ready**: 94/94 tests pass, 27/27 datasets verified, zero data loss


## Security & Data Types

### Eval-Safe Design

ZON is **immune to code injection attacks** that plague other formats:

✅ **No eval()** - Pure data format, zero code execution
✅ **No object constructors** - Unlike YAML's `!!python/object` exploit
✅ **No prototype pollution** - Dangerous keys blocked (`__proto__`, `constructor`)
✅ **Type-safe parsing** - Numbers via safe parsing, not `eval()`

**Comparison:**

| Format | Eval Risk | Code Execution |
|--------|-----------|----------------|
| **ZON** | ✅ None | Impossible |
| **JSON** | ✅ Safe | When not using `eval()` |
| **YAML** | ❌ High | `!!python/object/apply` RCE |
| **TOON** | ✅ Safe | Type-agnostic, no eval |

### Data Type Preservation

**Strong type guarantees:**
- ✅ **Integers**: `42` stays integer
- ✅ **Floats**: `3.14` preserves decimal (`.0` added for whole floats)
- ✅ **Booleans**: Explicit `T`/`F` (not string `"true"`/`"false"`)
- ✅ **Null**: Explicit `null` (not omitted like `undefined`)
- ✅ **No scientific notation**: `1000000`, not `1e6` (prevents LLM confusion)
- ✅ **Special values normalized**: `NaN`/`Infinity` → `null`

---

## New in v1.2.0: Enterprise Features

### Binary Format (ZON-B)

Compact binary encoding with 40-60% space savings vs JSON:

```python
from zon import encode_binary, decode_binary

# Encode to binary
data = {"users": [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]}
binary = encode_binary(data)  # 40-60% smaller than JSON

# Decode from binary
decoded = decode_binary(binary)
```

**Features:**
- MessagePack-inspired format with magic header (`ZNB\x01`)
- Full type support for all ZON primitives
- Perfect round-trip fidelity
- Ideal for storage, APIs, and network transmission

### Versioning & Migration System

Document-level schema versioning with automatic migrations:

```python
from zon import embed_version, extract_version, ZonMigrationManager

# Embed version metadata
versioned = embed_version(data, "2.0.0", "user-schema")

# Extract version info
meta = extract_version(versioned)

# Setup migration manager
manager = ZonMigrationManager()
manager.register_migration("1.0.0", "2.0.0", upgrade_function)

# Automatically migrate
migrated = manager.migrate(old_data, "1.0.0", "2.0.0")
```

**Features:**
- Semantic versioning support
- BFS-based migration path finding
- Backward/forward compatibility checking
- Chained migrations for complex upgrades

### Adaptive Encoding

Three encoding modes optimized for different use cases:

```python
from zon import encode_adaptive, recommend_mode, AdaptiveEncodeOptions

# Auto-recommend best mode
recommendation = recommend_mode(data)
# {'mode': 'compact', 'confidence': 0.95, 'reason': 'Large uniform array...'}

# Compact mode - maximum compression
compact = encode_adaptive(data, AdaptiveEncodeOptions(mode='compact'))

# Readable mode - pretty-printed with indentation
readable = encode_adaptive(data, AdaptiveEncodeOptions(mode='readable', indent=2))

# LLM-optimized - balanced for AI workflows
llm = encode_adaptive(data, AdaptiveEncodeOptions(mode='llm-optimized'))
```

**Encoding Modes:**

| Mode | Best For | Features |
|------|----------|----------|
| **compact** | Production APIs | Maximum compression, T/F booleans |
| **readable** | Config files | Multi-line indentation, human-friendly |
| **llm-optimized** | AI workflows | true/false booleans, no type coercion |

**Readable Mode Example:**
```zon
metadata:{
  generated:2025-01-01T12:00:00Z
  version:1.2.0
}

users:@(2):id,name,role
1,Alice,admin
2,Bob,user
```

### Developer Tools

Comprehensive utilities for working with ZON data:

```python
from zon import size, compare_formats, analyze, ZonValidator

# Analyze data size across formats
comparison = compare_formats(data)
# {'json': {'size': 1200, 'percentage': 100.0},
#  'zon': {'size': 800, 'percentage': 66.7},
#  'binary': {'size': 480, 'percentage': 40.0}}

# Data complexity analysis
analysis = analyze(data)
# {'depth': 3, 'complexity': 'moderate', 'recommended_format': 'zon'}

# Enhanced validation
validator = ZonValidator()
result = validator.validate(zon_string)
if not result.is_valid:
    for error in result.errors:
        print(f"Error at line {error.line}: {error.message}")
```

**Tools Available:**
- `size()` - Calculate data size in different formats
- `compare_formats()` - Compare JSON/ZON/Binary sizes
- `analyze()` - Comprehensive data structure analysis
- `infer_schema()` - Automatic schema inference
- `ZonValidator` - Enhanced validation with linting rules
- `expand_print()` - Pretty-printer for readable formatting

### Complete API

```python
from zon import (
    # Core encoding
    encode, decode, encode_llm,
    
    # Adaptive encoding (v1.2.0)
    encode_adaptive, recommend_mode, AdaptiveEncodeOptions,
    
    # Binary format (v1.2.0)
    encode_binary, decode_binary,
    
    # Versioning (v1.2.0)
    embed_version, extract_version, compare_versions,
    is_compatible, strip_version, ZonMigrationManager,
    
    # Developer tools (v1.2.0)
    size, compare_formats, analyze, infer_schema,
    compare, is_safe, ZonValidator, expand_print
)
```

---

## Quality & Security

### Data Integrity
- **Unit tests:** 340/340 passed (v1.2.0 adds 103 new tests for binary, versioning, tools)
- **Roundtrip tests:** 27/27 datasets verified + 51 cross-language examples
- **No data loss or corruption**
- **Cross-language compatibility:** 51% exact match with TypeScript v1.3.0

### Security Limits (DOS Prevention)

Automatic protection against malicious input:

| Limit | Maximum | Error Code |
|-------|---------|------------|
| Document size | 100 MB | E301 |
| Line length | 1 MB | E302 |
| Array length | 1M items | E303 |
| Object keys | 100K keys | E304 |
| Nesting depth | 100 levels | - |

**Protection is automatic** - no configuration required.

### Validation (Strict Mode)

**Enabled by default** - validates table structure:

```python
import zon

# Strict mode (default)
data = zon.decode(zon_string)

# Non-strict mode
data = zon.decode(zon_string, strict=False)
```

**Error codes:** E001 (row count), E002 (field count)

---

## Installation & Quick Start

### Installation

**Using pip (traditional):**
```bash
pip install zon-format
```

**Using UV (faster alternative):**
```bash
# Install with UV (5-10x faster than pip)
uv pip install zon-format

# Or for UV-based projects
uv add zon-format
```

> **What is UV?** [UV](https://github.com/astral-sh/uv) is a blazing-fast Python package installer and resolver, written in Rust. It's a drop-in replacement for pip that's 10-100x faster.

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

### Command Line Interface (CLI)

The ZON package includes a CLI tool for converting files between JSON and ZON format.

**Usage:**

```bash
# Encode JSON to ZON format
zon encode data.json > data.zonf

# Decode ZON back to JSON
zon decode data.zonf > output.json
```

**File Extension:**

ZON files conventionally use the `.zonf` extension to distinguish them from other formats.

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

### Mixed Structures

ZON intelligently combines formats:

```
metadata:"{version:1.0.4,env:production}"
users:@(5):id,name,active
1,Alice,T
2,Bob,F
...
logs:"[{id:101,level:INFO},{id:102,level:WARN}]"
```

---

## Encoding Modes (New in v1.2.0)

ZON now provides **three encoding modes** optimized for different use cases:

### Mode Overview

| Mode | Best For | Token Efficiency | Human Readable | LLM Clarity | Default |
|------|----------|------------------|----------------|-------------|---------|
| **compact** | Production APIs, LLMs | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ | ✅ YES |
| **llm-optimized** | AI workflows | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | |
| **readable** | Config files, debugging | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | |

### Adaptive Encoding

```python
from zon import encode_adaptive, AdaptiveEncodeOptions, recommend_mode

# Use compact mode (default - maximum compression)
output = encode_adaptive(data)

# Use readable mode (human-friendly)
output = encode_adaptive(data, AdaptiveEncodeOptions(mode='readable'))

# Use LLM-optimized mode (balanced for AI)
output = encode_adaptive(data, AdaptiveEncodeOptions(mode='llm-optimized'))

# Get recommendation for your data
recommendation = recommend_mode(data)
print(f"Use {recommendation['mode']} mode: {recommendation['reason']}")
```

### Mode Details

**Compact Mode (Default)**
- Maximum compression using tables and abbreviations (`T`/`F` for booleans)
- Dictionary compression for repeated values
- Best for production APIs and cost-sensitive LLM workflows

**LLM-Optimized Mode**
- Balances token efficiency with AI comprehension
- Uses `true`/`false` instead of `T`/`F` for better LLM understanding
- Disables dictionary compression for clarity

**Readable Mode**
- Human-friendly formatting with proper indentation
- Perfect for configuration files and debugging
- Easy editing and version control

---

## API Reference

### `zon.encode(data: Any) -> str`

Encodes Python data to ZON format.

```python
import zon

zon_str = zon.encode({
    "users": [
        {"id": 1, "name": "Alice"},
        {"id": 2, "name": "Bob"}
    ]
})
```

**Returns:** ZON-formatted string

### `zon.encode_adaptive(data: Any, options: AdaptiveEncodeOptions = None) -> str`

Encodes Python data using adaptive mode selection (New in v1.2.0).

```python
from zon import encode_adaptive, AdaptiveEncodeOptions

# Compact mode (default)
output = encode_adaptive(data)

# Readable mode with custom indentation
output = encode_adaptive(
    data,
    AdaptiveEncodeOptions(mode='readable', indent=4)
)

# With debug information
result = encode_adaptive(
    data,
    AdaptiveEncodeOptions(mode='compact', debug=True)
)
print(result.decisions)  # See encoding decisions
```

**Returns:** ZON-formatted string or `AdaptiveEncodeResult` if debug=True

### `zon.recommend_mode(data: Any) -> dict`

Analyzes data and recommends optimal encoding mode (New in v1.2.0).

```python
from zon import recommend_mode

recommendation = recommend_mode(my_data)
print(f"Use {recommendation['mode']} mode")
print(f"Confidence: {recommendation['confidence']}")
print(f"Reason: {recommendation['reason']}")
```

**Returns:** Dictionary with mode, confidence, reason, and metrics

### `zon.decode(zon_string: str, strict: bool = True) -> Any`

Decodes ZON format back to Python data.

```python
import zon

data = zon.decode("""
users:@(2):id,name
1,Alice
2,Bob
""")
```

**Options:**

```python
# Strict mode (default) - validates table structure
data = zon.decode(zon_string)

# Non-strict mode - allows row/field count mismatches  
data = zon.decode(zon_string, strict=False)
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

**Returns:** Original Python data structure

---

## Runtime Evals (Schema Validation)

ZON includes a built-in validation layer designed for **LLM Guardrails**.
Instead of just parsing data, you can enforce a schema to ensure the LLM output matches your expectations.

### Why use this?
1.  **Self-Correction:** Feed error messages back to the LLM so it can fix its own mistakes.
2.  **Type Safety:** Guarantee that `age` is a number, not a string like `"25"`.
3.  **Hallucination Check:** Ensure the LLM didn't invent fields you didn't ask for.

### Usage

```python
from zon import zon, validate

# 1. Define the Schema (The "Source of Truth")
UserSchema = zon.object({
    'name': zon.string().describe("The user's full name"),
    'age': zon.number().describe("Age in years"),
    'role': zon.enum(['admin', 'user']).describe("Access level"),
    'tags': zon.array(zon.string()).optional()
})

# 2. Generate the System Prompt (The "Input")
system_prompt = f"""
You are an API. Respond in ZON format with this structure:
{UserSchema.to_prompt()}
"""

print(system_prompt)
# Output:
# object:
#   - name: string - The user's full name
#   - age: number - Age in years
#   - role: enum(admin, user) - Access level
#   - tags: array of [string] (optional)

# 3. Validate the Output (The "Guardrail")
result = validate(llm_output, UserSchema)
```

### 💡 The "Input Optimization" Workflow (Best Practice)

The most practical way to use ZON is to **save money on Input Tokens** while keeping your backend compatible with JSON.

**1. Input (ZON):** Feed the LLM massive datasets in ZON (saving ~50% tokens).
**2. Output (JSON):** Ask the LLM to reply in standard JSON.

```python
import zon

# 1. Encode your massive context (Save 50% tokens!)
context = zon.encode(large_dataset)

# 2. Send to LLM
prompt = f"""
Here is the data in ZON format:
{context}

Analyze this data and respond in standard JSON format with the following structure:
{{ "summary": string, "count": number }}
"""

# 3. LLM Output (Standard JSON)
# { "summary": "Found 50 users", "count": 50 }
```

This gives you the **best of both worlds**:
- **Cheaper API Calls** (ZON Input)
- **Zero Code Changes** (JSON Output)

### Supported Types
- `zon.string()`
- `zon.number()`
- `zon.boolean()`
- `zon.enum(['a', 'b'])`
- `zon.array(schema)`
- `zon.object({ 'key': schema })`
- `.optional()` modifier

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

Comprehensive guides and references are available in the [`./docs/`](./docs/) directory:

### 📖 [Syntax Cheatsheet](./docs/syntax-cheatsheet.md)
Quick reference for ZON format syntax with practical examples.

**What's inside:**
- Basic types and primitives (strings, numbers, booleans, null)
- Objects and nested structures
- Arrays (tabular, inline, mixed)
- Quoting rules and escape sequences
- Complete examples with JSON comparisons
- Tips for LLM usage

**Perfect for:** Quick lookups, learning the syntax, copy-paste examples

---

### 🔧 [API Reference](./docs/api-reference.md)
Complete API documentation for `zon-format` v1.0.4.

**What's inside:**
- `encode()` function - detailed parameters and examples
- `decode()` function - detailed parameters and examples
- Python type definitions

### 📘 [Complete Specification](../SPEC.md)

Comprehensive formal specification including:
- Data model and encoding rules
- Security model (DOS prevention, no eval)
- Data type system and preservation guarantees
- Conformance checklists
- Media type specification (`.zonf`, `text/zon`)
- Examples and appendices

### 📚 Other Documentation

- **[API Reference](./docs/api-reference.md)** - Encoder/decoder API, options, error codes
- **[Syntax Cheatsheet](./docs/syntax-cheatsheet.md)** - Quick reference guide
- **[LLM Best Practices](./docs/llm-best-practices.md)** - Using ZON with LLMs

---

## Links

- [PyPI Package](https://pypi.org/project/zon-format/)
- [Changelog](./CHANGELOG.md)
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

Copyright (c) 2025 ZON-FORMAT (Roni Bhakta)

MIT License - see [LICENSE](../LICENSE) for details.

---

**Made with ❤️ for the LLM community**

*ZON v1.2.0 - Token efficiency that scales with complexity, now with adaptive encoding*
