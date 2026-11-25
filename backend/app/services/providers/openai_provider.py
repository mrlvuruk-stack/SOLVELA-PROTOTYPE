import httpx
import time
import json
from typing import Optional, AsyncGenerator
from app.services.providers.base import BaseAIProvider, ProviderResponse, ProviderChunk

class OpenAIProvider(BaseAIProvider):
    """
    Live OpenAI API Adapter using official REST streaming endpoints.
    Enforces verified active snapshot models (e.g. gpt-4o-mini-2024-07-18).
    Captures live connection latency, TTFB, and total turnaround time.
    """
    RETIRED_MODELS = {
        "gpt-3.5-turbo-0613", "gpt-3.5-turbo-16k-0613", "gpt-4-0314", "gpt-4-0613"
    }

    def __init__(self, api_key: Optional[str] = None, model_id: str = "gpt-4o-mini-2024-07-18"):
        if model_id in self.RETIRED_MODELS:
            raise ValueError(f"Model ID '{model_id}' is retired and cannot be used in production.")
        self.api_key = api_key
        self.model_id = model_id
        self.provider_name = "openai"
        self.endpoint = "https://api.openai.com/v1/chat/completions"
        self.is_simulated = False

    async def stream_response(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        timeout_seconds: float = 5.0
    ) -> AsyncGenerator[ProviderChunk, None]:
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is not configured")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": self.model_id,
            "messages": messages,
            "temperature": 0.3,
            "stream": True
        }

        start_time = time.perf_counter()
        first_chunk_received = False
        chunk_idx = 0

        async with httpx.AsyncClient(timeout=timeout_seconds) as client:
            async with client.stream("POST", self.endpoint, headers=headers, json=payload) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    line = line.strip()
                    if not line or line == "data: [DONE]":
                        continue
                    if line.startswith("data: "):
                        data_str = line[len("data: "):]
                        try:
                            parsed = json.loads(data_str)
                            delta = parsed["choices"][0].get("delta", {})
                            content_piece = delta.get("content", "")
                            if content_piece:
                                if not first_chunk_received:
                                    first_chunk_received = True
                                    ttfb_ms = (time.perf_counter() - start_time) * 1000.0
                                    yield ProviderChunk(
                                        text=content_piece,
                                        chunk_index=chunk_idx,
                                        is_first=True,
                                        ttfb_ms=ttfb_ms
                                    )
                                else:
                                    yield ProviderChunk(
                                        text=content_piece,
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
