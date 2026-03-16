"""
Streaming utilities for real-time progress updates

This module provides Server-Sent Events (SSE) support for long-running operations,
allowing the server to push progress updates to clients in real-time.
"""
import json
import time
import queue
from typing import Any, Generator


class StreamingContext:
    """
    Context manager for streaming progress updates during long operations.

    This class manages a queue of events that will be sent to the client
    via Server-Sent Events (SSE). It provides methods to emit progress updates,
    completion signals, and error messages.

    Example:
        context = StreamingContext()

        context.emit_progress("processing", "Starting task...", 10)
        # ... do work ...
        context.emit_progress("processing", "Half done...", 50)
        # ... do work ...
        context.emit_complete({"result": "success"})

        for event in context.generator():
            yield event
    """

    def __init__(self):
        """Initialize the streaming context with an event queue."""
        self.events = queue.Queue()
        self.is_complete = False

    def emit_progress(self, stage: str, message: str, progress: int):
        """
        Emit a progress update event.

        Args:
            stage: The current stage of processing (e.g., "validation", "sections")
            message: Human-readable progress message
            progress: Progress percentage (0-100)
        """
        self.events.put({
            "type": "progress",
            "stage": stage,
            "message": message,
            "progress": progress,
            "timestamp": time.time()
        })

    def emit_complete(self, data: Any):
        """
        Emit a completion event with final data.

        Args:
            data: The final result data to send to the client
        """
        self.events.put({
            "type": "complete",
            "data": data,
            "progress": 100,
            "timestamp": time.time()
        })
        self.is_complete = True

    def emit_error(self, error: str):
        """
        Emit an error event.

        Args:
            error: Error message describing what went wrong
        """
        self.events.put({
            "type": "error",
            "error": error,
            "timestamp": time.time()
        })
        self.is_complete = True

    def generator(self) -> Generator[str, None, None]:
        """
        Generator function for yielding SSE events.

        Yields:
            SSE-formatted event strings (e.g., "data: {...}\\n\\n")

        The generator will keep yielding events until is_complete is True.
        It sends keepalive comments to prevent connection timeouts.
        """
        while True:
            try:
                event = self.events.get(timeout=0.1)
                yield f"data: {json.dumps(event)}\n\n"
                if self.is_complete:
                    break
            except queue.Empty:
                # Send keepalive to prevent connection timeout
                yield ": keepalive\n\n"


def format_sse_event(data: dict) -> str:
    """
    Format a dictionary as an SSE event string.

    Args:
        data: Dictionary to format as SSE event

    Returns:
        SSE-formatted string (e.g., "data: {...}\\n\\n")
    """
    return f"data: {json.dumps(data)}\n\n"
