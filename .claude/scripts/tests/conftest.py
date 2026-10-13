#!/usr/bin/env python3
"""
Pytest fixtures for orchestration_v1 tests.

Provides:
- sample_db: Temporary SQLite database with orca schema
- mock_claude: Mock Anthropic API response
- tmp_project: Temporary kit project directory
- fake_hook_event: Mock hook event (UserPromptSubmit, PostToolUse, etc.)
"""

import pytest
import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import Mock, MagicMock
import json
from datetime import datetime


@pytest.fixture
def sample_db():
    """Create temporary in-memory SQLite database with orca.db schema."""
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()
    
    # Create minimal orca.db schema
    cursor.execute("""
        CREATE TABLE conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            turn INTEGER NOT NULL,
            role TEXT CHECK(role IN ('user','assistant','tool','system')),
            content TEXT NOT NULL,
            ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE workers (
            worker_id TEXT PRIMARY KEY,
            model TEXT,
            status TEXT,
            heartbeat TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            tasks_completed INTEGER DEFAULT 0
        )
    """)
    
    cursor.execute("""
        CREATE TABLE tasks (
            task_id TEXT PRIMARY KEY,
            status TEXT,
            worker_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE approval_requests (
            task_id TEXT PRIMARY KEY,
            command TEXT,
            category TEXT,
            status TEXT DEFAULT 'waiting_approval',
            requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    yield conn
    conn.close()


@pytest.fixture
def mock_claude():
    """Mock Anthropic API response."""
    mock = Mock()
    mock.messages.create.return_value = Mock(
        content=[Mock(text="Test response")],
        stop_reason="end_turn",
        usage=Mock(input_tokens=10, output_tokens=20)
    )
    return mock


@pytest.fixture
def tmp_project():
    """Create temporary project directory with minimal kit structure."""
    tmpdir = tempfile.TemporaryDirectory()
    proj_path = Path(tmpdir.name)
    
    # Create minimal directory structure
    (proj_path / ".claude" / "state").mkdir(parents=True, exist_ok=True)
    (proj_path / ".claude" / "logs").mkdir(parents=True, exist_ok=True)
    (proj_path / ".claude" / "tasks" / "done").mkdir(parents=True, exist_ok=True)
    (proj_path / ".claude" / "tasks" / "locks").mkdir(parents=True, exist_ok=True)
    (proj_path / ".claude" / "hooks").mkdir(parents=True, exist_ok=True)
    (proj_path / ".claude" / "scripts" / "lib").mkdir(parents=True, exist_ok=True)
    (proj_path / ".claude" / "skills").mkdir(parents=True, exist_ok=True)
    (proj_path / "plugins").mkdir(parents=True, exist_ok=True)
    
    yield proj_path
    tmpdir.cleanup()


@pytest.fixture
def fake_hook_event():
    """Create mock hook event payload."""
    return {
        "event_type": "UserPromptSubmit",
        "session_id": "sess_test_123",
        "timestamp": datetime.now().isoformat(),
        "content": "Test user prompt",
        "role": "user",
        "metadata": {
            "tool_name": "Read",
            "file_path": "/test/path"
        }
    }


@pytest.fixture
def mock_structured_logger(tmp_project):
    """Mock structured logger for testing."""
    logger_state = {"logs": []}
    
    def log(level, message, **kwargs):
        entry = {
            "level": level,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            **kwargs
        }
        logger_state["logs"].append(entry)
    
    logger_state["log"] = log
    return logger_state
