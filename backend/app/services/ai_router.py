import asyncio
import time
from typing import Dict, Any, Optional, AsyncGenerator
from app.core.config import settings
from app.services.providers.base import BaseAIProvider, ProviderResponse, ProviderChunk
from app.services.providers.simulation import SimulationProvider
from app.services.providers.openai_provider import OpenAIProvider
from app.services.providers.gemini_provider import GeminiProvider
from app.services.providers.anthropic_provider import AnthropicProvider

class AIRouterService:
    """
    Multi-Provider Dual-Router AI Engine with True Time-To-First-Byte (TTFB) 200ms Abort Probe.
    
    Architectural Timing Definitions:
    - Connection Time: Network socket and TLS handshake establishment.
    - TTFB (Time to First Byte / Token): Elapsed time from request dispatch to receipt of chunk 0.
    - Total Turnaround Time: Total duration from dispatch until the stream completes.
    
    The 200ms abort probe strictly monitors TTFB (receipt of the first token/byte).
    If chunk 0 is not yielded within 200ms, the primary task is cancelled immediately
    via generator closure, and the request fails over to the secondary fallback provider.
    """
    def __init__(self, mode: Optional[str] = None):
        self.abort_threshold_ms = settings.LLM_TTFB_ABORT_THRESHOLD_MS
        self.mode = mode or getattr(settings, "AI_ROUTER_MODE", "simulation")
        
        # Primary Tier 1 Adapter: OpenAI gpt-4o-mini-2024-07-18
        if self.mode == "live" and settings.OPENAI_API_KEY:
            self.primary_adapter: BaseAIProvider = OpenAIProvider(
                api_key=settings.OPENAI_API_KEY, 
                model_id=settings.MODEL_TIER1_PRIMARY
            )
        else:
            self.primary_adapter = SimulationProvider(
                model_id=settings.MODEL_TIER1_PRIMARY, 
                ttfb_ms=45.0,
                latency_ms=80.0
            )

        # Fallback Tier 1 Adapter: Google Gemini 3.5 Flash-Lite
        if self.mode == "live" and settings.GOOGLE_GEMINI_API_KEY:
            self.fallback_adapter: BaseAIProvider = GeminiProvider(
                api_key=settings.GOOGLE_GEMINI_API_KEY,
                model_id=settings.MODEL_TIER1_FALLBACK
            )
        else:
            self.fallback_adapter = SimulationProvider(
                model_id=settings.MODEL_TIER1_FALLBACK,
                ttfb_ms=35.0,
                latency_ms=65.0
            )

        # Socratic Tier 2 Adapter: Anthropic Claude Haiku 5.5
        if self.mode == "live" and settings.ANTHROPIC_API_KEY:
            self.socratic_adapter: BaseAIProvider = AnthropicProvider(
                api_key=settings.ANTHROPIC_API_KEY,
                model_id=settings.MODEL_TIER2_SOCRATIC
            )
        else:
            self.socratic_adapter = SimulationProvider(
                model_id=settings.MODEL_TIER2_SOCRATIC,
                ttfb_ms=50.0,
                latency_ms=90.0
            )

    async def route_with_failover(
        self, 
        prompt: str, 
        tier: str = "triage", 
        simulate_delay_ms: Optional[float] = None,
        simulate_ttfb_ms: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Executes primary route with a real 200ms TTFB abort trigger.
        Measures TTFB and total turnaround time separately.
        Cancels the primary stream immediately on TTFB breach or error and falls back.
        """
        start_time = time.perf_counter()
        active_adapter = self.socratic_adapter if tier == "socratic" else self.primary_adapter
        
        # If simulated delay is provided in tests, apply to TTFB or total latency
        if isinstance(active_adapter, SimulationProvider):
            if simulate_ttfb_ms is not None:
                active_adapter.ttfb_ms = simulate_ttfb_ms
            elif simulate_delay_ms is not None:
                active_adapter.ttfb_ms = simulate_delay_ms
                active_adapter.latency_ms = max(active_adapter.latency_ms, simulate_delay_ms)

        failover_engaged = False
        failover_reason: Optional[str] = None
        content = ""
        engaged_model = ""
        provider_used = ""
        is_simulated = getattr(active_adapter, "is_simulated", True)
        measured_ttfb: Optional[float] = None
        
        system_scaffold = (
            "You are Sovela AI Socratic Mentor. You assist students and working professionals to think critically. "
            "Never give direct answers; guide with questions."
        )

        stream = None
        try:
            stream = active_adapter.stream_response(
                prompt=prompt,
                system_prompt=system_scaffold,
                timeout_seconds=5.0
            )
            
            # True TTFB Abort Probe: Wait for chunk 0 within abort_threshold_ms (200ms)
            ttfb_timeout_seconds = self.abort_threshold_ms / 1000.0
            first_chunk = await asyncio.wait_for(stream.__anext__(), timeout=ttfb_timeout_seconds)
            measured_ttfb = first_chunk.ttfb_ms or ((time.perf_counter() - start_time) * 1000.0)
            
            chunks = [first_chunk.text]
            async for chunk in stream:
                chunks.append(chunk.text)
                
            content = "".join(chunks)
            engaged_model = getattr(active_adapter, "model_id", "primary")
            provider_used = getattr(active_adapter, "provider_name", "unknown")
            is_simulated = getattr(active_adapter, "is_simulated", True)

        except (asyncio.TimeoutError, TimeoutError):
            # TTFB Abort Probe Triggered: Primary failed to return first byte within 200ms!
            failover_engaged = True
            failover_reason = f"ttfb_abort_threshold_exceeded (> {self.abort_threshold_ms}ms)"
            if stream:
                await stream.aclose()
        except Exception as exc:
            # Primary raised network/connection/HTTP error
            failover_engaged = True
            failover_reason = f"primary_provider_error: {str(exc)}"
            if stream:
                await stream.aclose()

        # If primary TTFB failed or threw, activate fallback
        if failover_engaged:
            try:
                fallback_start = time.perf_counter()
                fallback_resp: ProviderResponse = await self.fallback_adapter.generate_response(
                    prompt=prompt,
                    system_prompt=system_scaffold,
                    timeout_seconds=5.0
                )
                content = f"[FALLBACK ENGAGED: {fallback_resp.model_id}] {fallback_resp.content}"
                engaged_model = fallback_resp.model_id
                provider_used = fallback_resp.provider_name
                is_simulated = fallback_resp.is_simulated
                measured_ttfb = fallback_resp.ttfb_ms
            except Exception as e:
                # Emergency safe string fallback
                content = f"[FALLBACK ENGAGED: {settings.MODEL_TIER1_FALLBACK}] Fallback response for: {prompt}"
                engaged_model = settings.MODEL_TIER1_FALLBACK
                provider_used = "emergency_fallback"
                is_simulated = True

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        return {
            "content": content,
            "model_used": engaged_model,
            "provider_used": provider_used,
            "is_simulated": is_simulated,
            "ttfb_ms": round(measured_ttfb, 2) if measured_ttfb is not None else None,
            "total_turnaround_ms": round(elapsed_ms, 2),
            "failover_triggered": failover_engaged,
            "failover_reason": failover_reason
        }
