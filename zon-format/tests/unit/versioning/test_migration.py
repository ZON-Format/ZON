"""Tests for ZON migration manager"""

import pytest
from zon.versioning import ZonMigrationManager


class TestMigrationBasics:
    """Basic migration tests"""
    
    def test_register_migration(self):
        """Test registering a migration"""
        manager = ZonMigrationManager()
        
        def migrate_fn(data, from_v, to_v):
            return {**data, "migrated": True}
        
        manager.register_migration("1.0.0", "2.0.0", migrate_fn, "Test migration")
        
        assert manager.has_migration("1.0.0", "2.0.0")
    
    def test_direct_migration(self):
        """Test direct migration"""
        manager = ZonMigrationManager()
        
        def add_field(data, from_v, to_v):
            return {**data, "newField": "value"}
        
        manager.register_migration("1.0.0", "2.0.0", add_field)
        
        data = {"oldField": "test"}
        result = manager.migrate(data, "1.0.0", "2.0.0")
        
        assert result["oldField"] == "test"
        assert result["newField"] == "value"
    
    def test_no_migration_needed(self):
        """Test migration with same version"""
        manager = ZonMigrationManager()
        
        data = {"test": "value"}
        result = manager.migrate(data, "1.0.0", "1.0.0")
        
        assert result == data
    
    def test_migration_not_found(self):
        """Test error when migration not found"""
        manager = ZonMigrationManager()
        
        data = {"test": "value"}
        
        with pytest.raises(ValueError, match="No migration path found"):
            manager.migrate(data, "1.0.0", "2.0.0")


class TestChainedMigrations:
    """Test chained migrations using BFS path finding"""
    
    def test_two_step_migration(self):
        """Test migration through two steps"""
        manager = ZonMigrationManager()
        
        def v1_to_v2(data, from_v, to_v):
            return {**data, "field_v2": "added in v2"}
        
        def v2_to_v3(data, from_v, to_v):
            return {**data, "field_v3": "added in v3"}
        
        manager.register_migration("1.0.0", "2.0.0", v1_to_v2)
        manager.register_migration("2.0.0", "3.0.0", v2_to_v3)
        
        data = {"original": "value"}
        result = manager.migrate(data, "1.0.0", "3.0.0")
        
        assert result["original"] == "value"
        assert result["field_v2"] == "added in v2"
        assert result["field_v3"] == "added in v3"
    
    def test_three_step_migration(self):
        """Test migration through three steps"""
        manager = ZonMigrationManager()
        
        manager.register_migration("1.0.0", "1.1.0", 
            lambda d, f, t: {**d, "v1_1": True})
        manager.register_migration("1.1.0", "1.2.0",
            lambda d, f, t: {**d, "v1_2": True})
        manager.register_migration("1.2.0", "2.0.0",
            lambda d, f, t: {**d, "v2_0": True})
        
        data = {"start": "value"}
        result = manager.migrate(data, "1.0.0", "2.0.0")
        
        assert result["start"] == "value"
        assert result["v1_1"] is True
        assert result["v1_2"] is True
        assert result["v2_0"] is True
    
    def test_complex_migration_graph(self):
        """Test migration with multiple possible paths (BFS finds shortest)"""
        manager = ZonMigrationManager()
        
        manager.register_migration("1.0.0", "1.1.0",
            lambda d, f, t: {**d, "path": d.get("path", "") + "A"})
        manager.register_migration("1.1.0", "2.0.0",
            lambda d, f, t: {**d, "path": d.get("path", "") + "B"})
        
        manager.register_migration("1.0.0", "2.0.0",
            lambda d, f, t: {**d, "path": "direct"})
        
        data = {"test": "value"}
        result = manager.migrate(data, "1.0.0", "2.0.0")
        
        assert result["path"] == "direct"


class TestMigrationWithRealData:
    """Test migrations with realistic data transformations"""
    
    def test_add_email_to_users(self):
        """Test adding email field to users"""
        manager = ZonMigrationManager()
        
        def add_email(data, from_v, to_v):
            if 'users' in data:
                for user in data['users']:
                    if 'email' not in user:
                        user['email'] = f"{user['name'].lower()}@example.com"
            return data
        
        manager.register_migration("1.0.0", "2.0.0", add_email,
            "Add email field to users")
        
        data = {
            "users": [
                {"id": 1, "name": "Alice"},
                {"id": 2, "name": "Bob"}
            ]
        }
        
        result = manager.migrate(data, "1.0.0", "2.0.0")
        
        assert result['users'][0]['email'] == "alice@example.com"
        assert result['users'][1]['email'] == "bob@example.com"
    
    def test_rename_field(self):
        """Test renaming a field"""
        manager = ZonMigrationManager()
        
        def rename_field(data, from_v, to_v):
            if 'oldName' in data:
                data['newName'] = data.pop('oldName')
            return data
        
        manager.register_migration("1.0.0", "2.0.0", rename_field)
        
        data = {"oldName": "value", "other": "data"}
        result = manager.migrate(data, "1.0.0", "2.0.0")
        
        assert 'oldName' not in result
        assert result['newName'] == "value"
        assert result['other'] == "data"
    
    def test_restructure_nested_data(self):
        """Test restructuring nested data"""
        manager = ZonMigrationManager()
        
        def flatten_config(data, from_v, to_v):
            if 'config' in data and 'settings' in data['config']:
                data['settings'] = data['config']['settings']
                del data['config']
            return data
        
        manager.register_migration("1.0.0", "2.0.0", flatten_config)
        
        data = {
            "config": {
                "settings": {"theme": "dark"}
            },
            "users": []
        }
        
        result = manager.migrate(data, "1.0.0", "2.0.0")
        
        assert 'config' not in result
        assert result['settings']['theme'] == "dark"


class TestMigrationHelpers:
    """Test migration helper methods"""
    
    def test_has_migration_direct(self):
        """Test has_migration for direct migration"""
        manager = ZonMigrationManager()
        manager.register_migration("1.0.0", "2.0.0", lambda d, f, t: d)
        
        assert manager.has_migration("1.0.0", "2.0.0") is True
        assert manager.has_migration("2.0.0", "3.0.0") is False
    
    def test_has_migration_chained(self):
        """Test has_migration for chained migration"""
        manager = ZonMigrationManager()
        manager.register_migration("1.0.0", "2.0.0", lambda d, f, t: d)
        manager.register_migration("2.0.0", "3.0.0", lambda d, f, t: d)
        
        assert manager.has_migration("1.0.0", "3.0.0") is True
    
    def test_has_migration_same_version(self):
        """Test has_migration for same version"""
        manager = ZonMigrationManager()
        
        assert manager.has_migration("1.0.0", "1.0.0") is True
    
    def test_get_available_versions(self):
        """Test getting available versions"""
        manager = ZonMigrationManager()
        manager.register_migration("1.0.0", "2.0.0", lambda d, f, t: d)
        manager.register_migration("2.0.0", "3.0.0", lambda d, f, t: d)
        manager.register_migration("1.5.0", "2.5.0", lambda d, f, t: d)
        
        versions = manager.get_available_versions()
        
        assert set(versions) == {"1.0.0", "1.5.0", "2.0.0", "2.5.0", "3.0.0"}
        assert versions == sorted(versions)


class TestMigrationVerbose:
    """Test verbose migration output"""
    
    def test_verbose_migration(self, capsys):
        """Test that verbose mode prints migration steps"""
        manager = ZonMigrationManager()
        
        manager.register_migration("1.0.0", "2.0.0",
            lambda d, f, t: d, "First migration")
        manager.register_migration("2.0.0", "3.0.0",
            lambda d, f, t: d, "Second migration")
        
        data = {"test": "value"}
        manager.migrate(data, "1.0.0", "3.0.0", verbose=True)
        
        captured = capsys.readouterr()
        assert "First migration" in captured.out
        assert "Second migration" in captured.out
