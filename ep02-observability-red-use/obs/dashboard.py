"""Renders one self-contained dashboard.html from a run's data — no
server, no dependencies, no network: open the file in a browser.

Same visual language as the ep01 project (series/observability/CLAUDE.md's
"signal dashboard" system) so this reads as the same show, filled with
this episode's own data: RED and USE over the same 30 jobs, job by job,
so you can see directly where one method warned and the other didn't.
"""
from pathlib import Path

CSS = """
:root{--bg:#f7f1f6;--panel:#fff;--ink:#241a26;--ink-2:#4a3a48;--muted:#7d6b7f;--line:#e2d0df;
--accent:#a3238e;--accent-soft:#f0dcec;--red:#4b5a8f;--red-soft:#dfe3f3;--use:#0f766e;--use-soft:#d5efec;
--bad:#b91c1c;--bad-soft:#fee2e2;--good:#15803d;--good-soft:#dcfce7;--warn:#a16207;--warn-soft:#f7ecc9;}
*{box-sizing:border-box} body{margin:0;background:var(--bg);color:var(--ink);
font-family:'Segoe UI',Inter,system-ui,Arial,sans-serif;
background-image:radial-gradient(circle,rgba(163,35,142,.14) 1.2px,transparent 1.2px);background-size:26px 26px;}
header{padding:20px 36px;border-bottom:3px solid var(--accent);background:#fff;display:flex;align-items:center;gap:14px;}
header .dot{width:10px;height:10px;border-radius:50%;background:var(--accent);}
header b{font-family:Consolas,monospace;letter-spacing:.04em;}
header span.sub{color:var(--muted);font-family:Consolas,monospace;font-size:13px;}
main{padding:24px 36px 48px;display:grid;grid-template-columns:1fr 1fr;gap:20px;max-width:1400px;margin:0 auto;}
.wide{grid-column:1/-1;}
.widget{background:var(--panel);border:1px solid var(--line);border-radius:10px;overflow:hidden;}
.widget h2{margin:0;padding:10px 18px;border-bottom:1px solid var(--line);background:#fbf6fa;
font-family:Consolas,monospace;font-size:13px;text-transform:uppercase;letter-spacing:.08em;display:flex;align-items:center;gap:10px;}
.widget h2 .dot{width:8px;height:8px;border-radius:50%;}
.widget h2 .sub{font-weight:400;color:var(--muted);text-transform:none;letter-spacing:0;}
.red-dot{background:var(--red)} .use-dot{background:var(--use)} .accent-dot{background:var(--accent)}
.widget .body{padding:16px 20px 18px;}
.stat-row{display:flex;gap:14px;}
.stat{flex:1;min-width:0;background:#fbf6fa;border:1px solid var(--line);border-radius:8px;padding:10px 10px;text-align:center;}
.stat .n{font-family:Consolas,monospace;font-weight:800;font-size:clamp(17px,2vw,27px);}
.stat.ok .n{color:var(--good)} .stat.warn .n{color:var(--bad)} .stat.neutral .n{color:var(--ink)}
.stat .l{font-size:10.5px;text-transform:uppercase;letter-spacing:.04em;color:var(--muted);margin-top:4px;line-height:1.3;}
.strip-label{font-family:Consolas,monospace;font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);margin:16px 0 6px;}
.strip{display:grid;grid-template-columns:repeat(30,1fr);gap:3px;}
.strip div{height:30px;border-radius:3px;font-family:Consolas,monospace;font-size:9px;display:flex;align-items:center;justify-content:center;color:#fff;}
.annot{font-size:14px;color:var(--ink-2);line-height:1.5;margin-top:10px;}
.verdict{margin-top:14px;padding:11px 16px;border-radius:8px;font-size:14.5px;font-weight:700;text-align:center;}
.verdict.ok{background:var(--good-soft);color:var(--good);} .verdict.warn{background:var(--bad-soft);color:var(--bad);}
.chart svg{display:block;width:100%;height:auto;}
.lead{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;}
.lead .stat .n{font-size:24px}
"""


def _chart(history, first_queued, oom_at_job, width=1240, height=380):
    pad_l, pad_r, pad_t, pad_b = 56, 96, 34, 42
    n = len(history)
    dx = (width - pad_l - pad_r) / max(1, n - 1)

    def x(job):
        return pad_l + (job - 1) * dx

    def y(v):
        return height - pad_b - (min(v, 100) / 100) * (height - pad_t - pad_b)

    out = ""
    for frac in (0, 0.25, 0.5, 0.75, 1):
        yy = height - pad_b - frac * (height - pad_t - pad_b)
        out += f'<line x1="{pad_l}" y1="{yy:.1f}" x2="{width - pad_r}" y2="{yy:.1f}" stroke="#e2d0df"/>'
        out += f'<text x="{pad_l - 8}" y="{yy + 4:.1f}" font-size="12" fill="#7d6b7f" text-anchor="end">{100 * frac:.0f}%</text>'
    for job in (1, 5, 10, 15, 20, 25, 30):
        if job <= n:
            out += f'<text x="{x(job):.1f}" y="{height - pad_b + 20}" font-size="12" fill="#7d6b7f" text-anchor="middle">job {job}</text>'
    if first_queued:
        out += (f'<rect x="{x(first_queued):.1f}" y="{pad_t}" width="{x(oom_at_job) - x(first_queued):.1f}" '
                f'height="{height - pad_t - pad_b}" fill="#fee2e2" opacity=".55"/>'
                f'<text x="{(x(first_queued) + x(oom_at_job)) / 2:.1f}" y="{pad_t - 10}" font-size="13" font-weight="700" '
                f'fill="#b91c1c" text-anchor="middle">{oom_at_job - first_queued} jobs of warning RED never showed</text>')
    red_pts = " ".join(f"{x(h[0]):.1f},{y(h[1]):.1f}" for h in history)
    use_pts = " ".join(f"{x(h[0]):.1f},{y(h[2]):.1f}" for h in history)
    out += f'<polyline points="{red_pts}" fill="none" stroke="#4b5a8f" stroke-width="3.5" stroke-linejoin="round" stroke-linecap="round"/>'
    out += f'<polyline points="{use_pts}" fill="none" stroke="#0f766e" stroke-width="3.5" stroke-linejoin="round" stroke-linecap="round"/>'
    last = history[-1]
    out += f'<circle cx="{x(last[0]):.1f}" cy="{y(last[1]):.1f}" r="6" fill="#b91c1c"/>'
    out += f'<text x="{x(last[0]) + 12:.1f}" y="{y(last[2]) + 5:.1f}" font-size="14" font-weight="700" fill="#0f766e">{last[2]}%</text>'
    out += f'<text x="{x(last[0]) + 12:.1f}" y="{y(last[1]) + 5:.1f}" font-size="14" font-weight="700" fill="#b91c1c">{last[1]}%</text>'
    # label sits above the highest point of the stretch of line it spans
    label_y = y(max(h[2] for h in history[:9])) - 14
    out += f'<text x="{x(2):.1f}" y="{label_y:.1f}" font-size="14" font-weight="700" fill="#0f766e">USE: memory utilization</text>'
    out += f'<text x="{x(2):.1f}" y="{y(0) - 12:.1f}" font-size="14" font-weight="700" fill="#4b5a8f">RED: error rate</text>'
    return (f'<svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" '
            f'font-family="Consolas,monospace">{out}</svg>')


def _mem_color(mem):
    if mem >= 90:
        return "#b91c1c"
    if mem >= 80:
        return "#a16207"
    return "#0f766e"


def render(*, red, use, history, oom_at_job, out_path):
    """red: RedMetrics; use: UseMetrics; history: list of (job_i, red_error_rate_pct, mem_pct, saturation)."""
    first_queued = next((h[0] for h in history if h[3] > 0), None)
    first_res_err = use.error_ticks[0] if use.error_ticks else None
    first_red_err = next((h[0] for h in history if h[1] > 0), None)
    lead = (first_red_err - first_queued) if (first_red_err and first_queued) else None

    red_stats = (
        f'<div class="stat neutral"><div class="n">{red.requests}</div><div class="l">requests</div></div>'
        f'<div class="stat {"warn" if red.errors else "ok"}"><div class="n">{red.error_rate_pct}%</div><div class="l">error rate</div></div>'
        f'<div class="stat neutral"><div class="n">{red.avg_duration_ms}</div><div class="l">avg ms, all requests</div></div>'
        f'<div class="stat neutral"><div class="n">{red.avg_success_duration_ms}</div><div class="l">avg ms, successes only</div></div>'
    )
    use_stats = (
        f'<div class="stat {"warn" if use.current_utilization_pct >= 90 else "ok"}"><div class="n">{use.current_utilization_pct}%</div><div class="l">memory utilization</div></div>'
        f'<div class="stat {"warn" if use.current_saturation else "ok"}"><div class="n">{use.current_saturation}</div><div class="l">saturation (queued)</div></div>'
        f'<div class="stat {"warn" if use.errors else "ok"}"><div class="n">{use.errors}</div><div class="l">resource errors</div></div>'
    )
    caller_strip = "".join(
        f'<div title="job {i + 1}: {ms} ms" style="background:{"#b91c1c" if bad else "#15803d"}">{"x" if bad else ""}</div>'
        for i, (ms, bad) in enumerate(zip(red.durations_ms, red.failed)))
    mem_strip = "".join(
        f'<div title="job {h[0]}: {h[2]}% memory, {h[3]} queued" style="background:{_mem_color(h[2])};opacity:{0.35 + 0.65 * h[2] / 100:.2f}">{h[3] or ""}</div>'
        for h in history)

    pre_err = history[oom_at_job - 2][1] if oom_at_job >= 2 else 0.0
    pre_util = history[oom_at_job - 2][2] if oom_at_job >= 2 else 0.0

    def lead_stat(value, label, cls):
        return f'<div class="stat {cls}"><div class="n">{value if value is not None else "-"}</div><div class="l">{label}</div></div>'

    body = f"""<!doctype html><html><head><meta charset="utf-8"><title>RED vs USE — your run</title>
<style>{CSS}</style></head><body>
<header><span class="dot"></span><b>RED VS USE</b><span class="sub">/ your own run, {len(history)} jobs</span></header>
<main>
  <div class="widget"><h2><span class="dot red-dot"></span>RED <span class="sub">the caller's side</span></h2>
    <div class="body"><div class="stat-row">{red_stats}</div>
    <div class="strip-label">every job, as the caller saw it (green = ok, red = failed)</div>
    <div class="strip">{caller_strip}</div>
    <div class="verdict ok">Through job {oom_at_job - 1}: {pre_err}% errors &mdash; completely clean.</div></div></div>

  <div class="widget"><h2><span class="dot use-dot"></span>USE <span class="sub">the resource's side</span></h2>
    <div class="body"><div class="stat-row">{use_stats}</div>
    <div class="strip-label">every job, as the resource saw it (darker = fuller memory, number = jobs queued)</div>
    <div class="strip">{mem_strip}</div>
    <div class="verdict warn">By job {oom_at_job - 1}: {pre_util}% memory &mdash; already past any sane alert threshold.</div></div></div>

  <div class="widget wide"><h2><span class="dot accent-dot"></span>BOTH, OVER TIME <span class="sub">RED's error rate vs USE's utilization, same {len(history)} jobs</span></h2>
    <div class="body chart">{_chart(history, first_queued, oom_at_job)}</div></div>

  <div class="widget wide"><h2><span class="dot accent-dot"></span>WHO KNEW WHEN</h2>
    <div class="body"><div class="lead">
      {lead_stat(f"job {first_queued}" if first_queued else None, "USE: first queued work", "warn")}
      {lead_stat(f"job {first_res_err}" if first_res_err else None, "USE: first resource error", "warn")}
      {lead_stat(f"job {first_red_err}" if first_red_err else None, "RED: first error", "warn")}
      {lead_stat(f"{lead} jobs" if lead is not None else None, "warning USE gave before RED moved", "neutral")}
    </div>
    <div class="annot">RED and USE aren't competing standards. RED watches the requests crossing the service's door; USE watches the resources working inside. A service can look perfectly healthy from one side while already failing on the other &mdash; so check both.</div></div></div>
</main></body></html>"""
    Path(out_path).write_text(body, encoding="utf-8")
    return out_path
