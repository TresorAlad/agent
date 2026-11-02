import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class TraceStep:
    step: int
    kind: str
    tool: str | None = None
    args_summary: str | None = None
    result_summary: str | None = None
    ts: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    meta: dict[str, Any] = field(default_factory=dict)


class TraceCollector:
    def __init__(self) -> None:
        self.steps: list[TraceStep] = []
        self._counter = 0

    def add(self, **kwargs: Any) -> TraceStep:
        self._counter += 1
        entry = TraceStep(step=self._counter, **kwargs)
        self.steps.append(entry)
        return entry

    def to_list(self) -> list[dict]:
        return [asdict(s) for s in self.steps]

    def to_json(self) -> str:
        return json.dumps(self.to_list(), ensure_ascii=False, indent=2)


def summarize_result(content: str, max_len: int = 200) -> str:
    text = content.strip()
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."
