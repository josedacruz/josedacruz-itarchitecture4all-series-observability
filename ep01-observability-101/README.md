# Observability 101 — a runnable demo

Companion code for the video *"Observability 101: Logs, Metrics, and
Traces."* No dependencies beyond the Python standard library — clone it,
run it, and see the same incident from the video reproduced on your own
machine, three ways.

## What it is

A tiny, fake "checkout service" (`store.py`) that handles a request in
three steps — check inventory, charge payment, confirm order — the same
flow shown in the video's sequence diagram. Every request is instrumented
by hand, with no metrics/tracing library involved, so the mechanics stay
visible instead of hidden behind a framework:

- **`obs/logging_.py`** — a structured JSON logger. Every log line is a
  real JSON object with a `trace_id`, not a free-text sentence, so it can
  be filtered by request later.
- **`obs/metrics.py`** — a `Counter` and a `Gauge`, implemented from
  scratch in about 30 lines, mirroring what a real metrics library (like
  Micrometer) gives you: something that only goes up, and something that
  reports whatever the value is right now.
- **`obs/tracing.py`** — a minimal `Span`/`start_span` context manager
  that records a name, a start time, an end time, and a parent span id,
  and can render itself as an ASCII waterfall — the same shape a real
  tracing backend draws, just printed to your terminal instead.

## Run it

```
python run_demo.py
open dashboard.html
```

`run_demo.py` fires 20 requests through the checkout service. One in
five is artificially slow (the "incident" from the video). In the
terminal you'll see:

1. its structured log lines, as they happen;
2. the live metrics snapshot after all 20 requests (a counter and a
   gauge);
3. one full trace, printed as a waterfall, for the slowest request in
   the batch — the same incident, now explained by its trace.

Then it writes **`dashboard.html`** — a real, self-contained visual view
of that same run (no server, no dependencies, just open the file):
your own logs, a live chart of your own machine's real latencies, the
slowest trace as a colored waterfall, and a correlation panel that
highlights the one `trace_id` shared across all three. It's the same
widget style as the video, filled with your own data instead of the
video's.

## Why it's built this way

The point isn't to reinvent Prometheus or Jaeger — it's to make the
three pillars concrete before reaching for a real tool. Later episodes
in the [Micrometer series](../../micrometer/) wire this exact shape up
to Prometheus and Grafana for real; this project is deliberately small
enough to read start to finish in a few minutes.

## Layout

```
project/
  obs/
    logging_.py   structured JSON logger (also keeps events in memory)
    metrics.py    Counter + Gauge
    tracing.py    Span + Trace, incl. to_dict() for the dashboard
    dashboard.py  renders dashboard.html from a real run's data
  store.py        the fake checkout service (inventory -> payment -> confirm)
  run_demo.py     fires requests, prints logs/metrics/trace, writes dashboard.html
```
