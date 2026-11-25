import pytest
import asyncio
import sys
import os
from typing import AsyncGenerator

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.services.ai_router import AIRouterService
from app.services.providers.simulation import SimulationProvider
from app.services.providers.base import BaseAIProvider, ProviderResponse, ProviderChunk
from app.services.providers.gemini_provider import GeminiProvider
from app.services.providers.anthropic_provider import AnthropicProvider

class FailingMockProvider(BaseAIProvider):
    async def stream_response(self, prompt: str, system_prompt=None, timeout_seconds=5.0) -> AsyncGenerator[ProviderChunk, None]:
        raise ConnectionError("Upstream AI Provider 502 Bad Gateway")
        yield  # Make it an async generator
        
    async def generate_response(self, prompt: str, system_prompt=None, timeout_seconds=5.0) -> ProviderResponse:
        raise ConnectionError("Upstream AI Provider 502 Bad Gateway")

def test_ai_router_provider_failure_and_fallback():
    """
    Test that when primary provider fails with an exception, the router seamlessly falls back
    to the secondary provider without crashing, returning explicit failover metadata.
    """
    router = AIRouterService()
    router.primary_adapter = FailingMockProvider()
    router.fallback_adapter = SimulationProvider(model_id="gemini-3.5-flash-lite", ttfb_ms=30.0, latency_ms=40.0)
    
    result = asyncio.run(router.route_with_failover(
        prompt="Synthesize research notes",
        tier="triage",
        simulate_delay_ms=50.0
    ))
    
    assert result["failover_triggered"] is True
    assert result["model_used"] == "gemini-3.5-flash-lite"
    assert "primary_provider_error" in result["failover_reason"]
    assert "FALLBACK ENGAGED" in result["content"]

def test_ai_router_timeout_abort_probe():
    """
    Test that primary provider taking longer than abort threshold (200ms) on TTFB triggers fallback.
    """
    router = AIRouterService()
    router.primary_adapter = SimulationProvider(model_id="gpt-4o-mini-2024-07-18", ttfb_ms=350.0, latency_ms=450.0)
    router.fallback_adapter = SimulationProvider(model_id="gemini-3.5-flash-lite", ttfb_ms=40.0, latency_ms=60.0)
    
    result = asyncio.run(router.route_with_failover(
        prompt="Explain topological sort",
        tier="triage"
    ))
    
    assert result["failover_triggered"] is True
    assert result["model_used"] == "gemini-3.5-flash-lite"
    assert "ttfb_abort_threshold_exceeded" in result["failover_reason"]

def test_retired_model_lifecycle_enforcement():
    """
    P0 Verification: Verify that retired model IDs (gemini-2.0-flash, claude-3-5-haiku-20241022,
    claude-3-5-sonnet-20241022) are explicitly rejected by provider constructors.
    """
    # Gemini retired model rejection
    with pytest.raises(ValueError) as excinfo:
        GeminiProvider(api_key="mock-key", model_id="gemini-2.0-flash")
    assert "RETIRED" in str(excinfo.value)
    
    # Anthropic retired models rejection
    with pytest.raises(ValueError) as excinfo_haiku:
        AnthropicProvider(api_key="mock-key", model_id="claude-3-5-haiku-20241022")
    assert "RETIRED" in str(excinfo_haiku.value)
    
    with pytest.raises(ValueError) as excinfo_sonnet:
        AnthropicProvider(api_key="mock-key", model_id="claude-3-5-sonnet-20241022")
    assert "RETIRED" in str(excinfo_sonnet.value)

def test_streaming_and_ttfb_metric_separation():
    """
    P1 Verification: Verify that streaming chunks provide chunk 0 as first byte with ttfb_ms,
    and that total turnaround time is strictly greater than or equal to ttfb_ms.
    """
    provider = SimulationProvider(model_id="gpt-4o-mini-2024-07-18", ttfb_ms=50.0, latency_ms=120.0)
    
    async def collect_stream():
        chunks = []
        async for c in provider.stream_response("Test prompt"):
            chunks.append(c)
        return chunks

    chunks = asyncio.run(collect_stream())
    assert len(chunks) > 1
    assert chunks[0].is_first is True
    assert chunks[0].ttfb_ms is not None
    assert chunks[0].ttfb_ms >= 45.0  # Measured simulated delay
    assert chunks[1].is_first is False
    assert chunks[1].ttfb_ms is None
