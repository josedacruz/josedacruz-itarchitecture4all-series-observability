"""RED: Rate, Errors, Duration — Tom Wilkie's method (Weaveworks, 2015),
for request-driven services. Measures from the caller's side: how many
requests, how many failed, how long each one took. Deliberately the
Four Golden Signals minus saturation — RED doesn't look at the resource
underneath a request at all, which is exactly its blind spot.
"""
from dataclasses import dataclass, field


@dataclass
class RedMetrics:
    requests: int = 0
    errors: int = 0
    durations_ms: list = field(default_factory=list)
    failed: list = field(default_factory=list)  # one bool per request, same order as durations_ms

    def record(self, duration_ms: float, *, error: bool = False):
        self.requests += 1
        self.durations_ms.append(duration_ms)
        self.failed.append(error)
        if error:
            self.errors += 1

    @property
    def error_rate_pct(self) -> float:
        return round(100 * self.errors / self.requests, 1) if self.requests else 0.0

    @property
    def avg_duration_ms(self) -> float:
        return round(sum(self.durations_ms) / len(self.durations_ms), 1) if self.durations_ms else 0.0

    @property
    def avg_success_duration_ms(self) -> float:
        # Failures are often fast (a killed process answers in milliseconds),
        # so one average over everything can *improve* while the service
        # fails. Keeping successes separate is what exposes that.
        ok = [d for d, bad in zip(self.durations_ms, self.failed) if not bad]
        return round(sum(ok) / len(ok), 1) if ok else 0.0

    def snapshot(self) -> dict:
        return {
            "rate_req": self.requests,
            "errors": self.errors,
            "error_rate_pct": self.error_rate_pct,
            "avg_duration_ms": self.avg_duration_ms,
            "avg_success_ms": self.avg_success_duration_ms,
        }
