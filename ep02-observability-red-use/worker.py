"""A simulated image-resize worker with a simulated memory leak,
instrumented two ways at once — RED (the caller's side) and USE (the
resource's side) — so you can watch the two methods disagree, job by job.

Nothing here allocates real memory: the leak is a model (memory climbs a
little every job, see _memory_pct) so the demo is safe and repeatable on
any machine. The instrumentation in obs/ is the real part — the same
record()/sample() calls you would make around a real request and a real
resource.

The leak: every job holds on to a little more memory than it frees.
Requests keep succeeding, right up until the process runs out of memory
and the 30th job is killed outright.
"""
import random
import time

from obs.red import RedMetrics
from obs.use import UseMetrics

TOTAL_JOBS = 30
OOM_AT_JOB = 30  # the job that gets killed when memory finally runs out

random.seed(42)

red = RedMetrics()
use = UseMetrics()
history = []  # one row per job: (job_i, red_error_rate_pct_so_far, mem_pct, saturation)


def _memory_pct(job_i: int) -> float:
    # climbs steadily — the actual leak. Nothing in RED can see this.
    base = 36 + job_i * 2.05
    return round(min(99.5, base + random.uniform(-1.5, 1.5)), 1)


def _saturation(job_i: int, mem_pct: float) -> int:
    # once memory pressure is high enough, the allocator starts stalling
    # and work queues up behind it — this is what "saturation" means.
    if mem_pct < 80:
        return 0
    return round((mem_pct - 80) * 0.9)


def run():
    for i in range(1, TOTAL_JOBS + 1):
        mem_pct = _memory_pct(i)
        sat = _saturation(i, mem_pct)
        gc_retry = mem_pct >= 92  # a resource-level error: an allocation had to retry

        if i == OOM_AT_JOB:
            # the request itself fails — fast, since the process is killed,
            # not slow. RED's duration metric gives no warning here either.
            duration_ms = round(random.uniform(3, 8), 1)
            time.sleep(duration_ms / 2000)
            red.record(duration_ms, error=True)
            use.sample(mem_pct, sat, error=True)
        else:
            duration_ms = round(random.uniform(90, 130), 1)
            time.sleep(duration_ms / 2000)
            red.record(duration_ms, error=False)
            use.sample(mem_pct, sat, error=gc_retry)

        history.append((i, red.error_rate_pct, mem_pct, sat))

    return red, use, history


if __name__ == "__main__":
    run()
    print("RED:", red.snapshot())
    print("USE:", use.snapshot())
    print(f"RED error rate through job {OOM_AT_JOB - 1}: 0.0% -- zero warning.")
    print(f"USE utilization at job {OOM_AT_JOB - 1}: {history[-2][2]}% -- already past any sane threshold.")
