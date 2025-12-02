import os
import json
import sys
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

import zon

EXAMPLES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../examples'))

if not os.path.exists(EXAMPLES_DIR):
    os.makedirs(EXAMPLES_DIR)

simple_key_value = {
    "name": "ZON Format",
    "version": "1.1.0",
    "active": True,
    "score": 98.5,
    "description": None
}

array_of_primitives = [
    "apple", "banana", "cherry", "date", "elderberry"
]

simple_table = [
    {"id": 1, "name": "Alice", "role": "Admin"},
    {"id": 2, "name": "Bob", "role": "User"},
    {"id": 3, "name": "Charlie", "role": "Guest"}
]

employees = [
    {"id": 101, "name": "John Doe", "department": "Engineering", "salary": 85000, "active": True},
    {"id": 102, "name": "Jane Smith", "department": "Marketing", "salary": 72000, "active": True},
    {"id": 103, "name": "Sam Brown", "department": "Engineering", "salary": 90000, "active": False},
    {"id": 104, "name": "Emily Davis", "department": "HR", "salary": 65000, "active": True}
]

mixed_structure = {
    "metadata": {
        "generated": "2025-01-01T12:00:00Z",
        "source": "System A"
    },
    "items": [
        {"id": 1, "value": 100},
        {"id": 2, "value": 200}
    ]
}

nested_objects = {
    "orderId": "ORD-123",
    "customer": {
        "name": "Alice",
        "address": {
            "street": "123 Main St",
            "city": "Wonderland"
        }
    },
    "items": [
        {"productId": "P1", "qty": 2, "price": 10.5},
        {"productId": "P2", "qty": 1, "price": 20.0}
    ]
}

deep_config = {
    "app": {
        "server": {
            "host": "localhost",
            "port": 8080,
            "options": {
                "timeout": 5000,
                "retry": 3
            }
        },
        "database": {
            "primary": {"connection": "db://primary"},
            "replica": {"connection": "db://replica"}
        }
    }
}

heavily_nested = {
    "level1": {
        "level2": {
            "level3": {
                "level4": {
                    "data": [1, 2, 3],
                    "info": "Deep"
                }
            }
        }
    }
}

dirty_data = {
    "primitives": {
        "integers": [0, 1, -1, 42, -42, 9007199254740991, -9007199254740991],
        "floats": [0.0, 1.1, -1.1, 3.14159, -2.71828, 1.5e10, 1.5e-10],
        "booleans": [True, False],
        "nulls": [None],
        "strings": [
            "", " ", "simple", "with spaces", "with, comma", "with: colon",
            "with \"quotes\"", "with 'single quotes'", "with \\n newline",
            "https://example.com/path?query=1&param=2",
            "special: !@#$%^&*()_+{}[]|\\\\:;\"'<>,.?/~`"
        ]
    },
    "edge_cases": {
        "empty_obj": {},
        "empty_arr": [],
        "nested_empty": {"a": {}, "b": []},
        "mixed_arr": [1, "two", True, None, {"a": 1}, [2]]
    }
}

complex_nested = {
    "level1": {
        "id": "L1",
        "meta": {"created": "2025-01-01", "active": True},
        "children": [
            {
                "id": "L2-A",
                "type": "group",
                "items": [
                    {"id": "L3-A1", "val": 10, "tags": ["a", "b"]},
                    {"id": "L3-A2", "val": 20, "tags": ["c"]}
                ],
                "config": {
                    "settings": {
                        "deep": {
                            "deeper": {
                                "deepest": "value"
                            }
                        }
                    }
                }
            },
            {
                "id": "L2-B",
                "type": "leaf",
                "data": [
                    {"x": 1, "y": 2},
                    {"x": 3, "y": 4, "z": 5},
                    {"x": 6}
                ]
            }
        ]
    }
}

nasty_strings = {
    "unicode": [
        "Emoji: 🚀🔥🎉💀👽",
        "Chinese: 你好世界",
        "Arabic: مرحبا بالعالم",
        "Russian: Привет мир",
        "Zalgo: H̴e̴l̴l̴o̴ ̴W̴o̴r̴l̴d̴"
    ],
    "control_chars": [
        "Null: \\u0000",
        "Backspace: \\b",
        "Form Feed: \\f",
        "Newline: \\n",
        "Carriage Return: \\r",
        "Tab: \\t",
        "Vertical Tab: \\v"
    ],
    "json_injection": [
        "{\\\"key\\\": \\\"value\\\"}",
        "[1, 2, 3]",
        "null",
        "true",
        "false",
        "// comment",
        "/* comment */"
    ],
    "script_injection": [
        "<script>alert('xss')</script>",
        "javascript:void(0)",
        "'; DROP TABLE users; --"
    ],
    "path_traversal": [
        "../../etc/passwd",
        "..\\\\..\\\\windows\\\\system32\\\\config\\\\sam"
    ]
}

def create_deep_recursion():
    """Create a deeply nested recursive object.
    
    Returns:
        Deeply nested dictionary.
    """
    obj = {"end": "bottom"}
    for i in range(50):
        obj = {"level": i, "next": obj}
    return obj

deep_recursion = create_deep_recursion()
hiking_example = {
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
            "wasSunny": True
        },
        {
            "id": 2,
            "name": "Ridge Overlook",
            "distanceKm": 9.2,
            "elevationGain": 540,
            "companion": "luis",
            "wasSunny": False
        },
        {
            "id": 3,
            "name": "Wildflower Loop",
            "distanceKm": 5.1,
            "elevationGain": 180,
            "companion": "sam",
            "wasSunny": True
        }
    ]
}

examples = [
    {'name': '01_simple_key_value', 'data': simple_key_value, 'desc': 'Simple Key-Value Object'},
    {'name': '02_array_of_primitives', 'data': array_of_primitives, 'desc': 'Array of Strings'},
    {'name': '03_simple_table', 'data': simple_table, 'desc': 'Simple Array of Objects (Table)'},
    {'name': '04_uniform_table', 'data': employees, 'desc': 'Uniform Tabular Data (Employees)'},
    {'name': '05_mixed_structure', 'data': mixed_structure, 'desc': 'Mixed Structure (Metadata + Table)'},
    {'name': '06_nested_objects', 'data': nested_objects, 'desc': 'Nested Objects & Arrays'},
    {'name': '07_deep_config', 'data': deep_config, 'desc': 'Deeply Nested Configuration'},
    {'name': '08_complex_nested', 'data': heavily_nested, 'desc': 'Heavily Nested Complex Data'},
    # {'name': '09_unified_dataset', 'data': datasets.unifiedDataset, 'desc': 'Unified Benchmark Dataset'},
    {'name': '10_dirty_data', 'data': dirty_data, 'desc': 'Dirty Data (All Types & Edge Cases)'},
    {'name': '11_complex_nested', 'data': complex_nested, 'desc': 'Deeply Nested Complex Structure'},
    {'name': '12_nasty_strings', 'data': nasty_strings, 'desc': 'Nasty Strings (Unicode, Injection, Control Chars)'},
    {'name': '13_deep_recursion', 'data': deep_recursion, 'desc': 'Deep Recursion (50 Levels)'},
    {'name': '14_hiking_example', 'data': hiking_example, 'desc': 'Hiking Example (User Request)'}
]

print(f"Generating examples in {EXAMPLES_DIR}...\n")

for ex in examples:
    json_path = os.path.join(EXAMPLES_DIR, f"{ex['name']}.json")
    zon_path = os.path.join(EXAMPLES_DIR, f"{ex['name']}.zonf")

    json_content = json.dumps(ex['data'], indent=2, ensure_ascii=False)
    zon_content = zon.encode(ex['data'])

    with open(json_path, 'w', encoding='utf-8') as f:
        f.write(json_content)
    
    with open(zon_path, 'w', encoding='utf-8') as f:
        f.write(zon_content)

    print(f"✅ Generated {ex['name']}")
    print(f"   Description: {ex['desc']}")
    print(f"   JSON: {len(json_content.encode('utf-8'))} bytes")
    print(f"   ZON:  {len(zon_content.encode('utf-8'))} bytes")
    print('---')

print('\nDone! View the examples in the "examples/" folder.')
