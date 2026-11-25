import httpx
import time
import json
from typing import Optional, AsyncGenerator
from app.services.providers.base import BaseAIProvider, ProviderResponse, ProviderChunk

class AnthropicProvider(BaseAIProvider):
    """
    Live Anthropic Claude Messages API Adapter.
    Enforces verified active models (e.g. claude-haiku-5-5, claude-sonnet-5-5).
    Strictly flags and blocks retired models:
    - claude-3-5-haiku-20241022 (Retired February 19, 2026)
    - claude-3-5-sonnet-20241022 (Retired October 28, 2025)
    - claude-3-haiku-20240307 / claude-2.1
    """
    RETIRED_MODELS = {
        "claude-3-5-haiku-20241022": "Retired February 19, 2026 per Anthropic API lifecycle schedule.",
        "claude-3-5-sonnet-20241022": "Retired October 28, 2025 per Anthropic API lifecycle schedule.",
        "claude-3-haiku-20240307": "Retired in 2025.",
        "claude-3-sonnet-20240229": "Retired in 2025.",
        "claude-2.1": "Retired in 2024."
    }

    def __init__(self, api_key: Optional[str] = None, model_id: str = "claude-haiku-5-5"):
        if model_id in self.RETIRED_MODELS:
            raise ValueError(
                f"Model ID '{model_id}' is RETIRED ({self.RETIRED_MODELS[model_id]}). "
                f"Please migrate to active model 'claude-haiku-5-5' or 'claude-sonnet-5-5'."
            )
        self.api_key = api_key
        self.model_id = model_id
        self.provider_name = "anthropic"
        self.endpoint = "https://api.anthropic.com/v1/messages"
        self.is_simulated = False

    async def stream_response(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        timeout_seconds: float = 5.0
    ) -> AsyncGenerator[ProviderChunk, None]:
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY is not configured")

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model_id,
            "max_tokens": 1024,
            "messages": [{"role": "user", "content": prompt}],
            "stream": True
        }
        if system_prompt:
            payload["system"] = system_prompt

        start_time = time.perf_counter()
        first_chunk_received = False
        chunk_idx = 0

        async with httpx.AsyncClient(timeout=timeout_seconds) as client:
            async with client.stream("POST", self.endpoint, headers=headers, json=payload) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    line = line.strip()
                    if not line or not line.startswith("data: "):
                        continue
                    data_str = line[len("data: "):]
                    try:
                        event = json.loads(data_str)
                        if event.get("type") == "content_block_delta":
                            delta = event.get("delta", {})
                            text = delta.get("text", "")
                            if text:
                                if not first_chunk_received:
                                    first_chunk_received = True
                                    ttfb_ms = (time.perf_counter() - start_time) * 1000.0
                                    yield ProviderChunk(
                                        text=text,
                                        chunk_index=chunk_idx,
                                        is_first=True,
                                        ttfb_ms=ttfb_ms
                                    )
                                else:
                                    yield ProviderChunk(
                                        text=text,
                                        chunk_index=chunk_idx,
                                        is_first=False,
                                        ttfb_ms=None
                                    )
                                chunk_idx += 1
                    except json.JSONDecodeError:
                        continue

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
            
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        
        return ProviderResponse(
            content="".join(full_text),
            model_id=self.model_id,
            provider_name=self.provider_name,
            is_simulated=False,
            ttfb_ms=measured_ttfb,
            latency_ms=elapsed_ms
        )
