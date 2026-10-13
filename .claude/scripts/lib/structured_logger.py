#!/usr/bin/env python3
"""
Structured JSON logging with trace correlation and observability.

Features:
- JSON format output (structured logging)
- Trace ID correlation across calls (pure Python, no external deps)
- Dual console + file output
- Auto level detection from kwargs
- Compatible with existing log() calls

Usage:
    from lib.structured_logger import StructuredLogger, new_trace_id, get_logger

    logger = get_logger(__name__)
    logger.info("Operation started", trace_id="abc123", user_id=42)
    # Output: {"timestamp":"2026-10-13T...", "level":"INFO", "logger":"__name__", "message":"Operation started", "trace_id":"abc123", "user_id":42}
"""

import sys
import os
import json
import logging
from pathlib import Path
from typing import Dict, Optional, Any
from datetime import datetime, timezone
import uuid
import threading

# Thread-local trace context
_trace_context = threading.local()

def new_trace_id() -> str:
    """Generate new trace ID (UUID4 short form)."""
    return str(uuid.uuid4())[:12]

def get_trace_id() -> Optional[str]:
    """Get current trace ID from thread-local context."""
    return getattr(_trace_context, 'trace_id', None)

def set_trace_id(trace_id: Optional[str]):
    """Set trace ID in thread-local context."""
    if trace_id:
        _trace_context.trace_id = trace_id
    else:
        _trace_context.trace_id = None

class StructuredFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        # Build structured log entry
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add trace ID if available
        trace_id = get_trace_id()
        if trace_id:
            log_entry["trace_id"] = trace_id

        # Add extra fields from record.__dict__ (populated by LoggerAdapter)
        if hasattr(record, 'extra_fields'):
            log_entry.update(record.extra_fields)

        return json.dumps(log_entry, ensure_ascii=False, default=str)

class StructuredLogger(logging.LoggerAdapter):
    """Logger adapter that adds structured fields."""

    def __init__(self, logger: logging.Logger, extra: Optional[Dict[str, Any]] = None):
        super().__init__(logger, extra or {})

    def process(self, msg: str, kwargs: Dict) -> tuple:
        """Process message and inject extra fields."""
        # Extract extra_fields from kwargs
        extra_fields = {}
        for key in list(kwargs.keys()):
            if key not in ['exc_info', 'stack_info', 'stacklevel']:
                extra_fields[key] = kwargs.pop(key)

        # Create a LogRecord with extra_fields
        if extra_fields:
            kwargs['extra'] = {'extra_fields': extra_fields}

        return msg, kwargs

def _get_or_create_logger(name: str) -> StructuredLogger:
    """Get or create a structured logger."""
    logger = logging.getLogger(name)

    # Only configure once
    if logger.handlers:
        return StructuredLogger(logger)

    logger.setLevel(logging.DEBUG)

    # Determine log directory
    log_dir = Path(__file__).parent.parent / "logs"
    log_dir.mkdir(exist_ok=True)

    # Console handler (INFO+)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(StructuredFormatter())
    logger.addHandler(console_handler)

    # File handler (DEBUG+)
    file_handler = logging.FileHandler(
        log_dir / "structured.log",
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(StructuredFormatter())
    logger.addHandler(file_handler)

    return StructuredLogger(logger)

# Global cache of loggers
_loggers: Dict[str, StructuredLogger] = {}

def get_logger(name: str) -> StructuredLogger:
    """Get a structured logger by name."""
    if name not in _loggers:
        _loggers[name] = _get_or_create_logger(name)
    return _loggers[name]

# Convenience function for backward compatibility with common.log()
def log(level: str, msg: str, **kwargs):
    """
    Log a message with structured fields (compatible with common.log()).

    Args:
        level: 'DEBUG', 'INFO', 'WARN', 'ERROR', 'CRITICAL'
        msg: Message text
        **kwargs: Extra structured fields
    """
    logger = get_logger(__name__)
    level_name = level.upper()

    # Map 'WARN' to 'WARNING' for logging
    if level_name == 'WARN':
        level_name = 'WARNING'

    # Call appropriate logging method
    getattr(logger, level_name.lower())(msg, **kwargs)

if __name__ == '__main__':
    # Test
    logger = get_logger(__name__)

    trace_id = new_trace_id()
    set_trace_id(trace_id)

    logger.info("Structured logging test", version="1.0", test_field=42)
    logger.debug("Debug message", operation="startup", duration_ms=123)
    logger.warning("Warning example", severity="low", component="worker")
    logger.error("Error occurred", error_code="ERR_001", retry_count=3)

    # Test backward-compat log()
    log('INFO', 'Backward compat test', module='lib', status='ok')

    print("\n[OK] Structured logs written to: .claude/logs/structured.log")
