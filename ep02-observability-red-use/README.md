# RED vs USE — a runnable demo

Companion code for the video *"RED vs USE Metrics: Why a Healthy Dashboard
Missed a Dying Service"* No dependencies beyond the Python standard library.

## What it is

A simulated image-resize worker (`worker.py`) with a simulated memory
leak, instrumented two ways at once. Nothing here allocates real memory
— the leak is a small model, so the demo is safe and gives the same
numbers on every machine. The instrumentation in `obs/` is the real
part: the same `record()` / `sample()` calls you would put around a real
request and a real resource.

- **`obs/red.py`** — RED (Tom Wilkie, Weaveworks, 2015): Rate, Errors,
  Duration. Measures from the *caller's* side.
- **`obs/use.py`** — USE (Brendan Gregg): Utilization, Saturation,
  Errors. Measures from the *resource's* side — "for every resource,
  check utilization, saturation, and errors."

The leak: every job holds on to a little more memory than it frees.
Requests keep succeeding — right up until the process runs out of
memory and the 30th job is killed outright.

## Run it

```
python run_demo.py
open dashboard.html
```

`run_demo.py` runs 30 jobs and prints, job by job, what each method saw
— the caller's view (ok / FAILED, duration) next to the resource's view
(memory %, queued work, resource errors). Then it prints both summaries
and writes **`dashboard.html`**, a self-contained page with:

- RED's and USE's numbers side by side, plus a per-job strip for each
- both methods on one chart, with the stretch where USE was already
  warning and RED still showed 0% shaded
- "who knew when": the job where USE first showed queued work, the job
  where RED first showed an error, and the gap between them

No server, no dependencies — just open the file.

## Things to try

- Change the leak rate in `worker.py` (`_memory_pct`) and re-run: the
  warning window grows or shrinks, but RED still moves last.
- Compare `avg_duration_ms` with `avg_success_ms` in the RED summary.
  The killed job fails in a few milliseconds, so the average over *all*
  requests is lower than the average over successes — a failing service
  can look faster.

## The point

RED and USE aren't competing standards. They watch different sides of
the same system, and a service can look perfectly healthy on one side
while already failing on the other. This is the actual example from the
video: a service with perfect RED numbers, seconds from an OOM kill,
visible only in USE.

## Layout

```
project/
  obs/
    red.py        RED: Rate, Errors, Duration
    use.py         USE: Utilization, Saturation, Errors
    dashboard.py   renders dashboard.html from the run's data
  worker.py        the leaking image-resize worker
  run_demo.py      runs it, prints both summaries, writes dashboard.html
```
