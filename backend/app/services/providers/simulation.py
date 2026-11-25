import asyncio
import time
from typing import Optional, AsyncGenerator
from app.services.providers.base import BaseAIProvider, ProviderResponse, ProviderChunk

class SimulationProvider(BaseAIProvider):
    """
    Deterministic Simulation Provider Adapter for benchmark test suites and offline development.
    Explicitly distinguishes between TTFB (Time to First Byte/Token) and total response completion.
    Always marks responses with is_simulated=True so simulated benchmarks are never mislabeled as live calls.
    """
    def __init__(
        self, 
        model_id: str = "gpt-4o-mini-2024-07-18", 
        ttfb_ms: float = 40.0, 
        latency_ms: float = 80.0, 
        should_fail: bool = False,
        fail_during_stream: bool = False
    ):
        self.model_id = model_id
        self.ttfb_ms = ttfb_ms
        self.latency_ms = max(latency_ms, ttfb_ms)
        self.should_fail = should_fail
        self.fail_during_stream = fail_during_stream
        self.provider_name = "simulation"
        self.is_simulated = True

    async def stream_response(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        timeout_seconds: float = 5.0
    ) -> AsyncGenerator[ProviderChunk, None]:
        start_time = time.perf_counter()
        
        # Simulate network & connection establishment + initial inference up to TTFB
        await asyncio.sleep(self.ttfb_ms / 1000.0)
        
        if self.should_fail:
            raise TimeoutError(f"Simulated primary provider gateway timeout for model {self.model_id}")
            
        actual_ttfb = (time.perf_counter() - start_time) * 1000.0
        
        # Yield first chunk (Time To First Byte / First Token)
        yield ProviderChunk(
            text=f"[{self.model_id}] ",
            chunk_index=0,
            is_first=True,
            ttfb_ms=actual_ttfb
        )
        
        if self.fail_during_stream:
            raise RuntimeError(f"Simulated stream disconnection error for model {self.model_id}")
            
        # Simulate subsequent streaming tokens up to full turnaround
        remaining_delay = max(0.0, (self.latency_ms - self.ttfb_ms) / 1000.0)
        chunks = [
            "Socratic pedagogical guidance: ",
            "What assumptions underlie ",
            f"your solution for: {prompt}?"
        ]
        chunk_delay = remaining_delay / max(len(chunks), 1)
        
        for idx, chunk in enumerate(chunks, start=1):
            await asyncio.sleep(chunk_delay)
            yield ProviderChunk(
                text=chunk,
                chunk_index=idx,
                is_first=False,
                ttfb_ms=None
            )

    async def generate_response(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None, 
        timeout_seconds: float = 5.0
    ) -> ProviderResponse:
        start_time = time.perf_counter()
        full_text = []
        measured_ttfb: Optional[float] = None
        
        async for chunk in self.stream_response(prompt, system_prompt, timeout_seconds):
            if chunk.is_first and chunk.ttfb_ms is not None:
                measured_ttfb = chunk.ttfb_ms
            full_text.append(chunk.text)
            
        total_elapsed = (time.perf_counter() - start_time) * 1000.0
        
        return ProviderResponse(
            content="".join(full_text),
            model_id=self.model_id,
            provider_name=self.provider_name,
            is_simulated=True,
            ttfb_ms=measured_ttfb,
            latency_ms=total_elapsed
        )
