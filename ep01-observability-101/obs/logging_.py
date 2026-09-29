"""A minimal structured logger.

Every log line is a real JSON object, not a sentence — so it can be
filtered by field later (by trace_id, by level, by service), instead of
grepped by hoping the right words are in there. That's the whole
difference between a log statement and a structured log event.

Also keeps every event in memory (EVENTS) so dashboard.py can render
them after the run — a stand-in for what a real log shipper does by
forwarding them to a backend instead.
"""
import json
import sys
import time

EVENTS = []


def log(level: str, msg: str, /, **fields):
    """Emit one structured log line to stdout, and remember it.

    `fields` is where the context goes — trace_id, span_id, a service
    name, an order id. Keeping them as separate JSON fields (not baked
    into `msg`) is what makes "show me every log line for this one
    request" a filter instead of a guess. Never put a secret or a full
    credit-card number in a field here — logs are usually the least
    access-controlled, longest-retained pillar, which is exactly why
    that's a real production mistake, not a theoretical one.
    """
    event = {
        "ts": round(time.time(), 3),
        "level": level,
        "msg": msg,
        **fields,
    }
    EVENTS.append(event)
    print(json.dumps(event), file=sys.stdout)


def info(msg: str, /, **fields):
    log("INFO", msg, **fields)


def warn(msg: str, /, **fields):
    log("WARN", msg, **fields)


def error(msg: str, /, **fields):
    log("ERROR", msg, **fields)


def events():
    return list(EVENTS)
