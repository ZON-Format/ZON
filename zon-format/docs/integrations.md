# Integrations Guide

**Version:** 1.1.0  
**Status:** Stable

## Overview

ZON provides first-class integrations with popular AI frameworks, making it easy to use token-efficient serialization in your existing workflows.

## Table of Contents

- [OpenAI](#openai)
- [LangChain](#langchain)
- [AI SDK](#ai-sdk)

---

## OpenAI

### Installation

```bash
# Using pip
pip install zon-format openai

# Using UV (faster)
uv pip install zon-format openai
```

### ZOpenAI Wrapper

Automatically handle ZON format in OpenAI API calls:

```python
from zon.integrations.openai import ZOpenAI
import os

client = ZOpenAI(api_key=os.environ['OPENAI_API_KEY'])

data = client.chat(
    model='gpt-4',
    messages=[
        {
            'role': 'user',
            'content': 'List the top 5 programming languages with their primary use case'
        }
    ]
)

print(data)
# {
#   'languages': [
#     {'name': 'Python', 'useCase': 'Data Science'},
#     {'name': 'JavaScript', 'useCase': 'Web Development'},
#     ...
#   ]
# }
```

### How It Works

The wrapper:
1. Automatically injects ZON format instructions into the system prompt
2. Sends the request to OpenAI
3. Parses the ZON response
4. Returns clean Python dictionaries

### Custom System Prompt

Add your own instructions alongside ZON format:

```python
data = client.chat(
    model='gpt-4',
    messages=[
        {
            'role': 'system',
            'content': 'You are a helpful assistant. Be concise.'
        },
        {
            'role': 'user',
            'content': 'Summarize the React framework'
        }
    ]
)
```

The wrapper appends ZON instructions to your system prompt.

---

## LangChain

### Installation

```bash
# Using pip
pip install zon-format langchain

# Using UV (faster)
uv pip install zon-format langchain
```

### ZonOutputParser

Parse ZON responses from LLM chains:

```python
from zon.integrations.langchain import ZonOutputParser
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

parser = ZonOutputParser()

prompt = ChatPromptTemplate.from_messages([
    ('system', parser.get_format_instructions()),
    ('user', 'List 3 programming languages with their year of creation')
])

model = ChatOpenAI(temperature=0)
chain = prompt | model | parser

result = chain.invoke({})
print(result)
# {
#   'languages': [
#     {'name': 'Python', 'year': 1991},
#     {'name': 'JavaScript', 'year': 1995},
#     {'name': 'Rust', 'year': 2010}
#   ]
# }
```

### Format Instructions

The parser automatically provides format instructions:

```python
instructions = parser.get_format_instructions()
print(instructions)
# Your response must be formatted as ZON (Zero Overhead Notation).
# ZON is a compact format for structured data.
# Rules:
# 1. Use 'key:value' for properties.
# 2. Use 'key{...}' for nested objects.
# ...
```

### Error Handling

```python
try:
    result = chain.invoke({})
except Exception as error:
    if 'Failed to parse ZON' in str(error):
        print('LLM returned invalid ZON:', error)
```

---

## AI SDK

### Installation

```bash
pip install zon-format
```

### zon_schema()

Generate prompts for AI SDK integration:

```python
from zon.integrations.ai_sdk import zon_schema

# Define schema
schema = {
    'users': {
        'type': 'array',
        'items': {
            'id': 'number',
            'name': 'string',
            'role': 'enum',
            'values': ['admin', 'user']
        }
    }
}

# Generate prompt
prompt = zon_schema(schema)
print(prompt)
# Respond in ZON format:
# users:@(N):id,name,role
```

---

## Best Practices

### 1. Always Provide Examples

LLMs learn better with examples:

```python
prompt = """
Respond in ZON format. Example:

users:@(2):id,name,role
1,Alice,Admin
2,Bob,User

Now list 3 products:
"""
```

### 2. Handle Parsing Errors Gracefully

```python
try:
    result = client.chat(...)
except Exception as error:
    if 'Failed to parse ZON' in str(error):
        # Retry with more explicit instructions
        # or fallback to JSON
        pass
```

### 3. Use Streaming for Large Datasets

```python
from zon import ZonStreamDecoder

decoder = ZonStreamDecoder()

for chunk in stream_response():
    objects = decoder.feed(chunk)
    for obj in objects:
        process(obj)
```

---

## See Also

- [API Reference](api-reference.md) - Full API documentation
- [LLM Best Practices](llm-best-practices.md) - Tips for LLM integration
- [Streaming Guide](streaming-guide.md) - Streaming details
