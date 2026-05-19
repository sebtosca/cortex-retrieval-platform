from __future__ import annotations

import time
from collections.abc import AsyncIterator, Iterator

_RETRY_DELAYS = [5, 10, 20, 40, 60, 60]  # seconds between attempts


class CortexLLM:
    """LiteLLM-backed LLM client with sync and async streaming."""

    def __init__(self, model: str, max_tokens: int = 1024, temperature: float = 0.0):
        self._model = model
        self._max_tokens = max_tokens
        self._temperature = temperature

    def stream(self, messages: list[dict]) -> Iterator[str]:
        import litellm

        response = litellm.completion(
            model=self._model,
            messages=messages,
            stream=True,
            max_tokens=self._max_tokens,
            temperature=self._temperature,
        )
        for chunk in response:
            token = chunk.choices[0].delta.content or ""
            if token:
                yield token

    async def astream(self, messages: list[dict]) -> AsyncIterator[str]:
        import litellm

        response = await litellm.acompletion(
            model=self._model,
            messages=messages,
            stream=True,
            max_tokens=self._max_tokens,
            temperature=self._temperature,
        )
        async for chunk in response:
            token = chunk.choices[0].delta.content or ""
            if token:
                yield token

    def complete(self, messages: list[dict]) -> str:
        """Non-streaming completion with exponential-backoff retry on rate limits."""
        import litellm

        for attempt, delay in enumerate([0] + _RETRY_DELAYS):
            if delay:
                time.sleep(delay)
            try:
                response = litellm.completion(
                    model=self._model,
                    messages=messages,
                    stream=False,
                    max_tokens=self._max_tokens,
                    temperature=self._temperature,
                )
                return response.choices[0].message.content or ""
            except litellm.RateLimitError:
                if attempt == len(_RETRY_DELAYS):
                    raise
                continue
