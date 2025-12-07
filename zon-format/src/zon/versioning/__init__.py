"""ZON Document Versioning

Provides version embedding, extraction, and validation for schema evolution.
"""

from .versioning import (
    embed_version,
    extract_version,
    strip_version,
    compare_versions,
    is_compatible,
    ZonDocumentMetadata
)

from .migration import (
    ZonMigrationManager,
    MigrationFunction,
    register_migration
)

__all__ = [
    'embed_version',
    'extract_version',
    'strip_version',
    'compare_versions',
    'is_compatible',
    'ZonDocumentMetadata',
    'ZonMigrationManager',
    'MigrationFunction',
    'register_migration',
]
