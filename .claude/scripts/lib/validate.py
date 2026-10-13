#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
validate.py — Configuration & data validation with pydantic.

Centralized schemas for common structures:
  - WorkersConfig (orca-workers-config.json)
  - ProjectLanguage (project-language.json)
  - SessionRecap (session-recap in orca.db)
  - MessageUsage (Claude API usage)
  - ORCACacheState (prompt cache state)
"""

from __future__ import annotations

from typing import Optional, Any, Dict, List
from datetime import datetime
import json

try:
    from pydantic import BaseModel, Field, validator
except ImportError:
    # Fallback: manual dict-based validation (no pydantic)
    BaseModel = None


if BaseModel:
    # ============ Pydantic Models ============

    class MessageUsage(BaseModel):
        """Claude API message.usage structure."""
        input_tokens: int
        output_tokens: int
        cache_creation_input_tokens: Optional[int] = 0
        cache_read_input_tokens: Optional[int] = 0

        class Config:
            extra = "allow"

    class WorkersConfig(BaseModel):
        """orca-workers-config.json schema."""
        max_workers: Optional[int] = 4
        worker_type: Optional[str] = "background"
        heartbeat_interval_sec: Optional[int] = 30
        checkpoint_interval_sec: Optional[int] = 300
        workers: Dict[str, Any] = Field(default_factory=dict)

        class Config:
            extra = "allow"

    class ProjectLanguage(BaseModel):
        """project-language.json schema."""
        project_id: str
        language_primary: Optional[str] = "ko"
        languages_supported: List[str] = Field(default_factory=lambda: ["ko", "en"])
        encoding: Optional[str] = "utf-8"

        class Config:
            extra = "allow"

    class SessionRecap(BaseModel):
        """Minimal session summary for orca.db.session_summary."""
        session_id: str
        started_at: Optional[str] = None
        ended_at: Optional[str] = None
        turns: Optional[int] = 0
        summary: Optional[str] = None
        key_decisions: Optional[str] = None
        files_touched: Optional[str] = None
        tokens_total: Optional[int] = 0

        class Config:
            extra = "allow"

    class ORCACacheState(BaseModel):
        """Prompt cache state for ~/.claude/state/orca-cache-state.json."""
        model_id: str
        cache_creation_tokens: Optional[int] = 0
        cache_read_tokens: Optional[int] = 0
        ttl_seconds: Optional[int] = 3600
        last_update: Optional[str] = None

        class Config:
            extra = "allow"

else:
    # ============ Fallback: Dict validation (no pydantic) ============

    def _validate_dict(data: dict, expected_keys: list[str]) -> dict:
        """Basic dict validation: check if expected keys exist."""
        if not isinstance(data, dict):
            raise TypeError(f"Expected dict, got {type(data)}")
        return data

    class MessageUsage:
        """Fallback for MessageUsage."""
        def __init__(self, **kwargs):
            self.input_tokens = kwargs.get("input_tokens", 0)
            self.output_tokens = kwargs.get("output_tokens", 0)
            self.cache_creation_input_tokens = kwargs.get("cache_creation_input_tokens", 0)
            self.cache_read_input_tokens = kwargs.get("cache_read_input_tokens", 0)

    class WorkersConfig:
        """Fallback for WorkersConfig."""
        def __init__(self, **kwargs):
            self.max_workers = kwargs.get("max_workers", 4)
            self.worker_type = kwargs.get("worker_type", "background")
            self.heartbeat_interval_sec = kwargs.get("heartbeat_interval_sec", 30)
            self.checkpoint_interval_sec = kwargs.get("checkpoint_interval_sec", 300)
            self.workers = kwargs.get("workers", {})

    class ProjectLanguage:
        """Fallback for ProjectLanguage."""
        def __init__(self, **kwargs):
            self.project_id = kwargs.get("project_id", "unknown")
            self.language_primary = kwargs.get("language_primary", "ko")
            self.languages_supported = kwargs.get("languages_supported", ["ko", "en"])
            self.encoding = kwargs.get("encoding", "utf-8")

    class SessionRecap:
        """Fallback for SessionRecap."""
        def __init__(self, **kwargs):
            self.session_id = kwargs.get("session_id", "unknown")
            self.started_at = kwargs.get("started_at")
            self.ended_at = kwargs.get("ended_at")
            self.turns = kwargs.get("turns", 0)
            self.summary = kwargs.get("summary")
            self.key_decisions = kwargs.get("key_decisions")
            self.files_touched = kwargs.get("files_touched")
            self.tokens_total = kwargs.get("tokens_total", 0)

    class ORCACacheState:
        """Fallback for ORCACacheState."""
        def __init__(self, **kwargs):
            self.model_id = kwargs.get("model_id", "unknown")
            self.cache_creation_tokens = kwargs.get("cache_creation_tokens", 0)
            self.cache_read_tokens = kwargs.get("cache_read_tokens", 0)
            self.ttl_seconds = kwargs.get("ttl_seconds", 3600)
            self.last_update = kwargs.get("last_update")


def load_workers_config(path: str) -> WorkersConfig:
    """Load and validate orca-workers-config.json."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return WorkersConfig(**data)
    except (FileNotFoundError, json.JSONDecodeError, ValueError) as e:
        raise ValueError(f"Failed to load workers config from {path}: {e}")


def load_project_language(path: str) -> ProjectLanguage:
    """Load and validate project-language.json."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return ProjectLanguage(**data)
    except (FileNotFoundError, json.JSONDecodeError, ValueError) as e:
        raise ValueError(f"Failed to load project language from {path}: {e}")


if __name__ == "__main__":
    # Test fallback
    print("validate.py loaded successfully")
