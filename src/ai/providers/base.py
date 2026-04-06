"""
AI Provider interfaces and implementations.
Supports OpenAI, Anthropic, Gemini, and local models.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, AsyncGenerator
from datetime import datetime
import json
import hashlib
import logging
import asyncio
from dataclasses import dataclass
from enum import Enum

from pydantic import BaseModel

from src.core.config import settings
from src.core.cache import RedisAnalysisCache, get_redis_client

logger = logging.getLogger(__name__)


# ==================== Models ====================


class AIProvider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    LOCAL = "local"


@dataclass
class AIResponse:
    """AI response wrapper."""

    content: str
    provider: str
    model: str
    tokens_used: int
    duration_ms: int
    cached: bool = False
    metadata: Dict[str, Any] = None


class AIAnalysisResult(BaseModel):
    """Structured AI analysis result."""

    attack_sophistication: str  # low, medium, high
    attacker_skill_level: str  # script_kiddie, intermediate, advanced, expert
    attack_objectives: List[str]
    threat_level: str  # low, medium, high, critical
    recommended_interaction_level: str  # low, medium, high
    deception_strategies: List[str]
    configuration_changes: Dict[str, Any]
    confidence: float
    reasoning: str
    mitre_attack_ids: List[str] = []


# ==================== Cache ====================

# Global analysis cache instance
_analysis_cache: Optional[RedisAnalysisCache] = None


async def get_analysis_cache() -> RedisAnalysisCache:
    """
    Get or create the analysis cache.
    Uses Redis if available, falls back to in-memory.
    """
    global _analysis_cache

    if _analysis_cache is None:
        redis_client = await get_redis_client()
        _analysis_cache = RedisAnalysisCache(
            redis_client=redis_client,
            ttl_seconds=settings.ai.cache_ttl,
            fallback_to_memory=True,
        )

        if redis_client:
            logger.info("Initialized Redis-backed analysis cache")
        else:
            logger.info("Initialized in-memory analysis cache (Redis unavailable)")

    return _analysis_cache


# Legacy in-memory cache for backward compatibility
class AnalysisCache:
    """Simple in-memory cache for AI responses."""

    def __init__(self, ttl_seconds: int = 3600):
        self.cache: Dict[str, tuple[str, datetime, int]] = {}
        self.ttl_seconds = ttl_seconds

    def _hash_key(self, content: str) -> str:
        """Create hash key from content."""
        return hashlib.sha256(content.encode()).hexdigest()

    def get(self, key: str) -> Optional[AIResponse]:
        """Get cached response."""
        if key in self.cache:
            content, timestamp, tokens = self.cache[key]
            if (datetime.utcnow() - timestamp).total_seconds() < self.ttl_seconds:
                return AIResponse(
                    content=content,
                    provider="cache",
                    model="cache",
                    tokens_used=tokens,
                    duration_ms=0,
                    cached=True,
                )
            else:
                del self.cache[key]
        return None

    def set(self, key: str, content: str, tokens: int):
        """Cache a response."""
        self.cache[key] = (content, datetime.utcnow(), tokens)

    def clear(self):
        """Clear cache."""
        self.cache.clear()


# ==================== Provider Interface ====================


class AIProviderInterface(ABC):
    """Abstract base class for AI providers."""

    def __init__(self, model: str, api_key: Optional[str] = None):
        self.model = model
        self.api_key = api_key
        self.client = None

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 2000,
        json_mode: bool = True,
    ) -> AIResponse:
        """Generate response from AI."""
        pass

    @abstractmethod
    async def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 2000,
    ) -> AsyncGenerator[str, None]:
        """Stream response from AI."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is available."""
        pass


# ==================== OpenAI Provider ====================


class OpenAIProvider(AIProviderInterface):
    """OpenAI API provider."""

    def __init__(
        self, model: str = "gpt-4-turbo-preview", api_key: Optional[str] = None
    ):
        super().__init__(model, api_key)

        if api_key:
            try:
                from openai import AsyncOpenAI

                self.client = AsyncOpenAI(api_key=api_key)
            except ImportError:
                logger.warning("OpenAI library not installed")

    def is_available(self) -> bool:
        return self.client is not None

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 2000,
        json_mode: bool = True,
    ) -> AIResponse:
        import time

        start = time.time()

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        response = await self.client.chat.completions.create(**kwargs)

        return AIResponse(
            content=response.choices[0].message.content,
            provider="openai",
            model=self.model,
            tokens_used=response.usage.total_tokens,
            duration_ms=int((time.time() - start) * 1000),
        )

    async def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 2000,
    ) -> AsyncGenerator[str, None]:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        stream = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )

        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content


# ==================== Anthropic Provider ====================


class AnthropicProvider(AIProviderInterface):
    """Anthropic API provider."""

    def __init__(
        self, model: str = "claude-3-opus-20240229", api_key: Optional[str] = None
    ):
        super().__init__(model, api_key)

        if api_key:
            try:
                from anthropic import AsyncAnthropic

                self.client = AsyncAnthropic(api_key=api_key)
            except ImportError:
                logger.warning("Anthropic library not installed")

    def is_available(self) -> bool:
        return self.client is not None

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 2000,
        json_mode: bool = True,
    ) -> AIResponse:
        import time

        start = time.time()

        kwargs = {
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [{"role": "user", "content": prompt}],
        }

        if system_prompt:
            kwargs["system"] = system_prompt

        response = await self.client.messages.create(**kwargs)

        return AIResponse(
            content=response.content[0].text,
            provider="anthropic",
            model=self.model,
            tokens_used=response.usage.input_tokens + response.usage.output_tokens,
            duration_ms=int((time.time() - start) * 1000),
        )

    async def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 2000,
    ) -> AsyncGenerator[str, None]:
        kwargs = {
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [{"role": "user", "content": prompt}],
        }

        if system_prompt:
            kwargs["system"] = system_prompt

        async with self.client.messages.stream(**kwargs) as stream:
            async for text in stream.text_stream:
                yield text


# ==================== Gemini Provider ====================


class GeminiProvider(AIProviderInterface):
    """Google Gemini API provider."""

    def __init__(self, model: str = "gemini-1.5-pro", api_key: Optional[str] = None):
        super().__init__(model, api_key)

        if api_key:
            try:
                import google.generativeai as genai

                genai.configure(api_key=api_key)
                self.client = genai.GenerativeModel(model)
            except ImportError:
                logger.warning("Google Generative AI library not installed")

    def is_available(self) -> bool:
        return self.client is not None

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 2000,
        json_mode: bool = True,
    ) -> AIResponse:
        import time

        start = time.time()

        full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt

        response = await asyncio.to_thread(
            self.client.generate_content,
            full_prompt,
            generation_config={
                "temperature": temperature,
                "max_output_tokens": max_tokens,
            },
        )

        return AIResponse(
            content=response.text,
            provider="gemini",
            model=self.model,
            tokens_used=response.usage_metadata.total_token_count,
            duration_ms=int((time.time() - start) * 1000),
        )

    async def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 2000,
    ) -> AsyncGenerator[str, None]:
        full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt

        response = await asyncio.to_thread(
            self.client.generate_content,
            full_prompt,
            generation_config={
                "temperature": temperature,
                "max_output_tokens": max_tokens,
            },
            stream=True,
        )

        for chunk in response:
            if chunk.text:
                yield chunk.text


# ==================== Provider Factory ====================


def create_provider(
    provider: str,
    model: Optional[str] = None,
    api_key: Optional[str] = None,
) -> AIProviderInterface:
    """Create an AI provider instance."""
    providers = {
        "openai": OpenAIProvider,
        "anthropic": AnthropicProvider,
        "gemini": GeminiProvider,
    }

    if provider not in providers:
        raise ValueError(f"Unknown provider: {provider}")

    return providers[provider](model=model, api_key=api_key)
