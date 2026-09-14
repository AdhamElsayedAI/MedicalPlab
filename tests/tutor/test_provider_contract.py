"""Tests for GenerativeProvider protocol and adapter contracts."""
from __future__ import annotations

import pytest
from medicalplab.tutor.provider import (
    GenerativeProvider,
    ProviderResponse,
    StubGenerativeProvider,
    get_default_provider,
)


def test_stub_provider_implements_protocol():
    stub = StubGenerativeProvider()
    assert isinstance(stub, GenerativeProvider)
    assert stub.provider_name == "stub"
    assert stub.model_name == "stub-tutor-v1"


def test_stub_provider_structured_generation():
    stub = StubGenerativeProvider()
    schema = {"type": "object", "properties": {"message": {"type": "string"}}}
    resp = stub.generate_structured(
        system_prompt="Test system",
        user_prompt="<state>pre_submission</state> in the renin pathway what substrate does active renin cleave?",
        response_schema=schema,
    )
    assert isinstance(resp, ProviderResponse)
    assert resp.structured_data is not None
    assert "message" in resp.structured_data
    assert resp.latency_ms >= 0.0
    assert resp.input_tokens > 0
    assert resp.output_tokens > 0


def test_stub_provider_custom_response():
    stub = StubGenerativeProvider()
    custom_dict = {"message": "Custom Socratic response", "citations": []}
    stub.set_custom_response("custom_query", custom_dict)

    resp = stub.generate_structured(
        system_prompt="System",
        user_prompt="This is a custom_query inquiry",
        response_schema={},
    )
    assert resp.structured_data == custom_dict


def test_get_default_provider_returns_stub_by_default(monkeypatch):
    monkeypatch.delenv("MEDICALPLAB_TUTOR_PROVIDER", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    prov = get_default_provider()
    assert isinstance(prov, StubGenerativeProvider)
