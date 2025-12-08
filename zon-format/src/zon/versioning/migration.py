"""ZON Data Migration Manager

Manages schema migrations for evolving ZON data structures.
Supports versioned migration functions with automatic path finding using BFS.
"""

from typing import Any, Callable, Optional, List, Dict, Tuple
from collections import deque
from dataclasses import dataclass


MigrationFunction = Callable[[Any, str, str], Any]


@dataclass
class Migration:
    """Represents a single migration"""
    
    from_version: str
    to_version: str
    migrate: MigrationFunction
    description: Optional[str] = None


class ZonMigrationManager:
    """Manager for ZON schema migrations.
    
    Allows registering migration functions and automatically finding migration paths.
    """
    
    def __init__(self):
        self.migrations: Dict[str, Migration] = {}
    
    def register_migration(
        self,
        from_version: str,
        to_version: str,
        migrate: MigrationFunction,
        description: Optional[str] = None
    ) -> None:
        """Registers a migration from one version to another.
        
        Args:
            from_version: Source version
            to_version: Target version
            migrate: Migration function
            description: Optional description of the migration
            
        Example:
            >>> manager = ZonMigrationManager()
            >>> def add_email(data, from_v, to_v):
            ...     if 'users' in data:
            ...         for user in data['users']:
            ...             user['email'] = f"{user['name']}@example.com"
            ...     return data
            >>> manager.register_migration("1.0.0", "2.0.0", add_email,
            ...     "Added email field to users")
        """
        key = f"{from_version}->{to_version}"
        self.migrations[key] = Migration(
            from_version=from_version,
            to_version=to_version,
            migrate=migrate,
            description=description
        )
    
    def migrate(
        self,
        data: Any,
        from_version: str,
        to_version: str,
        verbose: bool = False
    ) -> Any:
        """Migrates data from one version to another.
        
        Automatically finds the migration path if direct migration not available.
        
        Args:
            data: Data to migrate
            from_version: Current version
            to_version: Target version
            verbose: Print migration steps
            
        Returns:
            Migrated data
            
        Raises:
            ValueError: If no migration path exists
            
        Example:
            >>> manager = ZonMigrationManager()
            >>> # Register migrations...
            >>> migrated = manager.migrate(data, "1.0.0", "2.0.0")
        """
        if from_version == to_version:
            return data
        
        direct_key = f"{from_version}->{to_version}"
        if direct_key in self.migrations:
            migration = self.migrations[direct_key]
            if verbose:
                print(f"Migrating {from_version} → {to_version}: "
                      f"{migration.description or 'no description'}")
            return migration.migrate(data, from_version, to_version)
        
        path = self._find_migration_path(from_version, to_version)
        
        if not path:
            raise ValueError(
                f"No migration path found from {from_version} to {to_version}"
            )
        
        current = data
        for migration in path:
            if verbose:
                print(f"Migrating {migration.from_version} → {migration.to_version}: "
                      f"{migration.description or 'no description'}")
            current = migration.migrate(current, migration.from_version, migration.to_version)
        
        return current
    
    def _find_migration_path(
        self,
        from_version: str,
        to_version: str
    ) -> Optional[List[Migration]]:
        """Finds a migration path between two versions using BFS.
        
        Args:
            from_version: Source version
            to_version: Target version
            
        Returns:
            List of migrations to apply, or None if no path exists
        """
        visited = set()
        queue = deque([(from_version, [])])
        
        while queue:
            version, path = queue.popleft()
            
            if version == to_version:
                return path
            
            if version in visited:
                continue
            
            visited.add(version)
            
            for key, migration in self.migrations.items():
                if migration.from_version == version:
                    new_path = path + [migration]
                    queue.append((migration.to_version, new_path))
        
        return None
    
    def has_migration(self, from_version: str, to_version: str) -> bool:
        """Checks if a migration path exists between versions.
        
        Args:
            from_version: Source version
            to_version: Target version
            
        Returns:
            True if migration path exists
        """
        if from_version == to_version:
            return True
        
        direct_key = f"{from_version}->{to_version}"
        if direct_key in self.migrations:
            return True
        
        return self._find_migration_path(from_version, to_version) is not None
    
    def get_available_versions(self) -> List[str]:
        """Gets list of all versions involved in migrations.
        
        Returns:
            Sorted list of version strings
        """
        versions = set()
        for migration in self.migrations.values():
            versions.add(migration.from_version)
            versions.add(migration.to_version)
        return sorted(versions)


_global_migration_manager = ZonMigrationManager()


def register_migration(
    from_version: str,
    to_version: str,
    migrate: MigrationFunction,
    description: Optional[str] = None
) -> None:
    """Registers a migration in the global migration manager.
    
    Args:
        from_version: Source version
        to_version: Target version
        migrate: Migration function
        description: Optional description
        
    Example:
        >>> @register_migration("1.0.0", "2.0.0", "Add email field")
        >>> def add_email_migration(data, from_v, to_v):
        ...     # migration logic
        ...     return data
    """
    _global_migration_manager.register_migration(
        from_version,
        to_version,
        migrate,
        description
    )


def get_global_migration_manager() -> ZonMigrationManager:
    """Gets the global migration manager instance."""
    return _global_migration_manager
