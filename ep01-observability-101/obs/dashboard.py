"""Renders one self-contained dashboard.html from a real run's data — no
server, no dependencies, no network: open the file in a browser.

It deliberately mirrors the video's own visual language (the same
widget/status-dot/mono-label look from series/observability/CLAUDE.md)
so what you see here is recognizably "the same dashboard, now running on
your own machine, on your own data" — not a different-looking demo.

Panels: logs, metrics, the fastest trace and the slowest trace shown as
their own trees (so you can compare a clean request against the
incident, span by span), plus a correlation panel that is the actual
point of this project: the SAME trace_id highlighted across logs and
the slow trace, because that shared id is the entire correlation
mechanism.
"""
import html
import json
from pathlib import Path

CSS = """
:root{--bg:#f7f1f6;--panel:#fff;--ink:#241a26;--ink-2:#4a3a48;--muted:#7d6b7f;--line:#e2d0df;
--accent:#a3238e;--accent-soft:#f0dcec;--logs:#4b5a8f;--metrics:#0f766e;--traces:#a16207;--bad:#b91c1c;}
*{box-sizing:border-box} body{margin:0;background:var(--bg);color:var(--ink);
font-family:'Segoe UI',Inter,system-ui,Arial,sans-serif;
background-image:radial-gradient(circle,rgba(163,35,142,.14) 1.2px,transparent 1.2px);background-size:26px 26px;}
header{padding:22px 36px;border-bottom:3px solid var(--accent);background:#fff;display:flex;align-items:center;gap:14px;}
header .dot{width:10px;height:10px;border-radius:50%;background:var(--accent);}
header b{font-family:Consolas,monospace;letter-spacing:.04em;}
header span.sub{color:var(--muted);font-family:Consolas,monospace;font-size:13px;}
main{padding:28px 36px 60px;display:grid;grid-template-columns:1.3fr 1fr;gap:22px;max-width:1400px;margin:0 auto;}
.wide{grid-column:1/-1;}
.widget{background:var(--panel);border:1px solid var(--line);border-radius:10px;overflow:hidden;}
.widget h2{margin:0;padding:10px 18px;border-bottom:1px solid var(--line);background:#fbf6fa;
font-family:Consolas,monospace;font-size:13px;text-transform:uppercase;letter-spacing:.08em;display:flex;align-items:center;gap:10px;}
.widget h2 .dot{width:8px;height:8px;border-radius:50%;}
.logs-dot{background:var(--logs)} .metrics-dot{background:var(--metrics)} .traces-dot{background:var(--traces)} .accent-dot{background:var(--accent)}
.widget .body{padding:18px 20px;}
.term{background:#221a20;color:#d8d0e0;border-radius:8px;padding:14px 16px;font-family:Consolas,monospace;
font-size:13px;line-height:1.7;max-height:360px;overflow-y:auto;}
.term .row{white-space:pre-wrap;word-break:break-all;}
.term .lvl-INFO{color:#7ea6f5} .term .lvl-WARN{color:#e5b95a;font-weight:700} .term .lvl-ERROR{color:#e5605a;font-weight:700}
.term .k{color:#f0a6e0} .term .v{color:#8fe3c9}
.term .row.hl{background:rgba(163,35,142,.28);border-radius:4px;}
.stat-row{display:flex;gap:16px;margin-bottom:14px;}
.stat{flex:1;min-width:0;background:#fbf6fa;border:1px solid var(--line);border-radius:8px;padding:10px 10px;text-align:center;}
.stat .n{font-family:Consolas,monospace;font-weight:800;font-size:24px;color:var(--metrics);}
.stat .l{font-size:10px;text-transform:uppercase;letter-spacing:.04em;color:var(--muted);margin-top:2px;word-break:break-word;line-height:1.3;}
.dur-row{display:flex;align-items:center;gap:10px;margin:7px 0;font-family:Consolas,monospace;font-size:13px;}
.dur-row .dn{width:150px;text-align:right;color:var(--ink-2);flex-shrink:0;}
.dur-track{flex:1;height:18px;background:#f1e6ef;border-radius:4px;position:relative;overflow:hidden;}
.dur-bar{position:absolute;top:0;bottom:0;border-radius:4px;}
.dur-row .dv{width:70px;color:var(--muted);font-size:12px;}
.corr-id{font-family:Consolas,monospace;background:var(--accent-soft);color:var(--accent);padding:2px 8px;border-radius:4px;font-weight:700;}
.annot{font-size:14px;color:var(--ink-2);line-height:1.5;margin-top:10px;}
"""


def _log_rows(events, highlight_trace_id):
    rows = []
    for e in events:
        cls = "hl" if e.get("trace_id") == highlight_trace_id else ""
        parts = "".join(
            f'<span class="k">{html.escape(str(k))}</span>=<span class="v">{html.escape(str(v))}</span> '
            for k, v in e.items() if k not in ("level", "msg")
        )
        rows.append(
            f'<div class="row {cls}"><span class="lvl-{e["level"]}">{e["level"]:<5}</span> '
            f'{html.escape(e["msg"])}  {parts}</div>'
        )
    return "\n".join(rows)


def _svg_chart(values, width=560, height=200, color="var(--metrics)"):
    if not values:
        return ""
    pad = 30
    vmax = max(max(values) * 1.1, 1)
    n = len(values)
    dx = (width - pad * 2) / max(1, n - 1)

    def y(v):
        return height - pad - (v / vmax) * (height - pad * 2)

    pts = " ".join(f"{pad + i * dx:.1f},{y(v):.1f}" for i, v in enumerate(values))
    ticks = ""
    for frac in (0, 0.5, 1):
        yy = height - pad - frac * (height - pad * 2)
        ticks += f'<line x1="{pad}" y1="{yy:.1f}" x2="{width - pad}" y2="{yy:.1f}" stroke="#e2d0df" stroke-width="1"/>'
        ticks += f'<text x="{pad - 8}" y="{yy + 4:.1f}" font-size="10" fill="#7d6b7f" text-anchor="end">{vmax * frac:.0f}</text>'
    return (
        f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" '
        f'xmlns="http://www.w3.org/2000/svg" font-family="Consolas,monospace">{ticks}'
        f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="2.5" '
        f'stroke-linejoin="round" stroke-linecap="round"/></svg>'
    )


def _waterfall(trace_dict, highlight=False):
    total = max(trace_dict["total_ms"], 0.1)
    colors = {0: "var(--accent)"}
    palette = ["var(--logs)", "var(--traces)", "var(--metrics)"]
    rows = []
    for i, s in enumerate(trace_dict["spans"]):
        color = "var(--accent)" if i == 0 else palette[(i - 1) % len(palette)]
        left = s["offset_ms"] / total * 100
        width = max(0.6, s["duration_ms"] / total * 100)
        rows.append(
            f'<div class="dur-row"><span class="dn">{"&nbsp;&nbsp;" * s["depth"]}{html.escape(s["name"])}</span>'
            f'<div class="dur-track"><div class="dur-bar" style="left:{left:.1f}%;width:{width:.1f}%;background:{color}"></div></div>'
            f'<span class="dv">{s["duration_ms"]} ms</span></div>'
        )
    return "\n".join(rows)


def render(*, events, registry_snapshot, traces, out_path):
    """events: obs.logging_.events(); registry_snapshot: Registry.snapshot();
    traces: list[Trace] (e.g. obs.tracing.ALL_TRACES)."""
    slow_trace = max(traces, key=lambda t: t.spans[0].duration_ms)
    fast_trace = min(traces, key=lambda t: t.spans[0].duration_ms)
    slow_dict = slow_trace.to_dict()
    fast_dict = fast_trace.to_dict()
    highlight_id = slow_trace.trace_id

    latencies = [t.spans[0].duration_ms for t in traces]
    chart = _svg_chart(latencies)

    stats = "".join(
        f'<div class="stat"><div class="n">{v}</div><div class="l">{html.escape(k)}</div></div>'
        for k, v in registry_snapshot.items()
    )

    body = f"""<!doctype html><html><head><meta charset="utf-8"><title>Observability 101 — live run</title>
<style>{CSS}</style></head><body>
<header><span class="dot"></span><b>OBSERVABILITY 101</b><span class="sub">/ your own run, {len(traces)} requests</span></header>
<main>
  <div class="widget"><h2><span class="dot logs-dot"></span>LOGS <span style="font-weight:400;color:var(--muted);margin-left:8px">obs/logging_.py, {len(events)} events</span></h2>
    <div class="body"><div class="term">{_log_rows(events, highlight_id)}</div>
    <div class="annot">Every line above is a real structured JSON event, not a formatted string — filter it by <span class="corr-id">trace_id</span> and you get exactly one request's story.</div></div></div>

  <div class="widget"><h2><span class="dot metrics-dot"></span>METRICS <span style="font-weight:400;color:var(--muted);margin-left:8px">real latencies, this run</span></h2>
    <div class="body"><div class="stat-row">{stats}</div>{chart}
    <div class="annot">One in five requests spikes — the same pattern the video's seeded chart shows, now from your own machine's real timing.</div></div></div>

  <div class="widget"><h2><span class="dot traces-dot"></span>FASTEST TRACE <span style="font-weight:400;color:var(--muted);margin-left:8px">{fast_dict['total_ms']} ms &middot; trace <span class="corr-id">{fast_trace.trace_id}</span></span></h2>
    <div class="body">{_waterfall(fast_dict)}
    <div class="annot">The tree above is every span this request produced, in order &mdash; even the fastest request still has to walk all three steps.</div></div></div>

  <div class="widget"><h2><span class="dot traces-dot"></span>SLOWEST TRACE <span style="font-weight:400;color:var(--muted);margin-left:8px">{slow_dict['total_ms']} ms &middot; trace <span class="corr-id">{highlight_id}</span></span></h2>
    <div class="body">{_waterfall(slow_dict)}
    <div class="annot">Same tree shape, same three steps &mdash; but one span, <b>charge_payment</b>, is doing almost all the work. That's the incident.</div></div></div>

  <div class="widget wide"><h2><span class="dot accent-dot"></span>CORRELATION <span style="font-weight:400;color:var(--muted);margin-left:8px">how the three panels above connect</span></h2>
    <div class="body"><div class="annot" style="margin-top:0;font-size:15px">
      Every log line for the slow request above is tagged <span class="corr-id">{highlight_id}</span> — the same id labels its trace, and in a real backend (Prometheus exemplars, for example) it would tag the exact metric point that spiked too. One id, three pillars, one incident. That's correlation — not a feature you buy, just a field you propagate everywhere.
    </div></div></div>
</main></body></html>"""
    Path(out_path).write_text(body, encoding="utf-8")
    return out_path
