import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.services.ai_router import AIRouterService

def test_ai_router_primary_within_threshold():
    """
    Test primary route when response TTFB is below 200ms abort threshold.
    Verifies that TTFB is measured separately and no failover occurs.
    """
    router = AIRouterService()
    result = asyncio.run(router.route_with_failover(
        prompt="Explain QuickSort algorithm",
        tier="triage",
        simulate_ttfb_ms=60.0 # Well below 200ms TTFB threshold
    ))
    
    print(f"\n[AI Router Normal] Model: {result['model_used']} | TTFB: {result['ttfb_ms']} ms | Total: {result['total_turnaround_ms']} ms")
    assert result["failover_triggered"] is False
    assert result["model_used"] == "gpt-4o-mini-2024-07-18"
    assert result["ttfb_ms"] is not None
    assert result["ttfb_ms"] < 200.0
    assert result["is_simulated"] is True

def test_ai_router_abort_probe_and_failover():
    """
    Test 200ms abort probe trigger when primary model TTFB exceeds 200ms.
    Verifies that the primary stream is aborted and fails over to verified active fallback model.
    """
    router = AIRouterService()
    result = asyncio.run(router.route_with_failover(
        prompt="Explain Dijkstra with negative edges",
        tier="triage",
        simulate_ttfb_ms=250.0 # Exceeds 200ms TTFB threshold
    ))
    
    print(f"\n[AI Router Failover] Model: {result['model_used']} | Total: {result['total_turnaround_ms']} ms | Reason: {result['failover_reason']}")
    assert result["failover_triggered"] is True
    assert result["model_used"] == "gemini-3.5-flash-lite"
    assert "ttfb_abort_threshold_exceeded" in result["failover_reason"]
