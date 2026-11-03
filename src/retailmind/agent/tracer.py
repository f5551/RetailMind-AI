"""RetailMind AI — JSONL Execution Tracer."""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


class ExecutionTracer:
    """Records authentic execution traces for model calls, tools, and stops."""

    def __init__(self, task_id: str, session_id: str):
        self.task_id = task_id
        self.session_id = session_id
        self.events: List[Dict[str, Any]] = []

    def log_event(
        self,
        event_type: str,
        turn_index: int,
        data: Dict[str, Any],
        cost_info: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Appends a timestamped execution event."""
        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "task_id": self.task_id,
            "session_id": self.session_id,
            "turn_index": turn_index,
            "event_type": event_type,
            "data": data,
        }
        if cost_info:
            event["cost_info"] = cost_info
        self.events.append(event)

    def save_jsonl(self, file_path: Path) -> Path:
        """Serializes recorded trace events to a JSONL file."""
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            for event in self.events:
                f.write(json.dumps(event, default=str) + "\n")
        return file_path
