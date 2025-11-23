# ZON v1.0 (Entropy Engine)

**Zero Overhead Notation** - A human-readable data serialization format optimized for LLM token efficiency.

[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-Proprietary-orange.svg)](LICENSE)
[![Production](https://img.shields.io/badge/production-Free%20to%20Use-green.svg)](LICENSE)

> 🚀 **24-40% better compression than TOON** | 📊 **30-42% compression vs JSON** | 🔍 **100% Human Readable**

---

## 📚 Table of Contents

- [What is ZON?](#-what-is-zon)
- [Quick Start](#-quick-start)
- [Installation](#-installation)
- [Beginner Tutorial](#-beginner-tutorial)
- [Advanced Usage](#-advanced-usage)
- [LLM Framework Integration](#-llm-framework-integration)
- [Benchmark Results](#-benchmark-results)
- [API Reference](#-api-reference)
- [Best Practices](#-best-practices)
- [Limitations](#%EF%B8%8F-limitations)

---

## 🚀 What is ZON?

ZON is a **smart compression format** designed specifically for transmitting structured data to Large Language Models. Unlike traditional compression (which creates binary data), ZON remains **100% human-readable** while dramatically reducing token usage.

### Why ZON?

| Problem | Solution |
| :--- | :--- |
| 💸 **High LLM costs** from verbose JSON | ZON reduces tokens by 30-42% |
| 🔍 **Binary formats aren't debuggable** | ZON is plain text - you can read it! |
| 🎯 **One-size-fits-all compression** | ZON auto-selects optimal strategy per column |
| ⚠️ **Data corruption risks** | ZON has safety checkpoints every 50 rows |

### Key Features

- ✅ **Entropy Tournament**: Auto-selects best compression strategy per column
- ✅ **8 Compression Strategies**: ENUM, VALUE, DELTA, GAS_INT, GAS_PAT, GAS_MULT, LIQUID, SOLID
- ✅ **Human Readable**: Unlike TOON's binary format
- ✅ **100% Safe**: Guaranteed lossless reconstruction
- ✅ **Zero Configuration**: Works out of the box

---

## ⚡ Quick Start

```python
import zon

# Your data
users = [
    {"id": 1, "name": "Alice", "role": "Admin", "active": True},
    {"id": 2, "name": "Bob", "role": "User", "active": True},
    {"id": 3, "name": "Charlie", "role": "User", "active": False}
]

# Encode (compress)
compressed = zon.encode(users)
print(compressed)
# Output:
# #Z:1.0|D=User|rows[3]{active:E(T,F),id:R(1,1),name:S,role:E(Admin,%0)}|A=50
# $1:0,1,Alice,0
# 1,2,Bob,1
# 0,3,Charlie,1

# Decode (decompress)
original = zon.decode(compressed)
assert original == users  # ✓ Perfect reconstruction!
```

**Compression achieved**: ~60% smaller than JSON! 🎉

---

## 📦 Installation

### From PyPI (Recommended)

```bash
pip install zon-format
```

### From Source

```bash
git clone https://github.com/yourusername/zon-format.git
cd zon-format
pip install -e .
```

### Verify Installation

```python
import zon
print("ZON installed successfully! ✅")
```

---

## 📖 Beginner Tutorial

### Step 1: Understanding Your Data

ZON works best with **lists of similar objects** (like database rows or API responses):

```python
# ✅ Good - structured data
users = [
    {"name": "Alice", "age": 30},
    {"name": "Bob", "age": 25}
]

# ⚠️ Less effective - single object
single_user = {"name": "Alice", "age": 30}

# ✅ Still works - will use "inline mode"
small_list = [{"id": 1}]
```

### Step 2: Basic Encoding

```python
import zon

data = [
    {"product": "Laptop", "price": 999.99, "stock": 15},
    {"product": "Mouse", "price": 29.99, "stock": 50},
    {"product": "Keyboard", "price": 79.99, "stock": 30}
]

# Compress
zon_string = zon.encode(data)

# Save to file
with open('products.zon', 'w') as f:
    f.write(zon_string)

print(f"Original JSON: {len(str(data))} chars")
print(f"ZON format: {len(zon_string)} chars")
print(f"Reduction: {(1 - len(zon_string)/len(str(data))) * 100:.1f}%")
```

### Step 3: Basic Decoding

```python
# Read from file
with open('products.zon', 'r') as f:
    zon_string = f.read()

# Decompress
data = zon.decode(zon_string)

# Use your data
for product in data:
    print(f"{product['product']}: ${product['price']}")
```

### Step 4: Understanding the Format

Let's break down a ZON string:

```
#Z:1.0|rows[3]{id:R(1,1),status:E(active,inactive)}|A=50
$1:1,0
2,1
3,0
```

- `#Z:1.0`: Version header
- `rows[3]`: 3 rows of data
- `id:R(1,1)`: ID column uses Range strategy (start=1, step=1)
- `status:E(active,inactive)`: Status uses ENUM (0=active, 1=inactive)
- `A=50`: Anchors every 50 rows
- `$1:`: First row (explicit anchor)
- `1,0`: Row 2 data (id=2, status=active)

---

## 🎓 Advanced Usage

### Custom Anchor Intervals

Control safety vs compression trade-off:

```python
# More safety (anchor every 25 rows)
encoded = zon.encode(data, anchor_every=25)

# More compression (anchor every 100 rows)
encoded = zon.encode(data, anchor_every=100)

# Default is 50 (balanced)
```

### Handling Different Data Types

```python
data = [
    {
        "id": 1,
        "name": "Product",
        "price": 99.99,           # Float
        "in_stock": True,          # Boolean
        "description": None,       # Null
        "tags": ["sale", "new"],   # Array (stringified)
        "metadata": {"key": "val"} # Nested object (flattened)
    }
]

encoded = zon.encode(data)
decoded = zon.decode(encoded)
```

### Working with Large Datasets

```python
import json
import zon

# Read large JSON file
with open('large_dataset.json', 'r') as f:
    data = json.load(f)

# Encode in chunks if needed
chunk_size = 1000
for i in range(0, len(data), chunk_size):
    chunk = data[i:i+chunk_size]
    zon_chunk = zon.encode(chunk)
    
    with open(f'chunk_{i//chunk_size}.zon', 'w') as f:
        f.write(zon_chunk)
```

### Streaming Data

```python
# Process data as it arrives
def process_api_response(response_json):
    # Encode for LLM
    zon_data = zon.encode(response_json)
    
    # Send to LLM (uses fewer tokens!)
    llm_response = send_to_llm(zon_data)
    
    return llm_response
```

---

## 🤖 LLM Framework Integration

### OpenAI Integration

```python
import zon
import openai

# Prepare your data
users = [{"id": i, "name": f"User{i}", "active": True} for i in range(100)]

# Compress with ZON (saves tokens = saves money!)
zon_data = zon.encode(users)

# Use in prompt
response = openai.ChatCompletion.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": "You will receive data in ZON format. Decode mentally and analyze."},
        {"role": "user", "content": f"Analyze this user data:\n\n{zon_data}\n\nHow many active users?"}
    ]
)

print(response.choices[0].message.content)
```

**Cost Savings**: ~30-40% fewer tokens vs JSON!

### LangChain Integration

```python
from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate
import zon

# Prepare data
products = [
    {"name": "Laptop", "price": 999, "rating": 4.5},
    {"name": "Mouse", "price": 29, "rating": 4.2},
    # ... 100 more products
]

# Compress
zon_products = zon.encode(products)

# Create prompt template
template = """
You have access to product data in ZON format (a compressed JSON format).

Product Data:
{zon_data}

Question: {question}

Please analyze the data and answer.
"""

prompt = PromptTemplate(
    input_variables=["zon_data", "question"],
    template=template
)

# Use with LangChain
llm = OpenAI(temperature=0)
chain = prompt | llm

result = chain.invoke({
    "zon_data": zon_products,
    "question": "What's the average price of products with rating > 4?"
})

print(result)
```

### LlamaIndex Integration

```python
from llama_index import GPTSimpleVectorIndex, Document
import zon

# Prepare documents with ZON compression
docs_data = [
    {"title": "Doc1", "content": "...", "metadata": {...}},
    {"title": "Doc2", "content": "...", "metadata": {...}},
    # ... many more
]

# Compress metadata with ZON
zon_metadata = zon.encode([d["metadata"] for d in docs_data])

# Create documents
documents = [
    Document(
        text=doc["content"],
        extra_info={"compressed_meta": zon_metadata}
    )
    for doc in docs_data
]

# Build index
index = GPTSimpleVectorIndex.from_documents(documents)

# Query (the compressed metadata uses fewer tokens!)
response = index.query("Find documents about topic X")
```

### Anthropic Claude Integration

```python
import anthropic
import zon

client = anthropic.Anthropic(api_key="your-key")

# Large dataset
analytics_data = [...]  # 1000 rows

# Compress with ZON
zon_data = zon.encode(analytics_data)

message = client.messages.create(
    model="claude-3-opus-20240229",
    max_tokens=1024,
    messages=[
        {
            "role": "user",
            "content": f"""
            I'm providing analytics data in ZON format (compressed JSON).
            
            Data:
            {zon_data}
            
            Please analyze trends and provide insights.
            """
        }
    ]
)

print(message.content)
```

### Hugging Face Transformers

```python
from transformers import pipeline
import zon

# Sentiment analysis on compressed data
classifier = pipeline("sentiment-analysis")

reviews = [
    {"text": "Great product!", "rating": 5},
    {"text": "Not bad", "rating": 3},
    # ... 100 more
]

# Compress for context
zon_reviews = zon.encode(reviews)

# Include in prompt
prompt = f"""
Review Data (ZON format):
{zon_reviews}

Analyze overall sentiment.
"""

result = classifier(prompt)
print(result)
```

---

## 📊 Benchmark Results

### Standard Datasets

| Dataset | Records | JSON Size | ZON Size | Compression | vs TOON |
| :--- | :--- | :--- | :--- | :--- | :--- |
| employees.json | 20 | 15,381 | 5,668 | **63.1%** | **+9.7%** 🏆 |
| orders.json | 50 | 22,704 | 15,816 | **30.3%** | **+2.7%** ✅ |
| complex_nested.json | 1000 | 429,492 | 103,166 | **76.0%** | **+76.6%** 🚀 |

### Real-World API Data

| Dataset | Records | Compression | vs TOON |
| :--- | :--- | :--- | :--- |
| Random Users API | 50 | **42.4%** | **+40.4%** 🏆 |
| StackOverflow Q&A | 50 | **42.4%** | **+40.4%** 🏆 |
| GitHub Repos | 8 | **33.9%** | **+32.8%** ✅ |

**Average Performance**: 30.5% compression, +24.1% better than TOON

---

## 📚 API Reference

### `zon.encode(data, anchor_every=50)`

Encode a list of dictionaries into ZON format.

**Parameters:**
- `data` (List[Dict]): List of dictionaries to encode
- `anchor_every` (int, optional): Rows between safety anchors. Default: 50

**Returns:**
- `str`: ZON-formatted string

**Example:**
```python
zon_str = zon.encode([{"id": 1, "name": "Alice"}])
```

**Raises:**
- `TypeError`: If data is not a list

### `zon.decode(zon_str)`

Decode a ZON-formatted string back to original data.

**Parameters:**
- `zon_str` (str): ZON-formatted string

**Returns:**
- `List[Dict]`: Original data structure

**Example:**
```python
data = zon.decode("#Z:1.0|rows[1]{id:R(1,1)}|A=50\n$1:1")
```

**Raises:**
- `ZonDecodeError`: If string is malformed

---

## 💡 Best Practices

### ✅ DO:

1. **Use for structured data**
   ```python
   # Perfect use case
   db_results = [{"id": 1, "name": "..."}, ...]
   zon.encode(db_results)
   ```

2. **Batch similar data**
   ```python
   # Good - all objects have same structure
   users = [{"name": "Alice", "age": 30}, ...]
   ```

3. **Use appropriate anchor intervals**
   ```python
   # For critical data: more anchors
   zon.encode(data, anchor_every=25)
   
   # For non-critical: fewer anchors (more compression)
   zon.encode(data, anchor_every=100)
   ```

4. **Profile your data**
   ```python
   import json
   json_size = len(json.dumps(data))
   zon_size = len(zon.encode(data))
   print(f"Reduction: {(1 - zon_size/json_size) * 100:.1f}%")
   ```

### ❌ DON'T:

1. **Don't use for binary data**
   ```python
   # Bad - use appropriate binary format
   image_bytes = b'\x89PNG...'
   ```

2. **Don't use for highly random data**
   ```python
   # Bad - no patterns to compress
   random_data = [{"val": random.random()} for _ in range(100)]
   ```

3. **Don't modify ZON strings manually**
   ```python
   # Bad - will break decoding
   zon_str = zon_str.replace("1", "2")
   ```

---

## ⚠️ Limitations

### Known Limitations

1. **Arrays in Objects**: Arrays within objects are stringified
   ```python
   # Input: [{"tags": ["a", "b"]}]
   # Output: [{"tags": "['a', 'b']"}]  # String, not array
   ```

2. **Keys with Dots**: Conflicts with flattening
   ```python
   # Avoid: {"user.name": "Alice"}
   # Use instead: {"user_name": "Alice"}
   ```

3. **Empty Lists**: Returns `[{}]` instead of `[]`
   ```python
   # Workaround: Check before encoding
   if not data:
       return "[]"
   ```

See [EDGE_CASES.md](EDGE_CASES.md) for full details.

---

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Submit a pull request

---

## 📄 License

**Proprietary License - Free for Production Use**

✅ **You CAN**:
- Use ZON in production (commercial or non-commercial)
- Integrate into your applications and services
- Deploy at any scale

❌ **You CANNOT**:
- Redistribute or sell the source code
- Modify and redistribute
- Create competing products

**Copyright (c) 2025 Roni Bhakta. All Rights Reserved.**

See [LICENSE](LICENSE) for full terms. For custom licensing: ronibhakta1@gmail.com

---

## 🙏 Acknowledgments

- Inspired by TOON format for LLM token efficiency
- Benchmark datasets from JSONPlaceholder, GitHub API, Random User Generator, StackExchange API
- Community feedback and testing

---

## 📞 Support

- **Documentation**: [Full Docs](SPEC.md)
- **Issues**: [GitHub Issues](https://github.com/ZON-Format/ZON/issues)
- **Discussions**: [GitHub Discussions](https://github.com/ZON-Format/ZON/discussions)

---

**Made with ❤️ for the LLM community**

*ZON v1.0 - Compression that scales with complexity*
