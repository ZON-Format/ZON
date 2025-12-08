# Migration Guide: v1.1.0 → v1.2.0

This guide helps you upgrade from ZON v1.1.0 to v1.2.0 and take advantage of the new adaptive encoding features.

## What's New in v1.2.0

### Major Features

1. **Adaptive Encoding System** - Intelligent mode selection based on data structure
2. **Three Encoding Modes** - compact, readable, llm-optimized
3. **Data Complexity Analyzer** - Automatic structural analysis
4. **Enhanced CLI** - New commands: encode, decode, analyze
5. **Comprehensive Documentation** - New guides and examples

## Breaking Changes

**None!** v1.2.0 is 100% backward compatible with v1.1.0.

All existing code continues to work without modifications:

```python
# v1.1.0 code (still works)
from zon import encode, decode

output = encode(data)
decoded = decode(output)
```

## New Features You Should Use

### 1. Adaptive Encoding (Recommended)

Instead of using `encode()` directly, use `encode_adaptive()` for better results:

```python
# Old way (v1.1.0)
from zon import encode
output = encode(data)

# New way (v1.2.0) - Better!
from zon import encode_adaptive
output = encode_adaptive(data)  # Auto-selects best mode
```

### 2. Mode Selection

Choose the right mode for your use case:

```python
from zon import encode_adaptive, AdaptiveEncodeOptions

# For production APIs (maximum compression)
output = encode_adaptive(data, AdaptiveEncodeOptions(mode='compact'))

# For LLM workflows (balanced)
output = encode_adaptive(data, AdaptiveEncodeOptions(mode='llm-optimized'))

# For config files (human-friendly)
output = encode_adaptive(data, AdaptiveEncodeOptions(mode='readable'))
```

### 3. Get Recommendations

Let ZON analyze your data and recommend the best mode:

```python
from zon import recommend_mode

recommendation = recommend_mode(data)
print(f"Use {recommendation['mode']} mode")
print(f"Reason: {recommendation['reason']}")
```

### 4. Analyze Data Complexity

```python
from zon import DataComplexityAnalyzer

analyzer = DataComplexityAnalyzer()
result = analyzer.analyze(data)

print(f"Nesting: {result.nesting}")
print(f"Irregularity: {result.irregularity:.2%}")
print(f"Recommendation: {result.recommendation}")
```

## CLI Migration

### Old Commands (v1.1.0)

```bash
# Convert JSON to ZON
zon convert data.json -o output.zonf

# Validate ZON file
zon validate file.zonf

# Show stats
zon stats file.zonf
```

### New Commands (v1.2.0)

All old commands still work, plus new ones:

```bash
# Encode with mode selection (NEW)
zon encode data.json -m compact > output.zonf
zon encode data.json -m llm-optimized > output.zonf

# Decode back to JSON (NEW)
zon decode file.zonf --pretty > output.json

# Analyze data complexity (NEW)
zon analyze data.json --compare

# Old commands still work
zon convert data.json -o output.zonf
zon validate file.zonf
zon stats file.zonf
```

## Upgrade Checklist

### Step 1: Update Package

```bash
pip install --upgrade zon-format
# or
uv pip install --upgrade zon-format
```

### Step 2: Verify Installation

```bash
python -c "import zon; print(zon.__version__)"
# Should output: 1.2.0
```

### Step 3: Optional - Switch to Adaptive Encoding

Review your code and consider switching to `encode_adaptive()`:

```python
# Before
from zon import encode
result = encode(data)

# After (optional, recommended)
from zon import encode_adaptive
result = encode_adaptive(data)
```

### Step 4: Test Your Application

Run your test suite to ensure everything works:

```bash
pytest
```

All existing tests should pass without modifications.

## Use Case Examples

### 1. Production API

```python
# Before (v1.1.0)
from zon import encode

@app.route('/api/data')
def get_data():
    data = get_large_dataset()
    return encode(data), 200, {'Content-Type': 'text/zonf'}

# After (v1.2.0) - More explicit
from zon import encode_adaptive, AdaptiveEncodeOptions

@app.route('/api/data')
def get_data():
    data = get_large_dataset()
    output = encode_adaptive(
        data, 
        AdaptiveEncodeOptions(mode='compact')  # Maximum compression
    )
    return output, 200, {'Content-Type': 'text/zonf'}
```

### 2. LLM Workflows

```python
# Before (v1.1.0)
from zon import encode
import openai

context = encode(large_dataset)
response = openai.ChatCompletion.create(
    model="gpt-4",
    messages=[{"role": "user", "content": f"Analyze: {context}"}]
)

# After (v1.2.0) - Better for LLMs
from zon import encode_adaptive, AdaptiveEncodeOptions

context = encode_adaptive(
    large_dataset,
    AdaptiveEncodeOptions(mode='llm-optimized')  # Balanced for AI
)
response = openai.ChatCompletion.create(
    model="gpt-4",
    messages=[{"role": "user", "content": f"Analyze: {context}"}]
)
```

### 3. Configuration Files

```python
# Before (v1.1.0)
from zon import encode
import json

with open('config.json') as f:
    config = json.load(f)

with open('config.zonf', 'w') as f:
    f.write(encode(config))

# After (v1.2.0) - More readable
from zon import encode_adaptive, AdaptiveEncodeOptions

with open('config.zonf', 'w') as f:
    f.write(encode_adaptive(
        config,
        AdaptiveEncodeOptions(mode='readable')  # Human-friendly
    ))
```

## Performance Impact

v1.2.0 is as fast as v1.1.0:

- `encode()` - No performance change
- `encode_adaptive()` - Adds ~1-2ms for analysis (negligible for most use cases)
- `decode()` - No performance change

The analysis overhead is minimal and worth it for better encoding decisions.

## Troubleshooting

### Issue: Import errors

```python
# Error
from zon import encode_adaptive
ImportError: cannot import name 'encode_adaptive'
```

**Solution:** Make sure you have v1.2.0 installed:

```bash
pip install --upgrade zon-format
python -c "import zon; print(zon.__version__)"
```

### Issue: Tests fail after upgrade

**Solution:** This shouldn't happen as v1.2.0 is backward compatible. If you encounter issues:

1. Check if you're using internal APIs (not recommended)
2. Verify your test fixtures still match expected output
3. Report any issues on GitHub

## FAQ

### Q: Do I need to change my existing code?

**A:** No, v1.2.0 is fully backward compatible.

### Q: Should I use `encode()` or `encode_adaptive()`?

**A:** Use `encode_adaptive()` for new code. It provides better results with minimal overhead.

### Q: Will my existing ZON files work?

**A:** Yes, all ZON files from v1.1.0 decode correctly in v1.2.0.

### Q: Can I mix modes in the same application?

**A:** Yes! Use different modes for different data:

```python
# Compact for API responses
api_data = encode_adaptive(data, AdaptiveEncodeOptions(mode='compact'))

# Readable for config files
config_data = encode_adaptive(config, AdaptiveEncodeOptions(mode='readable'))
```

### Q: What if I don't want to use adaptive encoding?

**A:** Keep using `encode()` - it still works perfectly.

## Getting Help

- [Documentation](../README.md)
- [Adaptive Encoding Guide](./adaptive-encoding.md)
- [GitHub Issues](https://github.com/ZON-Format/ZON/issues)
- [API Reference](./api-reference.md)

## Summary

v1.2.0 is a **feature release** with:
- ✅ 100% backward compatibility
- ✅ New adaptive encoding features
- ✅ Enhanced CLI tools
- ✅ Better documentation
- ✅ No breaking changes

Upgrade with confidence!
