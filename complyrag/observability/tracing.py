"""OpenTelemetry tracing.

Every agent step runs inside a span carrying the obligation id, so a slow or
failing assessment can be followed step by step in Jaeger, Grafana Tempo or
Azure Monitor. With the exporter set to "none" spans are created but dropped.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from functools import wraps

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

log = logging.getLogger(__name__)
_configured = False


def setup_tracing(exporter: str = "none", service_name: str = "complyrag") -> None:
    global _configured
    if _configured:
        return
    provider = TracerProvider(resource=Resource.create({"service.name": service_name}))
    if exporter == "console":
        provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
    elif exporter == "otlp":
        try:
            from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        except ImportError:  # pragma: no cover - optional extra
            log.warning("OTLP exporter not installed; pip install '.[otlp]'")
        else:
            provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
    trace.set_tracer_provider(provider)
    _configured = True


tracer = trace.get_tracer("complyrag")


def traced(name: str) -> Callable:
    """Decorator for LangGraph nodes: one span per node call."""

    def decorator(fn: Callable) -> Callable:
        @wraps(fn)
        def wrapper(state, *args, **kwargs):
            with tracer.start_as_current_span(name) as span:
                obligation = state.get("obligation") if isinstance(state, dict) else None
                if obligation is not None:
                    span.set_attribute("complyrag.obligation", obligation.id)
                return fn(state, *args, **kwargs)

        return wrapper

    return decorator
