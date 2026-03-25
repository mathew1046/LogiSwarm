from __future__ import annotations

import logging
import os
import time
from typing import Any

import httpx
from pydantic import BaseModel, ConfigDict, Field


class MaxTokensWarningFilter(logging.Filter):
    """Suppress repetitive max-tokens warnings from provider/client loggers."""

    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage().lower()
        return "max token" not in message and "max_tokens" not in message


def configure_llm_logging_filter() -> None:
    """Attach max-token warning filter to relevant LLM-related loggers."""
    filter_instance = MaxTokensWarningFilter()
    for logger_name in ("", "httpx", "anthropic", "llm"):
        logging.getLogger(logger_name).addFilter(filter_instance)


class DisruptionAssessment(BaseModel):
    """Structured reasoning output returned by the LLM core."""

    model_config = ConfigDict(extra="allow")

    disruption_probability: float = Field(ge=0.0, le=1.0)
    severity: str
    affected_routes: list[str]
    recommended_actions: list[str]
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str


class ClaudeReasoningCore:
    """Anthropic Claude-powered reasoning engine with tool-use JSON output."""

    _INPUT_COST_PER_M_TOKENS = 3.0
    _OUTPUT_COST_PER_M_TOKENS = 15.0

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model_name: str | None = None,
        max_tokens: int = 800,
        timeout_seconds: float = 30.0,
        max_concurrent_calls: int = 5,
    ) -> None:
        configure_llm_logging_filter()

        self.api_key = api_key or os.getenv("LLM_API_KEY", "")
        self.base_url = (base_url or os.getenv("LLM_BASE_URL", "https://api.anthropic.com")).rstrip("/")
        self.model_name = model_name or os.getenv("LLM_MODEL_NAME", "claude-sonnet-4-6")
        self.max_tokens = max_tokens
        self.timeout_seconds = timeout_seconds

        configured_semaphore_size = int(
            os.getenv("LLM_MAX_CONCURRENT_CALLS", str(max_concurrent_calls))
        )
        self._semaphore = _GlobalSemaphoreRegistry.get(configured_semaphore_size)

    async def reason(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Convert feed + memory context into a structured disruption assessment."""
        if not self.api_key:
            return self._fallback_assessment(
                reasoning="LLM_API_KEY is missing; returning fallback assessment."
            )

        system_prompt = str(payload.get("system_prompt") or "You are a supply-chain risk analyst.")
        events = payload.get("events") if isinstance(payload.get("events"), list) else []
        memory_episodes = (
            payload.get("memory_episodes")
            if isinstance(payload.get("memory_episodes"), list)
            else []
        )

        user_prompt = self._build_user_prompt(events=events, memory_episodes=memory_episodes)
        started_at = time.perf_counter()

        async with self._semaphore:
            try:
                response_payload = await self._call_messages_api(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                )
                assessment = self._extract_tool_assessment(response_payload)
                assessment_obj = DisruptionAssessment.model_validate(assessment)
                result = assessment_obj.model_dump(mode="json")

                self._log_usage(response_payload=response_payload, started_at=started_at)
                return result
            except Exception as exc:
                return self._fallback_assessment(
                    reasoning=f"LLM reasoning failed: {exc}",
                )

    async def _call_messages_api(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> dict[str, Any]:
        endpoint = f"{self.base_url}/v1/messages"
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
        }

        payload = {
            "model": self.model_name,
            "max_tokens": self.max_tokens,
            "system": system_prompt,
            "messages": [
                {
                    "role": "user",
                    "content": [{"type": "text", "text": user_prompt}],
                }
            ],
            "tools": [
                {
                    "name": "submit_assessment",
                    "description": "Return a structured supply-chain disruption assessment.",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "disruption_probability": {
                                "type": "number",
                                "minimum": 0,
                                "maximum": 1,
                            },
                            "severity": {
                                "type": "string",
                                "enum": ["LOW", "MEDIUM", "HIGH", "CRITICAL"],
                            },
                            "affected_routes": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                            "recommended_actions": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                            "confidence": {
                                "type": "number",
                                "minimum": 0,
                                "maximum": 1,
                            },
                            "reasoning": {"type": "string"},
                        },
                        "required": [
                            "disruption_probability",
                            "severity",
                            "affected_routes",
                            "recommended_actions",
                            "confidence",
                            "reasoning",
                        ],
                        "additionalProperties": False,
                    },
                }
            ],
            "tool_choice": {"type": "tool", "name": "submit_assessment"},
        }

        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            response = await client.post(endpoint, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()

        if not isinstance(data, dict):
            raise ValueError("Unexpected LLM response format")
        return data

    @staticmethod
    def _build_user_prompt(events: list[Any], memory_episodes: list[Any]) -> str:
        return (
            "Assess disruption risk from current regional signals and memory. "
            "Prioritize route impact and actionable steps.\n\n"
            f"Current events:\n{events}\n\n"
            f"Retrieved memory episodes:\n{memory_episodes}\n"
        )

    @staticmethod
    def _extract_tool_assessment(response_payload: dict[str, Any]) -> dict[str, Any]:
        content = response_payload.get("content")
        if not isinstance(content, list):
            raise ValueError("LLM response missing content blocks")

        for block in content:
            if not isinstance(block, dict):
                continue
            if block.get("type") == "tool_use" and block.get("name") == "submit_assessment":
                tool_input = block.get("input")
                if isinstance(tool_input, dict):
                    return tool_input

        raise ValueError("LLM did not return tool_use assessment")

    def _log_usage(self, response_payload: dict[str, Any], started_at: float) -> None:
        usage = response_payload.get("usage") if isinstance(response_payload.get("usage"), dict) else {}
        input_tokens = int(usage.get("input_tokens", 0))
        output_tokens = int(usage.get("output_tokens", 0))
        latency_seconds = round(time.perf_counter() - started_at, 3)
        estimated_cost = self._estimate_cost(input_tokens=input_tokens, output_tokens=output_tokens)

        logging.getLogger("llm").info(
            "llm_call model=%s input_tokens=%s output_tokens=%s latency_s=%s est_cost_usd=%.6f",
            self.model_name,
            input_tokens,
            output_tokens,
            latency_seconds,
            estimated_cost,
        )

    def _estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        return (
            (input_tokens / 1_000_000) * self._INPUT_COST_PER_M_TOKENS
            + (output_tokens / 1_000_000) * self._OUTPUT_COST_PER_M_TOKENS
        )

    @staticmethod
    def _fallback_assessment(reasoning: str) -> dict[str, Any]:
        assessment = DisruptionAssessment(
            disruption_probability=0.0,
            severity="LOW",
            affected_routes=[],
            recommended_actions=[],
            confidence=0.0,
            reasoning=reasoning,
        )
        return assessment.model_dump(mode="json")


class _GlobalSemaphoreRegistry:
    """Process-wide semaphore registry to enforce shared LLM concurrency limits."""

    _semaphores: dict[int, asyncio.Semaphore] = {}

    @classmethod
    def get(cls, size: int) -> asyncio.Semaphore:
        if size <= 0:
            size = 1
        if size not in cls._semaphores:
            cls._semaphores[size] = asyncio.Semaphore(size)
        return cls._semaphores[size]
