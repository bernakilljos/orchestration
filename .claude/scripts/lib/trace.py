#!/usr/bin/env python3
"""
Lightweight OpenTelemetry-inspired tracing without external dependencies.

Pure Python implementation for:
- Trace ID generation and propagation
- Span tracking (start/end timing)
- Context correlation across function calls
- Integration with structured_logger

Usage:
    from lib.trace import Tracer, get_trace_id, set_trace_id

    tracer = Tracer(__name__)
    with tracer.span("operation_name"):
        # Code to trace
        pass

    # Or manual tracing
    set_trace_id("custom-trace-id")
    tracer.span_start("my_span")
    # ... do work ...
    tracer.span_end("my_span")
"""

import time
import json
from pathlib import Path
from typing import Dict, Optional, Any
from datetime import datetime
import threading
from contextlib import contextmanager

from .structured_logger import (
    get_trace_id,
    set_trace_id,
    new_trace_id,
    get_logger
)

class Span:
    """Represents a single span (unit of work)."""

    def __init__(self, trace_id: str, span_id: str, name: str, start_time: float):
        self.trace_id = trace_id
        self.span_id = span_id
        self.name = name
        self.start_time = start_time
        self.end_time: Optional[float] = None
        self.attributes: Dict[str, Any] = {}
        self.status = "UNSET"  # UNSET, OK, ERROR
        self.error: Optional[str] = None

    def set_attribute(self, key: str, value: Any):
        """Set a span attribute."""
        self.attributes[key] = value

    def set_status(self, status: str, error: Optional[str] = None):
        """Set span status (OK, ERROR)."""
        self.status = status
        if error:
            self.error = error

    def end(self):
        """Mark span as ended."""
        self.end_time = time.time()

    @property
    def duration_ms(self) -> Optional[float]:
        """Get span duration in milliseconds."""
        if self.end_time is None:
            return None
        return (self.end_time - self.start_time) * 1000

    def to_dict(self) -> Dict[str, Any]:
        """Convert span to dict (for JSON export)."""
        return {
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "name": self.name,
            "start_time": datetime.fromtimestamp(self.start_time).isoformat() + "Z",
            "end_time": datetime.fromtimestamp(self.end_time).isoformat() + "Z" if self.end_time else None,
            "duration_ms": self.duration_ms,
            "status": self.status,
            "error": self.error,
            "attributes": self.attributes,
        }

class Tracer:
    """Tracer for creating and managing spans."""

    def __init__(self, name: str):
        self.name = name
        self.logger = get_logger(name)
        self.spans: Dict[str, Span] = {}
        self.trace_id = new_trace_id()
        set_trace_id(self.trace_id)

    def set_trace_id(self, trace_id: str):
        """Set custom trace ID."""
        self.trace_id = trace_id
        set_trace_id(trace_id)

    def span_start(self, name: str, **attributes) -> str:
        """
        Start a new span.

        Args:
            name: Span name
            **attributes: Initial span attributes

        Returns:
            span_id
        """
        span_id = f"{len(self.spans):04d}"
        span = Span(self.trace_id, span_id, name, time.time())

        for key, value in attributes.items():
            span.set_attribute(key, value)

        self.spans[span_id] = span
        self.logger.debug(
            f"Span start: {name}",
            span_id=span_id,
            trace_id=self.trace_id
        )
        return span_id

    def span_end(self, span_id: str, status: str = "OK", error: Optional[str] = None):
        """
        End a span.

        Args:
            span_id: Span ID (returned by span_start)
            status: 'OK' or 'ERROR'
            error: Error message (if status=ERROR)
        """
        if span_id not in self.spans:
            self.logger.warning(f"Span not found: {span_id}")
            return

        span = self.spans[span_id]
        span.end()
        span.set_status(status, error)

        self.logger.debug(
            f"Span end: {span.name}",
            span_id=span_id,
            trace_id=self.trace_id,
            duration_ms=span.duration_ms,
            status=status
        )

    @contextmanager
    def span(self, name: str, **attributes):
        """
        Context manager for span creation.

        Usage:
            with tracer.span("my_operation", user_id=42):
                # Code here
                pass
        """
        span_id = self.span_start(name, **attributes)
        try:
            yield span_id
            self.span_end(span_id, status="OK")
        except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError) as e:
            self.span_end(span_id, status="ERROR", error=str(e))
            raise

    def set_span_attribute(self, span_id: str, key: str, value: Any):
        """Set an attribute on a span."""
        if span_id not in self.spans:
            return
        self.spans[span_id].set_attribute(key, value)

    def export_spans(self) -> str:
        """Export all spans as JSON."""
        spans = [span.to_dict() for span in self.spans.values()]
        return json.dumps(
            {
                "trace_id": self.trace_id,
                "name": self.name,
                "span_count": len(spans),
                "spans": spans,
            },
            indent=2,
            default=str
        )

    def save_spans(self, filename: Optional[str] = None):
        """Save spans to a JSON file."""
        if filename is None:
            log_dir = Path(__file__).parent.parent / "logs"
            log_dir.mkdir(exist_ok=True)
            filename = log_dir / f"traces-{self.trace_id}.json"

        with open(filename, 'w', encoding='utf-8') as f:
            f.write(self.export_spans())

        self.logger.info(f"Traces exported", file=str(filename), span_count=len(self.spans))

if __name__ == '__main__':
    # Test
    tracer = Tracer(__name__)
    tracer.logger.info("Tracer initialized", trace_id=tracer.trace_id)

    # Test span operations
    with tracer.span("test_operation_1", component="demo") as span_id:
        time.sleep(0.1)
        tracer.set_span_attribute(span_id, "status", "in_progress")

    # Manual span
    sid = tracer.span_start("test_operation_2", retry_count=0)
    time.sleep(0.05)
    tracer.set_span_attribute(sid, "result", "success")
    tracer.span_end(sid)

    # Export
    print("\n=== Trace Summary ===")
    print(f"Trace ID: {tracer.trace_id}")
    print(f"Total spans: {len(tracer.spans)}")
    for span in tracer.spans.values():
        print(f"  - {span.name} ({span.duration_ms:.1f}ms) [{span.status}]")

    tracer.save_spans()
    print("\n??Traces saved to: .claude/logs/")

