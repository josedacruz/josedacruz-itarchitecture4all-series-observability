"""A minimal span/trace implementation.

A trace is a tree of spans, one per unit of work, linked by a shared
trace_id and each span's parent_id — that's the entire mechanism. A real
tracing SDK (OpenTelemetry, Micrometer Tracing) adds context propagation
across *process* boundaries (serializing trace_id/span_id into an
outgoing request's headers — the W3C `traceparent` header is the modern
standard — so the next service can continue the same trace with a new
child span), plus sampling and exporters, on top of this same idea; this
version keeps everything in one process, so the shape is visible without
any of that machinery.
"""
import time
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, field

ALL_TRACES: list["Trace"] = []


@dataclass
class Span:
    name: str
    trace_id: str
    span_id: str
    parent_id: str | None
    start: float
    end: float | None = None
    attributes: dict = field(default_factory=dict)

    @property
    def duration_ms(self) -> float:
        return round(((self.end or time.time()) - self.start) * 1000, 1)


class Trace:
    """Collects every span recorded under one trace_id."""

    def __init__(self, trace_id: str | None = None):
        self.trace_id = trace_id or uuid.uuid4().hex[:12]
        self.spans: list[Span] = []
        self._stack: list[str] = []
        ALL_TRACES.append(self)

    @contextmanager
    def start_span(self, name: str, **attributes):
        parent_id = self._stack[-1] if self._stack else None
        span = Span(
            name=name,
            trace_id=self.trace_id,
            span_id=uuid.uuid4().hex[:8],
            parent_id=parent_id,
            start=time.time(),
            attributes=attributes,
        )
        self.spans.append(span)
        self._stack.append(span.span_id)
        try:
            yield span
        finally:
            span.end = time.time()
            self._stack.pop()

    def depth_of(self, span: Span) -> int:
        depth = 0
        pid = span.parent_id
        while pid:
            depth += 1
            parent = next((s for s in self.spans if s.span_id == pid), None)
            pid = parent.parent_id if parent else None
        return depth

    def waterfall(self) -> str:
        """Render every span as an ASCII bar, proportional to its share
        of the trace's total duration — the same shape a tracing UI's
        waterfall view draws, in a terminal. See dashboard.py for the
        same data rendered as real HTML/SVG."""
        if not self.spans:
            return "(empty trace)"
        root = self.spans[0]
        total_ms = max(root.duration_ms, 0.1)
        width = 40
        lines = [f"trace {self.trace_id}  (total {root.duration_ms} ms)"]
        for span in self.spans:
            depth = self.depth_of(span)
            offset_ms = (span.start - root.start) * 1000
            bar_start = int((offset_ms / total_ms) * width)
            bar_len = max(1, int((span.duration_ms / total_ms) * width))
            bar = " " * bar_start + "#" * bar_len
            indent = "  " * depth
            lines.append(f"{indent}{span.name:<20} {bar:<{width}} {span.duration_ms} ms")
        return "\n".join(lines)

    def to_dict(self) -> dict:
        root = self.spans[0]
        return {
            "trace_id": self.trace_id,
            "total_ms": root.duration_ms,
            "spans": [
                {
                    "name": s.name,
                    "span_id": s.span_id,
                    "parent_id": s.parent_id,
                    "depth": self.depth_of(s),
                    "offset_ms": round((s.start - root.start) * 1000, 1),
                    "duration_ms": s.duration_ms,
                    "attributes": s.attributes,
                }
                for s in self.spans
            ],
        }
