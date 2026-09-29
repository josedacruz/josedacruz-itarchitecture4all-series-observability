"""A fake checkout service: inventory check -> charge payment -> confirm
order. The same three-step flow shown in the video's sequence diagram.
Instrumented by hand with the obs/ package, on purpose — no metrics or
tracing library involved, so the mechanics stay visible.
"""
import random
import time

from obs.logging_ import info, warn
from obs.metrics import Registry
from obs.tracing import Trace

registry = Registry()
requests_total = registry.counter("checkout_requests_total")
requests_failed = registry.counter("checkout_requests_failed_total")
queue_size = registry.gauge("checkout_queue_size")


def checkout(order_id: str, *, simulate_slow_payment: bool = False) -> Trace:
    """Handle one checkout request and return its trace."""
    trace = Trace()
    queue_size.increment()
    requests_total.increment()
    info("checkout started", trace_id=trace.trace_id, order_id=order_id)

    with trace.start_span("checkout"):
        with trace.start_span("check_inventory"):
            info("checking inventory", trace_id=trace.trace_id, order_id=order_id)
            time.sleep(random.uniform(0.01, 0.03))

        with trace.start_span("charge_payment"):
            info("charging payment", trace_id=trace.trace_id, order_id=order_id)
            if simulate_slow_payment:
                # The incident from the video: the payment provider is
                # slow today. Nothing errors — it's just slow, which is
                # exactly the kind of problem a log line alone won't show.
                warn(
                    "payment provider responding slowly",
                    trace_id=trace.trace_id,
                    order_id=order_id,
                )
                time.sleep(random.uniform(0.25, 0.4))
            else:
                time.sleep(random.uniform(0.02, 0.05))

        with trace.start_span("confirm_order"):
            info("order confirmed", trace_id=trace.trace_id, order_id=order_id)
            time.sleep(random.uniform(0.005, 0.015))

    queue_size.decrement()
    info("checkout finished", trace_id=trace.trace_id, order_id=order_id)
    return trace
