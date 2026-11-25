import httpx
import time
import json
from typing import Optional, AsyncGenerator
from app.services.providers.base import BaseAIProvider, ProviderResponse, ProviderChunk

class GeminiProvider(BaseAIProvider):
    """
    Live Google Gemini API Adapter.
    Enforces verified active models (e.g. gemini-3.5-flash-lite).
    Strictly flags and blocks retired models (e.g. gemini-2.0-flash retired June 1, 2026; gemini-1.5-flash).
    """
    RETIRED_MODELS = {
        "gemini-2.0-flash": "Shut down on June 1, 2026 per Google Cloud / AI Studio lifecycle policy.",
        "gemini-1.5-flash": "Retired and superseded by Gemini 2.5/3.5/3.8 Flash generations.",
        "gemini-1.0-pro": "Retired in 2025."
    }

    def __init__(self, api_key: Optional[str] = None, model_id: str = "gemini-3.5-flash-lite"):
        if model_id in self.RETIRED_MODELS:
            raise ValueError(
                f"Model ID '{model_id}' is RETIRED ({self.RETIRED_MODELS[model_id]}). "
                f"Please migrate to active snapshot 'gemini-3.5-flash-lite'."
            )
        self.api_key = api_key
        self.model_id = model_id
        self.provider_name = "google_gemini"
        self.is_simulated = False

    async def stream_response(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        timeout_seconds: float = 5.0
    ) -> AsyncGenerator[ProviderChunk, None]:
        if not self.api_key:
            raise ValueError("GOOGLE_GEMINI_API_KEY is not configured")

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_id}:streamGenerateContent?alt=sse&key={self.api_key}"
        
        contents = []
        if system_prompt:
            contents.append({"role": "user", "parts": [{"text": f"SYSTEM INSTRUCTION: {system_prompt}"}]})
        contents.append({"role": "user", "parts": [{"text": prompt}]})

        payload = {"contents": contents}
        start_time = time.perf_counter()
        first_chunk_received = False
        chunk_idx = 0

        async with httpx.AsyncClient(timeout=timeout_seconds) as client:
            async with client.stream("POST", url, json=payload) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    line = line.strip()
                    if not line or not line.startswith("data: "):
                        continue
                    data_str = line[len("data: "):]
                    try:
                        parsed = json.loads(data_str)
                        candidates = parsed.get("candidates", [])
                        if candidates:
                            parts = candidates[0].get("content", {}).get("parts", [])
                            for part in parts:
                                text = part.get("text", "")
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
