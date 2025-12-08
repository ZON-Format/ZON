# ZON Versioning & Migration System

The ZON versioning system provides document-level schema versioning with automatic migration support, enabling seamless schema evolution and backward/forward compatibility.

## Overview

ZON's versioning system includes:

- **Document Versioning**: Embed version metadata in ZON documents
- **Migration Manager**: Automatic migration path finding using BFS
- **Compatibility Checking**: Validate version compatibility
- **Chained Migrations**: Support for multi-step migration paths
- **Schema Evolution**: Track and manage schema changes over time

## Quick Start

```python
from zon import embed_version, extract_version, ZonMigrationManager

# Embed version in data
data = {"name": "Alice", "age": 30}
versioned = embed_version(data, "1.0.0", "user-schema")

# Extract version metadata
meta = extract_version(versioned)
print(f"Version: {meta['version']}, Schema: {meta['schema_id']}")

# Migrate between versions
manager = ZonMigrationManager()
manager.register_migration("1.0.0", "2.0.0", upgrade_fn)
migrated = manager.migrate(data, "1.0.0", "2.0.0")
```

## Version Metadata

### Embedding Versions

The `embed_version()` function adds version metadata to your data:

```python
from zon import embed_version

data = {
    "users": [
        {"id": 1, "name": "Alice"},
        {"id": 2, "name": "Bob"}
    ]
}

# Embed version 1.0.0
versioned = embed_version(data, "1.0.0", "user-list-schema")

# Result includes __zon_version__ metadata
# {
#     "__zon_version__": {
#         "version": "1.0.0",
#         "schema_id": "user-list-schema",
#         "timestamp": "2024-01-01T12:00:00Z"
#     },
#     "users": [...]
# }
```

### Extracting Versions

Extract version metadata from versioned documents:

```python
from zon import extract_version

meta = extract_version(versioned_data)

print(meta['version'])      # "1.0.0"
print(meta['schema_id'])    # "user-list-schema"
print(meta['timestamp'])    # ISO 8601 timestamp
```

### Stripping Versions

Remove version metadata when no longer needed:

```python
from zon import strip_version

# Remove version metadata
clean_data = strip_version(versioned_data)

# Original data without __zon_version__ key
assert '__zon_version__' not in clean_data
```

## Version Comparison

### compare_versions(v1: str, v2: str) -> int

Compare semantic versions:

```python
from zon import compare_versions

result = compare_versions("1.2.0", "1.1.5")
# Returns: 1 (v1 > v2)
# Returns: 0 (v1 == v2)
# Returns: -1 (v1 < v2)

# Use in sorting
versions = ["1.2.0", "1.0.1", "2.0.0", "1.1.0"]
sorted_versions = sorted(versions, key=lambda v: (compare_versions(v, "0.0.0"), v))
```

### is_compatible(current: str, required: str) -> bool

Check if versions are compatible:

```python
from zon import is_compatible

# Check backward compatibility
if is_compatible("2.1.0", "2.0.0"):
    print("Version 2.1.0 is compatible with 2.0.0")

# Major version changes are incompatible
assert not is_compatible("2.0.0", "1.0.0")
```

## Migration Manager

### Setting Up Migrations

```python
from zon import ZonMigrationManager

manager = ZonMigrationManager()

# Register a migration from 1.0.0 to 2.0.0
def migrate_1_to_2(data):
    """Add 'email' field to users."""
    for user in data['users']:
        user['email'] = f"{user['name'].lower()}@example.com"
    return data

manager.register_migration("1.0.0", "2.0.0", migrate_1_to_2)

# Register another migration from 2.0.0 to 3.0.0
def migrate_2_to_3(data):
    """Rename 'name' to 'full_name'."""
    for user in data['users']:
        user['full_name'] = user.pop('name')
    return data

manager.register_migration("2.0.0", "3.0.0", migrate_2_to_3)
```

### Performing Migrations

```python
# Migrate directly
v1_data = {"users": [{"id": 1, "name": "Alice"}]}
v2_data = manager.migrate(v1_data, "1.0.0", "2.0.0")

# Chained migration (1.0.0 -> 2.0.0 -> 3.0.0)
v3_data = manager.migrate(v1_data, "1.0.0", "3.0.0")

# Automatic path finding
assert v3_data['users'][0]['full_name'] == "Alice"
assert v3_data['users'][0]['email'] == "alice@example.com"
```

### Migration Path Finding

The manager uses BFS to find the shortest migration path:

```python
manager = ZonMigrationManager()

# Register migrations
manager.register_migration("1.0.0", "1.1.0", upgrade_minor)
manager.register_migration("1.1.0", "2.0.0", upgrade_major)
manager.register_migration("2.0.0", "2.1.0", add_feature)

# Find migration path
path = manager.find_migration_path("1.0.0", "2.1.0")
# Returns: ["1.0.0", "1.1.0", "2.0.0", "2.1.0"]

# Check if migration exists
if manager.has_migration_path("1.0.0", "3.0.0"):
    data = manager.migrate(data, "1.0.0", "3.0.0")
else:
    raise ValueError("No migration path available")
```

## Real-World Examples

### Example 1: User Schema Evolution

```python
from zon import ZonMigrationManager, embed_version, extract_version

manager = ZonMigrationManager()

# Version 1.0.0: Basic user
v1_schema = {
    "users": [
        {"id": 1, "name": "Alice"}
    ]
}

# Migration: 1.0.0 -> 2.0.0 (add email)
def add_email(data):
    for user in data['users']:
        user['email'] = f"{user['name'].lower()}@example.com"
    return data

# Migration: 2.0.0 -> 3.0.0 (add roles)
def add_roles(data):
    for user in data['users']:
        user['roles'] = ['user']
    return data

# Migration: 3.0.0 -> 4.0.0 (rename name to display_name)
def rename_name(data):
    for user in data['users']:
        user['display_name'] = user.pop('name')
    return data

# Register all migrations
manager.register_migration("1.0.0", "2.0.0", add_email)
manager.register_migration("2.0.0", "3.0.0", add_roles)
manager.register_migration("3.0.0", "4.0.0", rename_name)

# Load old data and migrate
old_data = load_from_file("users_v1.json")
versioned = embed_version(old_data, "1.0.0", "user-schema")

# Migrate to latest
meta = extract_version(versioned)
current_version = meta['version']

if current_version != "4.0.0":
    data = manager.migrate(old_data, current_version, "4.0.0")
    save_to_file(embed_version(data, "4.0.0", "user-schema"))
```

### Example 2: Configuration Migration

```python
from zon import ZonMigrationManager

manager = ZonMigrationManager()

# v1: Simple config
v1_config = {
    "database": "postgres://localhost/mydb",
    "port": 5432
}

# Migration: 1.0 -> 2.0 (split database URL)
def split_db_url(config):
    url = config.pop('database')
    config['database'] = {
        'type': 'postgres',
        'host': 'localhost',
        'name': 'mydb'
    }
    return config

# Migration: 2.0 -> 3.0 (add connection pool)
def add_pool(config):
    config['database']['pool'] = {
        'min_size': 5,
        'max_size': 20
    }
    return config

manager.register_migration("1.0", "2.0", split_db_url)
manager.register_migration("2.0", "3.0", add_pool)

# Migrate configuration
v3_config = manager.migrate(v1_config, "1.0", "3.0")
```

### Example 3: API Versioning

```python
from zon import embed_version, extract_version, ZonMigrationManager
from flask import request, jsonify

manager = ZonMigrationManager()

# Setup migrations
manager.register_migration("1.0", "2.0", upgrade_v1_to_v2)
manager.register_migration("2.0", "3.0", upgrade_v2_to_v3)

@app.route('/api/data', methods=['POST'])
def handle_data():
    data = request.json
    
    # Extract version from request
    meta = extract_version(data)
    client_version = meta.get('version', '1.0')
    
    # Migrate to current API version
    if client_version != CURRENT_API_VERSION:
        data = manager.migrate(
            data,
            client_version,
            CURRENT_API_VERSION
        )
    
    # Process data with current schema
    result = process_data(data)
    
    # Return with version
    return jsonify(embed_version(result, CURRENT_API_VERSION))
```

## Best Practices

### 1. Semantic Versioning

Use semantic versioning (MAJOR.MINOR.PATCH):

```python
# MAJOR: Breaking changes
"1.0.0" -> "2.0.0"  # Schema completely changed

# MINOR: Backward-compatible additions
"2.0.0" -> "2.1.0"  # Added optional fields

# PATCH: Bug fixes, no schema change
"2.1.0" -> "2.1.1"  # Fixed data validation
```

### 2. Always Version Your Data

```python
from zon import embed_version

# Do this
data = fetch_data()
versioned = embed_version(data, "1.0.0", "my-schema")
save_data(versioned)

# Not this
save_data(data)  # No version info!
```

### 3. Test Migrations

```python
import unittest
from zon import ZonMigrationManager

class TestMigrations(unittest.TestCase):
    def setUp(self):
        self.manager = ZonMigrationManager()
        setup_migrations(self.manager)
    
    def test_v1_to_v2(self):
        v1_data = {"users": [{"id": 1, "name": "Alice"}]}
        v2_data = self.manager.migrate(v1_data, "1.0.0", "2.0.0")
        
        # Verify email was added
        self.assertIn('email', v2_data['users'][0])
    
    def test_chained_migration(self):
        v1_data = {"users": [{"id": 1, "name": "Alice"}]}
        v3_data = self.manager.migrate(v1_data, "1.0.0", "3.0.0")
        
        # Verify all transformations
        self.assertIn('email', v3_data['users'][0])
        self.assertIn('roles', v3_data['users'][0])
```

### 4. Handle Missing Migrations

```python
from zon import ZonMigrationManager

manager = ZonMigrationManager()

try:
    migrated = manager.migrate(data, "1.0.0", "5.0.0")
except ValueError as e:
    if "No migration path" in str(e):
        # Handle missing migration
        logger.error(f"Cannot migrate from 1.0.0 to 5.0.0")
        # Fallback strategy
        data = reset_to_latest_schema(data)
    else:
        raise
```

### 5. Document Your Migrations

```python
def migrate_v1_to_v2(data):
    """
    Migration: 1.0.0 -> 2.0.0
    
    Changes:
    - Add 'email' field to all users (generated from name)
    - Add 'created_at' timestamp (set to current time)
    - Remove deprecated 'nickname' field
    
    Breaking changes: None
    Backward compatible: Yes
    """
    # Implementation
    pass
```

## CLI Support

```bash
# Check version of ZON file
zon version data.zonf

# Migrate to new version
zon migrate data.zonf --from=1.0.0 --to=2.0.0 > migrated.zonf

# Validate version compatibility
zon validate data.zonf --min-version=2.0.0
```

## Advanced Topics

### Conditional Migrations

```python
def conditional_migration(data):
    """Apply different migrations based on data shape."""
    if 'legacy_format' in data:
        return migrate_legacy(data)
    elif 'users' in data:
        return migrate_users(data)
    else:
        return data
```

### Rollback Support

```python
class VersionManager:
    def __init__(self):
        self.manager = ZonMigrationManager()
        self.history = []
    
    def migrate_with_rollback(self, data, from_v, to_v):
        # Save original
        self.history.append((data, from_v))
        
        try:
            return self.manager.migrate(data, from_v, to_v)
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            return self.rollback()
    
    def rollback(self):
        if self.history:
            return self.history.pop()[0]
        raise ValueError("Nothing to rollback")
```

## Further Reading

- [API Reference](api-reference.md)
- [Migration Guide](migration-v1.2.md)
- [Schema Validation](schema-validation.md)
