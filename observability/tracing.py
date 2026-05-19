from __future__ import annotations

import logging

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

logger = logging.getLogger(__name__)


def configure_tracing(endpoint: str, service_name: str) -> None:
    """Wire up the global OTel TracerProvider with OTLP/gRPC export to Jaeger.

    Safe to call even when Jaeger is unreachable — BatchSpanProcessor retries
    silently so the API never crashes on exporter failures.
    """
    resource = Resource.create({"service.name": service_name})
    provider = TracerProvider(resource=resource)
    provider.add_span_processor(
        BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint, insecure=True))
    )
    trace.set_tracer_provider(provider)
    logger.info("OTel tracing configured → %s (service=%s)", endpoint, service_name)
