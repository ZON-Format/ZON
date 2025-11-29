# Using ZON with LLMs - Best Practices

Copyright (c) 2025 ZON-FORMAT (Roni Bhakta)

Guide for maximizing ZON's effectiveness in LLM applications.

## Why ZON for LLMs?

LLM API costs are directly tied to token count. ZON reduces tokens by **29% vs JSON** while achieving **100% retrieval accuracy**.

**Key Benefits:**
- 💰 **Lower costs**: Fewer tokens = lower API bills
- 🎯 **Better accuracy**: 100% vs JSON's 91.7%
- 📊 **Self-documenting**: Explicit headers `@(N):columns`
- 🔍 **Human-readable**: Easy to debug and verify

---

## Sending ZON as Input

### Basic Pattern

Wrap ZON data in code blocks with format label:

````markdown
Here's the user data in ZON format:

```zon
users:@(3):active,id,name,role
T,1,Alice,admin
T,2,Bob,user
F,3,Carol,guest
```

Question: How many active users are there?
````

**Why this works:**
- ✅ Code blocks prevent formatting issues
- ✅ `zon` label helps model recognize format
- ✅ Explicit headers  (`@(3):columns`) give clear schema

### Alternative: No Code Block

For simple queries, code blocks aren't required:

```
Data:
users:@(3):id,name,active
1,Alice,T
2,Bob,F
3,Carol,T

Question: List all active users.
```

---

## Prompting Strategies

### Strategy 1: Show the Format (No Explanation)

**Best approach** - Let the model infer the structure:

````
```zon
products:@(4):category,id,name,price,stock
Electronics,1,Laptop,999,45
Books,2,Python Guide,29.99,120
Electronics,3,Mouse,19.99,200
Books,4,JavaScript Basics,24.95,85
```

Find products with stock below 100.
````

**Why it works:** The explicit headers (`@(4):category,id,name,price,stock`) are self-documenting.

### Strategy 2: Minimal Context

For complex queries, add brief context:

````
Data format: ZON (tabular)  
@(N) = row count  
Column names listed in header

```zon
logs:@(100):level,message,timestamp,userId
ERROR,Database timeout,2025-01-15T10:30:00Z,1001
WARN,High memory usage,2025-01-15T10:31:15Z,1002
ERROR,API rate limit,2025-01-15T10:32:45Z,1001
...
```

How many ERROR logs are from userId 1001?
````

### Strategy 3: Comparison (When Teaching Format)

If the model hasn't seen ZON before:

````
Traditional JSON:
```json
{"users": [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]}
```

Same data in compact ZON format:
```zon
users:@(2):id,name
1,Alice
2,Bob
```

Now answer based on this ZON data:
```zon
sales:@(5):amount,date,product,region
1250,2025-01-10,Laptop,West
890,2025-01-11,Mouse,East
...
```
````

---

## Common Use Cases

### 1. Data Retrieval Questions

**Perfect for ZON** - table format excels here:

````
```zon
employees:@(20):active,department,id,name,salary
T,Engineering,1,Alice Chen,95000
T,Sales,2,Bob Smith,75000
F,Marketing,3,Carol Lee,68000
...
```

Questions:
1. What's the average salary in Engineering?
2. How many inactive employees are there?
3. List all Sales department employees.
````

### 2. Aggregation Tasks

````
```zon
transactions:@(1000):amount,category,date,userId
45.99,groceries,2025-01-10,1001
120.00,electronics,2025-01-10,1002
23.50,groceries,2025-01-11,1001
...
```

Calculate total spending by category for userId 1001.
````

### 3. Filtering and Search

````
```zon
products:@(500):category,inStock,name,price,rating
Electronics,T,Laptop Pro,1299,4.5
Books,F,Python Guide,29.99,4.8
Electronics,T,USB Mouse,19.99,4.2
...
```

Find all in-stock Electronics with rating above 4.0.
````

### 4. Structure Awareness

````
```zon
metadata:"{version:1.0.3,env:production,deployed:2025-01-15}"
users:@(5):id,name,active
1,Alice,T
2,Bob,F
3,Carol,T
4,Dan,T
5,Eve,F
config:"{database:{host:localhost,port:5432},cache:{ttl:3600}}"
```

Questions:
- What are the top-level keys?
- How many users are in the dataset?
- What's the database port?
````

---

## Validation and Error Handling

### Ask Model to Validate

````
```zon
users:@(3):id,name,active
1,Alice,T
2,Bob,F
```

Before answering: verify the data has exactly 3 rows as declared.
Then answer: How many users are active?
````

### Handle Missing Data

````
```zon
products:@(4):id,name,price,stock
1,Laptop,999,45
2,Mouse,19.99,null
3,Keyboard,79.99,0
4,Monitor,299,15
```

Note: `null` means missing value.
Question: Which products have unknown stock levels?
````

---

## Optimizing Token Usage

### Tip 1: Use Compact Field Names

```zon
# Good ✅ (shorter column names)
u:@(100):id,n,e,a
1,Alice,alice@ex.com,T
2,Bob,bob@ex.com,F

# Acceptable ❌ (verbose names)
users:@(100):userId,fullName,emailAddress,isActive
1,Alice,alice@ex.com,true
2,Bob,bob@ex.com,false
```

**Token savings:** ~20% with compact names

### Tip 2: Boolean Shorthand

ZON uses `T`/`F` instead of `true`/`false`:

```zon
users:@(100):id,name,active,verified
1,Alice,T,T
2,Bob,F,T
3,Carol,T,F
```

**Token savings:** ~40% on boolean fields

### Tip 3: Null Handling

ZON uses explicit `null`:

```zon
data:@(50):id,value,note
1,100,null
2,null,Missing value
3,200,null
```

**Token savings:** Consistent with JSON, but unambiguous type.

---

## Advanced Patterns

### Multi-Table Structures

````
```zon
users:@(3):id,name,role
1,Alice,admin
2,Bob,user
3,Carol,user

posts:@(5):authorId,content,id,likes
1,Hello world,101,42
2,My first post,102,15
1,ZON is great,103,89
3,Learning LLMs,104,23
2,Second post,105,31
```

Question: How many posts did each admin user create?
````

### Nested Config + Tables

````
```zon
config:"{version:1.0,env:prod,features:{darkMode:T,beta:F}}"
users:@(1000):id,name,lastLogin
...
stats:"{totalUsers:1000,activeToday:245,avgSessionTime:420}"
```

What percentage of users were active today?
````

---

## Testing LLM Comprehension

### Benchmark Your Model

Test with simple queries first:

````
```zon
test:@(3):id,value
1,100
2,200
3,300
```

1. How many rows? (Answer: 3)
2. What's the sum of values? (Answer: 600)
3. What's the average? (Answer: 200)
````

If model gets these right → ready for complex queries!

### Common Failure Modes

1. **Counting mismatch**: Model counts incorrectly
   - **Fix**: Add explicit count in question: "The data has @(N) rows..."

2. **Type confusion**: Model treats `T` as string not boolean
   - **Fix**: Remind: "`T`=true, `F`=false"

3. **Missing columns**: Model assumes column exists
   - **Fix**: Headers are explicit - validate first

---

## Model-Specific Tips

### GPT-4/GPT-5
- ✅ Works perfectly out of box
- ✅ No hints needed
- ✅ 100% accuracy on ZON

### Claude
- ✅ Also works great
- ✅ Slightly more verbose responses
- ✅ 100% accuracy

### Llama Models
- ✅ Works well
- ⚠️ May need reminder: "@(N) means N rows"
- ✅ 90%+ accuracy

---

## Python Integration Example

```python
import zon
import openai

# Prepare data
users = [
    {"id": 1, "name": "Alice", "active": True},
    {"id": 2, "name": "Bob", "active": False},
    {"id": 3, "name": "Carol", "active": True}
]

# Encode to ZON (saves tokens!)
zon_data = zon.encode({"users": users})

# Use with OpenAI
response = openai.ChatCompletion.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": "You will receive data in ZON format."},
        {"role": "user", "content": f"Data:\n{zon_data}\n\nHow many active users?"}
    ]
)

print(response.choices[0].message.content)
# Answer: 2 active users (Alice and Carol)
```

---

## Complete Example: E-Commerce Query

````
Here's today's sales data in ZON format:

```zon
orders:@(245):amount,category,customerId,orderId,status
129.99,electronics,C1001,ORD5001,shipped
45.50,books,C1002,ORD5002,pending
89.99,electronics,C1001,ORD5003,shipped
23.99,books,C1003,ORD5004,delivered
199.99,electronics,C1004,ORD5005,shipped
...
```

Questions:
1. How many orders are from customer C1001?
2. What's the total revenue from electronics?
3. How many orders are still pending?
4. What's the average order value?

Please analyze the data and provide numerical answers.
````

**Why this works:**
- Clear format with `@(245)` count
- Explicit column headers
- Self-documenting structure
- No ambiguity

---

## Comparison: ZON vs TOON vs JSON

| Aspect | JSON | TOON | ZON |
|--------|------|------|-----|
| **Token count** | 28,042 | 20,988 | 19,995 👑 |
| **LLM accuracy** | 91.7% | 100% | 100% ✅ |
| **Hints needed** | Sometimes | No | No ✅ |
| **Self-documenting** | No | Yes | Yes ✅ |
| **Boolean format** | `true`/`false` | `true`/`false` | `T`/`F` 👑 |

**Verdict:** ZON offers best balance of compactness and accuracy.

---

## Quick Reference

### Do's ✅
- Use code blocks for formatting
- Include `@(N)` row counts
- List column names explicitly
- Use `T`/`F` for booleans
- Use `null` for null values

### Don'ts ❌
- Don't explain ZON syntax (show, don't tell)
- Don't mix formats (stick to ZON)
- Don't omit row counts
- Don't use verbose field names unnecessarily

---

**See also:**
- [Syntax Cheatsheet](./syntax-cheatsheet.md) - Quick reference
- [API Reference](./api-reference.md) - encode/decode functions
- [Format Specification](./SPEC.md) - Formal grammar
