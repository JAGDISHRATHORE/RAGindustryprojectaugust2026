"""Thin client for any OpenAI-compatible chat endpoint.

One code path serves Ollama and vLLM (local, data stays on premises), Azure
OpenAI and OpenAI. Only `base_url`, `api_key` and `model` change.

The client adds what the raw SDK lacks for production use:

* JSON output validated against a Pydantic schema, with a repair loop that
  sends the validation error back to the model,
* retries with exponential backoff for transient network and rate-limit errors,
* a response cache keyed by model and prompt, so re-running an assessment on an
  unchanged corpus costs nothing,
* token and cost accounting per run.
"""

from __future__ import annotations

import hashlib
import json
import logging
import threading
import time
from pathlib import Path
from typing import TypeVar

from openai import APIConnectionError, APITimeoutError, InternalServerError, OpenAI, RateLimitError
from pydantic import BaseModel, ValidationError
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from complyrag.config import Settings
from complyrag.schemas import RunMetrics

log = logging.getLogger(__name__)
T = TypeVar("T", bound=BaseModel)

_TRANSIENT = (APIConnectionError, APITimeoutError, RateLimitError, InternalServerError)


class LLMOutputError(RuntimeError):
    """The model kept returning output that does not match the schema."""


class UsageTracker:
    def __init__(self, price_in: float = 0.0, price_out: float = 0.0):
        self._lock = threading.Lock()
        self.price_in, self.price_out = price_in, price_out
        self.metrics = RunMetrics()

    def record(self, prompt_tokens: int, completion_tokens: int, cached: bool) -> None:
        with self._lock:
            m = self.metrics
            if cached:
                m.cache_hits += 1
                return
            m.llm_calls += 1
            m.prompt_tokens += prompt_tokens
            m.completion_tokens += completion_tokens
            m.cost_eur += (
                prompt_tokens / 1000 * self.price_in + completion_tokens / 1000 * self.price_out
            )


class LLMClient:
    def __init__(self, settings: Settings, tracker: UsageTracker | None = None):
        self.settings = settings
        self.model = settings.llm_model
        self.tracker = tracker or UsageTracker(
            settings.llm_price_in_per_1k, settings.llm_price_out_per_1k
        )
        self._client = OpenAI(
            base_url=settings.llm_base_url,
            api_key=settings.llm_api_key,
            timeout=settings.llm_timeout_s,
            max_retries=0,  # retries are handled by tenacity below
        )
        self._cache_dir: Path | None = None
        if settings.llm_cache:
            self._cache_dir = settings.cache_dir / "llm"
            self._cache_dir.mkdir(parents=True, exist_ok=True)

    # -- caching ---------------------------------------------------------------
    def _key(self, messages: list[dict]) -> str:
        payload = json.dumps([self.model, self.settings.llm_temperature, messages], sort_keys=True)
        return hashlib.sha256(payload.encode()).hexdigest()

    def _cache_get(self, key: str) -> str | None:
        if not self._cache_dir:
            return None
        path = self._cache_dir / f"{key}.json"
        return json.loads(path.read_text())["content"] if path.exists() else None

    def _cache_put(self, key: str, content: str) -> None:
        if self._cache_dir:
            (self._cache_dir / f"{key}.json").write_text(json.dumps({"content": content}))

    # -- calls -----------------------------------------------------------------
    @retry(
        retry=retry_if_exception_type(_TRANSIENT),
        wait=wait_exponential(multiplier=1, min=1, max=20),
        stop=stop_after_attempt(4),
        reraise=True,
    )
    def _complete(self, messages: list[dict]) -> str:
        key = self._key(messages)
        cached = self._cache_get(key)
        if cached is not None:
            self.tracker.record(0, 0, cached=True)
            return cached

        started = time.perf_counter()
        response = self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.settings.llm_temperature,
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content or ""
        usage = response.usage
        self.tracker.record(
            usage.prompt_tokens if usage else 0,
            usage.completion_tokens if usage else 0,
            cached=False,
        )
        log.debug("llm call %.2fs", time.perf_counter() - started)
        self._cache_put(key, content)
        return content

    def complete_json(self, system: str, user: str, schema: type[T]) -> T:
        messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
        last_error = ""
        for attempt in range(self.settings.llm_json_retries + 1):
            content = self._complete(messages)
            try:
                return schema.model_validate_json(_strip_fences(content))
            except ValidationError as err:
                last_error = str(err)
                log.warning("schema validation failed (attempt %d): %s", attempt + 1, last_error)
                messages = messages + [
                    {"role": "assistant", "content": content},
                    {
                        "role": "user",
                        "content": "Your answer did not match the required JSON schema:\n"
                        f"{last_error}\nReturn only the corrected JSON object.",
                    },
                ]
        raise LLMOutputError(last_error)


def _strip_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text
        text = text.rsplit("```", 1)[0]
    return text.strip()
