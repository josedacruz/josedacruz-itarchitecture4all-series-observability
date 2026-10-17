"""USE: Utilization, Saturation, Errors — Brendan Gregg's method, for any
resource (CPU, memory, a queue, a disk). "For every resource, check
utilization, saturation and errors." Measures from the system's side:
how busy is it, how much extra work is piling up waiting, and how many
resource-level errors (allocation failures, GC retries) it's throwing.
Unlike RED, USE has no notion of "a request" at all — it doesn't know
or care whether the caller's request succeeded.
"""
from dataclasses import dataclass, field


@dataclass
class UseMetrics:
    utilization_pct: list = field(default_factory=list)  # one sample per tick
    saturation: list = field(default_factory=list)        # queued/waiting work per tick
    errors: int = 0
    error_ticks: list = field(default_factory=list)       # which tick each error happened on (1-based)

    def sample(self, utilization_pct: float, saturation: int, *, error: bool = False):
        self.utilization_pct.append(utilization_pct)
        self.saturation.append(saturation)
        if error:
            self.errors += 1
            self.error_ticks.append(len(self.utilization_pct))

    @property
    def current_utilization_pct(self) -> float:
        return self.utilization_pct[-1] if self.utilization_pct else 0.0

    @property
    def current_saturation(self) -> int:
        return self.saturation[-1] if self.saturation else 0

    def snapshot(self) -> dict:
        return {
            "utilization_pct": self.current_utilization_pct,
            "saturation": self.current_saturation,
            "errors": self.errors,
        }
