# LogiSwarm - Geo-Aware Swarm Intelligence for Supply Chains
# Copyright (C) 2025 LogiSwarm Contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from typing import Any, Literal

import httpx
from openai import AsyncOpenAI
from pydantic import BaseModel, ConfigDict, Field

from app.rate_limiter import llm_rate_limiter


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


LLMMode = Literal["primary", "fallback"]


class ClaudeReasoningCore:
    """Anthropic Claude-powered reasoning engine with dual LLM configuration."""

    _INPUT_COST_PER_M_TOKENS = 3.0
    _OUTPUT_COST_PER_M_TOKENS = 15.0

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model_name: str | None = None,
        max_tokens: int = 800,
        timeout_seconds: float = 30.0,
        agent_id: str | None = None,
        mode: LLMMode = "primary",
    ) -> None:
        configure_llm_logging_filter()

        self.mode = mode
        self.max_tokens = max_tokens
        self.timeout_seconds = timeout_seconds
        self.agent_id = agent_id or "unknown"

        if mode == "primary":
            config = llm_rate_limiter.get_primary_config()
            self.api_key = api_key or config.api_key or os.getenv("LLM_API_KEY", "")
            self.base_url = (base_url or config.base_url).rstrip("/")
            self.model_name = model_name or config.model_name
        else:
            config = llm_rate_limiter.get_fallback_config()
            self.api_key = api_key or config.api_key or os.getenv("LLM_API_KEY", "")
            self.base_url = (base_url or config.base_url).rstrip("/")
            self.model_name = model_name or config.model_name

        self._fallback_timeout_seconds = float(
            os.getenv("LLM_FALLBACK_TIMEOUT_SECONDS", "10.0")
        )

        # Detect if using OpenAI-compatible API (OpenCode Go, etc.)
        self._is_openai_compatible = self._detect_openai_compatible(self.base_url)
        self._openai_client: AsyncOpenAI | None = None

        if self._is_openai_compatible:
            self._openai_client = AsyncOpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
                timeout=self.timeout_seconds,
            )

    def _detect_openai_compatible(self, base_url: str) -> bool:
        """Detect if the provider uses OpenAI-compatible API format."""
        # OpenCode Go and similar providers use OpenAI format
        openai_providers = [
            "opencode.ai",
            "openai.com",
            "azure.com",
            "together.xyz",
            "fireworks.ai",
            "groq.com",
        ]
        return any(provider in base_url.lower() for provider in openai_providers)

    async def reason(
        self,
        payload: dict[str, Any],
        use_fallback_on_error: bool = True,
    ) -> dict[str, Any]:
        """Convert feed + memory context into a structured disruption assessment."""
        if not self.api_key:
            return self._fallback_assessment(
                reasoning="LLM_API_KEY is missing; returning fallback assessment."
            )

        acquired = await llm_rate_limiter.acquire(self.agent_id)
        if not acquired:
            return self._fallback_assessment(
                reasoning="LLM call rate-limited; returning fallback assessment."
            )

        try:
            use_fallback, model_to_use = llm_rate_limiter.should_use_fallback(
                self.model_name
            )
            current_mode = "fallback" if use_fallback else self.mode

            system_prompt = str(
                payload.get("system_prompt") or "You are a supply-chain risk analyst."
            )
            events = (
                payload.get("events") if isinstance(payload.get("events"), list) else []
            )
            memory_episodes = (
                payload.get("memory_episodes")
                if isinstance(payload.get("memory_episodes"), list)
                else []
            )

            user_prompt = self._build_user_prompt(
                events=events, memory_episodes=memory_episodes
            )
            started_at = time.perf_counter()

            try:
                response_payload = await self._call_messages_api(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    model_override=model_to_use if use_fallback else None,
                )
                assessment = self._extract_tool_assessment(response_payload)
                assessment_obj = DisruptionAssessment.model_validate(assessment)
                result = assessment_obj.model_dump(mode="json")

                elapsed_ms = (time.perf_counter() - started_at) * 1000
                usage = response_payload.get("usage", {})
                provider_name = (
                    "opencode" if self._is_openai_compatible else "anthropic"
                )
                llm_rate_limiter.log_call(
                    agent_id=self.agent_id,
                    model=model_to_use if use_fallback else self.model_name,
                    tokens_in=int(usage.get("input_tokens", 0)),
                    tokens_out=int(usage.get("output_tokens", 0)),
                    latency_ms=elapsed_ms,
                    provider=provider_name,
                    model_type=current_mode,
                    fallback_used=use_fallback,
                )
                return result

            except httpx.HTTPStatusError as exc:
                if (
                    use_fallback_on_error
                    and exc.response.status_code == 429
                    and self.mode != "fallback"
                ):
                    llm_rate_limiter.mark_fallback_needed(
                        reason="rate_limit_429",
                        original_model=self.model_name,
                    )
                    return await self._call_with_fallback(
                        system_prompt=system_prompt,
                        user_prompt=user_prompt,
                        started_at=started_at,
                    )
                return self._fallback_assessment(
                    reasoning=f"LLM API error: {exc.response.status_code}"
                )

            except asyncio.TimeoutError:
                if use_fallback_on_error and self.mode != "fallback":
                    llm_rate_limiter.mark_fallback_needed(
                        reason="timeout",
                        original_model=self.model_name,
                    )
                    return await self._call_with_fallback(
                        system_prompt=system_prompt,
                        user_prompt=user_prompt,
                        started_at=started_at,
                    )
                return self._fallback_assessment(reasoning="LLM call timed out")

            except Exception as exc:
                return self._fallback_assessment(
                    reasoning=f"LLM reasoning failed: {exc}"
                )

        finally:
            llm_rate_limiter.release()

    async def _call_with_fallback(
        self,
        system_prompt: str,
        user_prompt: str,
        started_at: float,
    ) -> dict[str, Any]:
        """Retry the LLM call with the fallback model."""
        fallback_config = llm_rate_limiter.get_fallback_config()

        try:
            response_payload = await self._call_messages_api(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                api_key=fallback_config.api_key,
                base_url=fallback_config.base_url,
                model_override=fallback_config.model_name,
            )
            assessment = self._extract_tool_assessment(response_payload)
            assessment_obj = DisruptionAssessment.model_validate(assessment)
            result = assessment_obj.model_dump(mode="json")

            elapsed_ms = (time.perf_counter() - started_at) * 1000
            usage = response_payload.get("usage", {})
            llm_rate_limiter.log_call(
                agent_id=self.agent_id,
                model=fallback_config.model_name,
                tokens_in=int(usage.get("input_tokens", 0)),
                tokens_out=int(usage.get("output_tokens", 0)),
                latency_ms=elapsed_ms,
                provider="anthropic",
                model_type="fallback",
                fallback_used=True,
            )
            return result

        except Exception as exc:
            return self._fallback_assessment(
                reasoning=f"Fallback LLM call failed: {exc}"
            )

    async def _call_messages_api(
        self,
        system_prompt: str,
        user_prompt: str,
        api_key: str | None = None,
        base_url: str | None = None,
        model_override: str | None = None,
    ) -> dict[str, Any]:
        effective_api_key = api_key or self.api_key
        effective_base_url = (base_url or self.base_url).rstrip("/")
        effective_model = model_override or self.model_name

        # Use OpenAI-compatible client for providers like OpenCode Go
        is_openai = self._is_openai_compatible or self._detect_openai_compatible(
            effective_base_url
        )
        if is_openai:
            return await self._call_openai_api(
                system_prompt,
                user_prompt,
                effective_api_key,
                effective_base_url,
                effective_model,
            )

        # Original Anthropic API call
        endpoint = f"{effective_base_url}/v1/messages"
        headers = {
            "Content-Type": "application/json",
            "x-api-key": effective_api_key,
            "anthropic-version": "2023-06-01",
        }

        payload = {
            "model": effective_model,
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

        timeout = max(
            self.timeout_seconds,
            llm_rate_limiter.fallback_timeout_seconds
            if model_override
            else self.timeout_seconds,
        )

        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(endpoint, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()

        if not isinstance(data, dict):
            raise ValueError("Unexpected LLM response format")
        return data

    async def _call_openai_api(
        self,
        system_prompt: str,
        user_prompt: str,
        api_key: str,
        base_url: str,
        model: str,
    ) -> dict[str, Any]:
        """Call OpenAI-compatible API (OpenCode Go, etc.)."""
        # Create temporary client if base_url differs (e.g., for fallback)
        client = self._openai_client
        if not client or base_url != self.base_url:
            client = AsyncOpenAI(
                api_key=api_key, base_url=base_url, timeout=self.timeout_seconds
            )

        # Build the full prompt with structured instructions
        full_prompt = (
            f"{system_prompt}\n\n"
            f"{user_prompt}\n\n"
            "You must respond with a JSON object matching this structure:\n"
            "{\n"
            '  "disruption_probability": <float 0.0-1.0>,\n'
            '  "severity": "LOW" | "MEDIUM" | "HIGH" | "CRITICAL",\n'
            '  "affected_routes": ["<route_id>", ...],\n'
            '  "recommended_actions": ["<action>", ...],\n'
            '  "confidence": <float 0.0-1.0>,\n'
            '  "reasoning": "<explanation>"\n'
            "}"
        )

        response = await client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": full_prompt}],
            temperature=0.3,
            max_tokens=self.max_tokens if self.max_tokens else None,
        )

        content = response.choices[0].message.content
        if not content:
            raise ValueError("OpenAI API returned empty response")

        # Parse JSON from response
        try:
            # Extract JSON if wrapped in markdown code blocks
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            assessment = json.loads(content.strip())

            # Convert to Anthropic-like response format
            return {
                "content": [
                    {
                        "type": "tool_use",
                        "name": "submit_assessment",
                        "input": assessment,
                    }
                ],
                "usage": {
                    "input_tokens": response.usage.prompt_tokens
                    if response.usage
                    else 0,
                    "output_tokens": response.usage.completion_tokens
                    if response.usage
                    else 0,
                },
            }
        except json.JSONDecodeError as e:
            raise ValueError(
                f"Failed to parse JSON response from LLM: {e}\nContent: {content}"
            )

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
            if (
                block.get("type") == "tool_use"
                and block.get("name") == "submit_assessment"
            ):
                tool_input = block.get("input")
                if isinstance(tool_input, dict):
                    return tool_input

        raise ValueError("LLM did not return tool_use assessment")

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
