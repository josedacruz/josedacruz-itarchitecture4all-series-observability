"""Fires 20 checkout requests (one in five artificially slow, the
"incident" from the video) and prints the same story three ways:
the structured logs as they happen, the metrics snapshot afterwards,
and one full trace for the slowest request — then writes dashboard.html,
a real visual, no-dependency view of the same run.

Usage:
    python run_demo.py
"""
from obs import dashboard, logging_, tracing
from store import checkout, registry

TOTAL_REQUESTS = 20
SLOW_EVERY_N = 5


def main():
    print("=" * 70)
    print("1) LOGS — as each request happens")
    print("=" * 70)

    for i in range(1, TOTAL_REQUESTS + 1):
        slow = i % SLOW_EVERY_N == 0
        checkout(f"order-{i:03d}", simulate_slow_payment=slow)

    print()
    print("=" * 70)
    print("2) METRICS — snapshot after all requests")
    print("=" * 70)
    for name, value in registry.snapshot().items():
        print(f"  {name:<32} {value}")

    print()
    print("=" * 70)
    print("3) TRACES — the slowest request, explained")
    print("=" * 70)
    slow_trace = max(tracing.ALL_TRACES, key=lambda t: t.spans[0].duration_ms)
    print(slow_trace.waterfall())
    print()
    print("Notice: the log lines alone told you a payment was slow once.")
    print("The metrics told you requests kept flowing, on average, fine.")
    print("Only the trace shows you WHERE inside one request the time went.")

    out = dashboard.render(
        events=logging_.events(),
        registry_snapshot=registry.snapshot(),
        traces=tracing.ALL_TRACES,
        out_path="dashboard.html",
    )
    print()
    print("=" * 70)
    print(f"4) VISUAL — open {out} in a browser to see this run as a real dashboard")
    print("=" * 70)


if __name__ == "__main__":
    main()
