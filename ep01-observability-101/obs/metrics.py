"""Two meter types, built from scratch, to show what they actually are
underneath a real library like Micrometer.

A Counter only ever goes up. A Gauge reports whatever the value is right
now, and can go up or down. Modelling the wrong shape of data with the
wrong type (e.g. a Counter for something that resets) is the single most
common metrics mistake — see the "Micrometer Counters and Gauges
Explained" episode for the real version of this mistake in practice.
"""
from dataclasses import dataclass, field


@dataclass
class Counter:
    name: str
    value: int = 0

    def increment(self, by: int = 1):
        if by < 0:
            raise ValueError("a Counter can only go up — that's the whole point of it")
        self.value += by


@dataclass
class Gauge:
    name: str
    value: float = 0.0

    def set(self, value: float):
        self.value = value

    def increment(self, by: float = 1.0):
        self.value += by

    def decrement(self, by: float = 1.0):
        self.value -= by


class Registry:
    """The smallest possible stand-in for a MeterRegistry: a place every
    meter is registered, so a snapshot can print all of them together."""

    def __init__(self):
        self._meters = {}

    def counter(self, name: str) -> Counter:
        return self._meters.setdefault(name, Counter(name))

    def gauge(self, name: str) -> Gauge:
        return self._meters.setdefault(name, Gauge(name))

    def snapshot(self) -> dict:
        return {name: m.value for name, m in self._meters.items()}
