# ZON Syntax Cheatsheet

Quick reference for ZON format syntax.

---

## Primitives

| Type | ZON | JSON |
|------|-----|------|
| Boolean (true) | `T` | `true` |
| Boolean (false) | `F` | `false` |
| Null | `null` | `null` |
| Number | `42`, `3.14` | `42`, `3.14` |
| String | `hello`, `"with spaces"` | `"hello"` |

---

## Objects

```
# Simple object
user{name:Alice,age:30}

# Nested object
config{db{host:localhost,port:5432}}

# With arrays
data{tags[red,blue],count:5}
```

---

## Arrays

```
# Simple array
colors[red,blue,green]

# Number array
ids[1,2,3]

# Array of objects
users[{id:1,name:Alice},{id:2,name:Bob}]
```

---

## Tables

```
# Basic table
users:@(3):id,name,role
1,Alice,admin
2,Bob,user
3,Carol,guest

# With delta encoding
logs:@(100):id:delta,message
1,Started
+1,Processing
+1,Done

# With dictionary
status[3]:pending,active,done
tasks:@(10):id,status
1,0
2,1
3,0
```

---

## Mixed Structures

```
# Combine all formats
metadata{version:1.0,env:prod}
users:@(2):id,name
1,Alice
2,Bob
tags[important,urgent]
```

---

## Special Characters

| Character | Meaning |
|-----------|---------|
| `@(N)` | Table with N rows |
| `:delta` | Delta-encoded column |
| `[K]` | Array or dictionary with K items |
| `{}` | Object |
| `T` / `F` | Boolean true/false |
| `null` | Null value |

---

## Quoting Rules

Quote strings when they:
- Start with a number: `"123abc"`
- Contain commas: `"a,b,c"`
- Contain newlines: `"line1\nline2"`
- Look like booleans: `"true"`, `"false"`
- Are empty: `""`

---

## See Also

- [SPEC.md](../SPEC.md) - Full specification
- [Advanced Features](advanced-features.md)
- [API Reference](api-reference.md)
