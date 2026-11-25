from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Dict, Any, AsyncGenerator

@dataclass
class ProviderChunk:
    text: str
    chunk_index: int
    is_first: bool = False
    ttfb_ms: Optional[float] = None

@dataclass
class ProviderResponse:
    content: str
    model_id: str
    provider_name: str
    is_simulated: bool = False
    connection_time_ms: Optional[float] = None
    ttfb_ms: Optional[float] = None
    latency_ms: float = 0.0  # Total turnaround time in ms
    raw_payload: Optional[Dict[str, Any]] = None

class BaseAIProvider(ABC):
    """
    Abstract AI Provider Interface enforcing streaming, TTFB measurement,
    lifecycle model validation, and timeout handling.
    """
    @abstractmethod
    async def generate_response(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None, 
        timeout_seconds: float = 5.0
    ) -> ProviderResponse:
        """
        Executes a prompt against the provider with timeout safety and returns complete response.
        """
        pass

    @abstractmethod
    async def stream_response(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        timeout_seconds: float = 5.0
    ) -> AsyncGenerator[ProviderChunk, None]:
        """
        Streams response chunks asynchronously to enable precise Time To First Byte (TTFB)
        measurement and incremental rendering.
        """
        pass

    async def check_health(self) -> bool:
        """
        Verifies API reachability and credentials.
        """
        return True
