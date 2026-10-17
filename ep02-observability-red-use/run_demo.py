"""Runs the leaking image-resize worker for 30 jobs, instrumented both
ways at once — RED and USE — prints what each method saw job by job,
then both summaries, then writes a visual dashboard.html comparing them
over time.

Usage:
    python run_demo.py
"""
from obs import dashboard
from worker import OOM_AT_JOB, run


def main():
    red, use, history = run()

    print("job   RED: caller saw        USE: resource saw")
    print("---   --------------------   ------------------------------------")
    for (job, _err_pct, mem, sat), ms, failed in zip(history, red.durations_ms, red.failed):
        caller = f"{'FAILED' if failed else 'ok':<6} {ms:>6.1f} ms"
        if failed:
            event = "OOM kill"
        elif job in use.error_ticks:
            event = "allocation retry"
        else:
            event = ""
        print(f"{job:>3}   {caller:<20}   mem {mem:>5.1f}%  queued {sat:>2}  {event}")

    print()
    print("=" * 70)
    print("RED (the caller's side)")
    print("=" * 70)
    for k, v in red.snapshot().items():
        print(f"  {k:<16} {v}")

    print()
    print("=" * 70)
    print("USE (the resource's side)")
    print("=" * 70)
    for k, v in use.snapshot().items():
        print(f"  {k:<16} {v}")

    pre = history[OOM_AT_JOB - 2]
    first_queued = next((h[0] for h in history if h[3] > 0), None)
    print()
    print("=" * 70)
    print(f"Through job {OOM_AT_JOB - 1}: RED error rate was {pre[1]}% -- zero warning.")
    print(f"Through job {OOM_AT_JOB - 1}: USE memory utilization was already {pre[2]}%.")
    if first_queued:
        print(f"USE first showed queued work at job {first_queued} -- "
              f"{OOM_AT_JOB - first_queued} jobs before the kill.")
    print("=" * 70)

    out = dashboard.render(red=red, use=use, history=history, oom_at_job=OOM_AT_JOB, out_path="dashboard.html")
    print()
    print(f"Open {out} in a browser to see both methods, side by side, over time.")


if __name__ == "__main__":
    main()
