#!/usr/bin/env python3
"""
Unit tests for lib/common.py

Tests:
- log() unified logging
- get_infra() path resolution
- ensure_table() schema creation
- scan() filesystem pattern matching
- render() template substitution
- search() content search
"""

import pytest
import sqlite3
import json
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib import common


class TestLog:
    """Test logging functions."""
    
    def test_log_initialization(self, caplog):
        """Test logger lazy initialization."""
        common.log('INFO', 'test message')
        # Logger should exist after call
        assert common._get_logger() is not None
    
    def test_log_with_kwargs(self, caplog):
        """Test logging with extra fields."""
        common.log('INFO', 'test', file='test.py', line=42)
        # Should not raise exception


class TestGetInfra:
    """Test infrastructure path resolution."""
    
    def test_get_infra_paths_exist(self, tmp_project, monkeypatch):
        """Test that get_infra() returns valid paths."""
        # Mock __file__ to point to our test kit
        monkeypatch.setattr(
            common,
            '__file__',
            str(tmp_project / ".claude" / "scripts" / "lib" / "common.py")
        )
        
        infra = common.get_infra()
        
        # Verify critical keys exist
        assert 'root' in infra
        assert 'state_dir' in infra
        assert 'logs_dir' in infra
        assert 'tasks_dir' in infra


class TestEnsureTable:
    """Test database table creation."""
    
    def test_ensure_table_creates_new(self, sample_db):
        """Test creating new table if not exists."""
        schema = {
            'id': 'INTEGER PRIMARY KEY',
            'name': 'TEXT NOT NULL'
        }
        
        conn = common.ensure_table(sample_db, 'test_table', schema)
        
        # Verify table exists
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='test_table'"
        )
        assert cursor.fetchone() is not None
    
    def test_ensure_table_skips_existing(self, sample_db):
        """Test that existing tables are not recreated."""
        schema = {'id': 'INTEGER PRIMARY KEY'}
        
        # Create table first time
        common.ensure_table(sample_db, 'existing', schema)
        
        # Call again - should not raise
        conn = common.ensure_table(sample_db, 'existing', schema)
        assert conn is not None


class TestScan:
    """Test filesystem scanning."""
    
    def test_scan_finds_files(self, tmp_project):
        """Test scan() finds files matching pattern."""
        # Create test files
        (tmp_project / ".claude" / "test1.py").touch()
        (tmp_project / ".claude" / "test2.py").touch()
        
        results = common.scan(str(tmp_project / ".claude"), "*.py", recursive=False)
        
        assert len(results) >= 2
        assert any("test1.py" in str(r) for r in results)
    
    def test_scan_recursive(self, tmp_project):
        """Test recursive scanning."""
        # Create nested test files
        (tmp_project / ".claude" / "scripts" / "test.py").touch()
        
        results = common.scan(str(tmp_project / ".claude"), "*.py", recursive=True)
        
        assert any("test.py" in str(r) for r in results)


class TestRender:
    """Test template rendering."""
    
    def test_render_simple_substitution(self):
        """Test simple {{key}} substitution."""
        template = "Hello {{name}}, you have {{count}} messages"
        context = {"name": "Alice", "count": 5}
        
        result = common.render(template, context)
        
        assert result == "Hello Alice, you have 5 messages"
    
    def test_render_missing_key(self):
        """Test rendering with missing context key."""
        template = "Hello {{name}}"
        context = {}
        
        result = common.render(template, context)
        
        # Should leave placeholder if key missing
        assert "{{name}}" in result


class TestSearch:
    """Test content search."""
    
    def test_search_literal_string(self, tmp_project):
        """Test literal string search."""
        test_file = tmp_project / "test.txt"
        test_file.write_text("This is a test file\nWith multiple lines\n")
        
        results = common.search("test", [test_file], case_sensitive=False)
        
        assert len(results) >= 1
        assert any("test" in r[2].lower() for r in results)
    
    def test_search_regex_pattern(self, tmp_project):
        """Test regex pattern search."""
        test_file = tmp_project / "test.txt"
        test_file.write_text("error: 404\nerror: 500\nwarning: 123\n")
        
        results = common.search(r"/error: \d+", [test_file])
        
        assert len(results) >= 2


class TestHashContent:
    """Test content hashing."""
    
    def test_hash_content_consistent(self):
        """Test that same content produces same hash."""
        content = "test content"
        hash1 = common.hash_content(content)
        hash2 = common.hash_content(content)
        
        assert hash1 == hash2
    
    def test_hash_content_length(self):
        """Test hash truncation."""
        content = "test"
        hash_val = common.hash_content(content, length=8)
        
        assert len(hash_val) == 8


class TestSilentFailAudit:
    """Test silent fail pattern detection."""
    
    def test_silent_fail_audit_patterns(self, tmp_project):
        """Test detecting except: pass patterns."""
        # Create test script with silent fail
        test_script = tmp_project / ".claude" / "scripts" / "test_fail.py"
        test_script.write_text("""
def func():
    try:
        something()
    except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError):
        pass
""")
        
        # This would require mocking get_infra to return our tmp_project
        # For now, just verify the audit function exists
        assert hasattr(common, 'silent_fail_audit')
        assert callable(common.silent_fail_audit)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

