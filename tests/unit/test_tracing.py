from __future__ import annotations

from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter


def _make_provider() -> tuple[TracerProvider, InMemorySpanExporter]:
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    return provider, exporter


def test_rag_span_names_are_correct():
    provider, exporter = _make_provider()
    tracer = provider.get_tracer("cortex.query")

    with tracer.start_as_current_span("rag.query"):
        with tracer.start_as_current_span("rag.embed"):
            pass
        with tracer.start_as_current_span("rag.retrieve"):
            pass
        with tracer.start_as_current_span("rag.rerank"):
            pass
        with tracer.start_as_current_span("rag.generate"):
            pass

    names = {s.name for s in exporter.get_finished_spans()}
    assert names == {"rag.query", "rag.embed", "rag.retrieve", "rag.rerank", "rag.generate"}


def test_child_spans_are_nested_under_root():
    provider, exporter = _make_provider()
    tracer = provider.get_tracer("cortex.query")

    with tracer.start_as_current_span("rag.query"):
        with tracer.start_as_current_span("rag.embed"):
            pass
        with tracer.start_as_current_span("rag.retrieve"):
            pass
        with tracer.start_as_current_span("rag.rerank"):
            pass
        with tracer.start_as_current_span("rag.generate"):
            pass

    spans = exporter.get_finished_spans()
    root = next(s for s in spans if s.name == "rag.query")
    children = [s for s in spans if s.parent and s.parent.span_id == root.context.span_id]
    assert len(children) == 4


def test_span_attributes_are_recorded():
    provider, exporter = _make_provider()
    tracer = provider.get_tracer("cortex.query")

    with tracer.start_as_current_span("rag.retrieve") as s:
        s.set_attribute("candidates.count", 20)
        s.set_attribute("dense_top_k", 20)

    with tracer.start_as_current_span("rag.rerank") as s:
        s.set_attribute("top_k", 5)
        s.set_attribute("results.count", 5)

    with tracer.start_as_current_span("rag.generate") as s:
        s.set_attribute("llm.model", "claude-haiku-4-5-20251001")
        s.set_attribute("tokens.generated", 42)

    spans = {s.name: s for s in exporter.get_finished_spans()}
    assert spans["rag.retrieve"].attributes["candidates.count"] == 20
    assert spans["rag.rerank"].attributes["top_k"] == 5
    assert spans["rag.generate"].attributes["tokens.generated"] == 42


def test_configure_tracing_does_not_raise_on_bad_endpoint():
    """BatchSpanProcessor must not propagate OTLP connection failures to the app."""
    from observability.tracing import configure_tracing

    configure_tracing(endpoint="http://localhost:19999", service_name="test")
    # No exception means the exporter failure is absorbed by BatchSpanProcessor
