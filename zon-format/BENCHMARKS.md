# ZON Performance Benchmarks

**Date:** 2025-12-02  
**Version:** v1.1.0  
**Environment:** Python 3.14 (macOS)

## Overview

Comprehensive comparison of ZON against major serialization formats:
- **JSON** - JavaScript Object Notation (compact & formatted)
- **YAML** - YAML Ain't Markup Language

All benchmarks measure both byte sizes and token counts across three major LLM tokenizers.

### Formats Excluded from Comparison

**CSV (Comma-Separated Values):**
- ❌ **Data Loss:** CSV can only represent flat tabular data
- ❌ On `unified_dataset`: drops 75% of data (metadata, config, logs) - only captures 290 bytes vs 1,854 bytes full data
- ❌ On `complex_nested`: flattens nested structures, loses hierarchy and relationships
- **Use Case:** Best for simple spreadsheets and database exports, not structured API data

**XML (Extensible Markup Language):**
- ❌ **Structural Transformations:** XML encoding introduces structural changes
- ❌ **Verbose:** Significantly larger than other formats (2-3x size of JSON)
- ❌ **Limited Benefit:** No clear advantage for LLM applications

**TOON (Token-Oriented Object Notation):**
- ❌ **Not Yet Available:** Python package encoder is not implemented (`NotImplementedError`)
- 📝 Will be added once the official Python package is complete

**Our Principle:** Only compare formats that preserve 100% of the data with perfect roundtrip fidelity.

---

## Unified Dataset

A representative dataset with metadata, users, configuration, and logs.

### 📦 Byte Sizes & Data Completeness

All formats below preserve **100% of the data** with perfect roundtrip:

| Format | Size | Notes |
|--------|------|-------|
| **ZON** | 1,371 bytes | Smallest complete representation 👑 |
| **JSON (compact)** | 1,854 bytes | 26% larger than ZON |
| **YAML** | 1,885 bytes | 27% larger than ZON |
| **JSON (formatted)** | 2,842 bytes | 52% larger than ZON |

### Token Efficiency (Complete Data Only)

Comparing only formats that preserve **all data**:

**GPT-4o (o200k):**
```
ZON              ████████████████████ 511 tokens 👑
JSON (compact)   ███████████████████████ 589 tokens (+15.3%)
YAML             ████████████████████████████ 717 tokens (+40.3%)
JSON (formatted) █████████████████████████████████ 939 tokens (+83.8%)
```

**Claude 3.5 (Anthropic):**
```
ZON              ████████████████████ 506 tokens 👑
JSON (compact)   ███████████████████████ 584 tokens (+15.4%)
YAML             ████████████████████████████ 715 tokens (+41.3%)
JSON (formatted) █████████████████████████████████ 937 tokens (+85.2%)
```

**Llama 3 (Meta):**
```
ZON              ████████████████████ 506 tokens 👑  
JSON (compact)   ███████████████████████ 584 tokens (+15.4%)
YAML             ████████████████████████████ 715 tokens (+41.3%)
JSON (formatted) █████████████████████████████████ 937 tokens (+85.2%)
```

**Key Insight:** For complete data preservation, ZON saves **15% tokens vs JSON** and **41% vs YAML**.

---

## Complex Nested Dataset

Large dataset (1,000 records) with deep nesting and varied structures.

### 📦 Byte Sizes & Data Completeness

All formats below preserve **100% of the data** with perfect roundtrip:

| Format | Size | Notes |
|--------|------|-------|
| **ZON** | 122 KB | 69% smaller than JSON 👑 |
| **JSON (compact)** | 390 KB | Baseline |
| **YAML** | 490 KB | 26% larger than JSON |
| **JSON (formatted)** | 721 KB | 85% larger than JSON |

### Token Efficiency (Complete Data Only)

**GPT-4o (o200k):**
```
ZON              ████████████████████ 61,356 tokens 👑
JSON (compact)   ████████████████████████████████████████ 121,213 tokens (+97.6%)
YAML             ██████████████████████████████████████████████████ 145,489 tokens (+137.1%)
JSON (formatted) ████████████████████████████████████████████████████████████████████ 206,611 tokens (+236.7%)
```

**Claude 3.5 (Anthropic):**
```
ZON              ████████████████████ 60,732 tokens 👑
JSON (compact)   ████████████████████████████████████████ 119,627 tokens (+97.0%)
YAML             ██████████████████████████████████████████████████ 144,930 tokens (+138.6%)
JSON (formatted) ████████████████████████████████████████████████████████████████████ 206,024 tokens (+239.2%)
```

**Llama 3 (Meta):**
```
ZON              ████████████████████ 60,732 tokens 👑
JSON (compact)   ████████████████████████████████████████ 119,627 tokens (+97.0%)
YAML             ██████████████████████████████████████████████████ 144,930 tokens (+138.6%)
JSON (formatted) ████████████████████████████████████████████████████████████████████ 206,024 tokens (+239.2%)
```

**ZON dominates on complex data:** 50% fewer tokens than JSON, 58% fewer than YAML.

---

## Overall Summary

Aggregated stats across both datasets (complete data only):

### GPT-4o (o200k)
- **Total Tokens:** ZON: 61,867 | JSON (compact): 121,802 | YAML: 146,206
- **ZON vs JSON:** -49.2% fewer tokens ✨
- **ZON vs YAML:** -57.7% fewer tokens

### Claude 3.5 (Anthropic)
- **Total Tokens:** ZON: 61,238 | JSON (compact): 120,211 | YAML: 145,645
- **ZON vs JSON:** -49.1% fewer tokens ✨
- **ZON vs YAML:** -57.9% fewer tokens

### Llama 3 (Meta)
- **Total Tokens:** ZON: 61,238 | JSON (compact): 120,211 | YAML: 145,645
- **ZON vs JSON:** -49.1% fewer tokens ✨
- **ZON vs YAML:** -57.9% fewer tokens

---

## Key Findings


### ✅ When to Use ZON
1. **Complex nested structures** - 50% token savings vs JSON
2. **LLM applications** - Fewer tokens = lower API costs  
3. **Complete data preservation** - No information loss
4. **Null optimization** - Automatically removes redundant nulls

### ⚠️ When Not to Use ZON
1. **Speed-critical applications** - JSON is 10-20x faster
2. **Wide ecosystem support needed** - JSON/YAML have more libraries and tools
3. **Human editing required** - JSON/YAML are more familiar to developers

### 📊 Performance Highlights
- **49% fewer tokens** than JSON across all tokenizers
- **58% fewer tokens** than YAML
- **69% smaller files** for complex nested data
- **100% data fidelity** with perfect roundtrip
- **Consistent wins** across GPT-4o, Claude, and Llama tokenizers

---

## Run Benchmarks

```bash
# Comprehensive format comparison with data completeness checks
python3 benchmarks/run.py

# Performance (speed) benchmarks
python3 benchmarks/performance_benchmark.py

# Token analysis
python3 benchmarks/unified_benchmark.py
```

---

## Methodology

- **Byte Sizes:** UTF-8 encoded string length
- **Token Counts:** Measured using `tiktoken` library
  - GPT-4o: `o200k_base` encoding
  - Claude/Llama: `cl100k_base` encoding (approximation)
- **Data Completeness:** Verified via roundtrip testing
  - ✅ Complete: Perfect roundtrip
  - ⚠️ Partial: Data loss (e.g., CSV dropping objects)
  - Structural only: Encoding transformations
- **Performance:** Average of 100 iterations (10 for large datasets)
- **Environment:** Python 3.14, macOS ARM64

---

## See Also

- [README.md](README.md) - Full documentation
- [Advanced Features](docs/advanced-features.md) - Delta encoding, dictionaries
- [SPEC.md](SPEC.md) - Format specification
