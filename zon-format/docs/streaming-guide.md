# Streaming Guide

**Version:** 1.1.0

## Overview

ZON supports streaming for memory-efficient processing of large datasets.

---

## Stream Encoding

Process large datasets without loading everything into memory:

```python
from zon import ZonStreamEncoder
import sys

encoder = ZonStreamEncoder()

# Stream large dataset
for chunk in get_large_dataset():
    zon_chunk = encoder.write(chunk)
    sys.stdout.write(zon_chunk)
```

---

## Stream Decoding

Parse streaming ZON data:

```python
from zon import ZonStreamDecoder

decoder = ZonStreamDecoder()

with open('large_file.zonf') as f:
    for line in f:
        objects = decoder.feed(line)
        for obj in objects:
            process(obj)
```

---

## Use Cases

### 1. Large File Processing

```python
from zon import ZonStreamDecoder

decoder = ZonStreamDecoder()

with open('10GB_file.zonf') as f:
    for chunk in f:
        objects = decoder.feed(chunk)
        for obj in objects:
            database.insert(obj)
```

### 2. HTTP Streaming

```python
import requests
from zon import ZonStreamDecoder

decoder = ZonStreamDecoder()

response = requests.get('https://api.example.com/stream', stream=True)
for chunk in response.iter_content(chunk_size=8192):
    objects = decoder.feed(chunk.decode('utf-8'))
    for obj in objects:
        print(obj)
```

---

## API Reference

### ZonStreamEncoder

```python
class ZonStreamEncoder:
    def __init__(self):
        """Initialize stream encoder"""
        
    def write(self, data: dict) -> str:
        """Encode data chunk to ZON string"""
```

### ZonStreamDecoder

```python
class ZonStreamDecoder:
    def __init__(self):
        """Initialize stream decoder"""
        
    def feed(self, chunk: str) -> List[dict]:
        """Feed chunk and return parsed objects"""
```

---

## See Also

- [API Reference](api-reference.md)
- [Advanced Features](advanced-features.md)
