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

import asyncio
import os
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Optional

from loguru import logger


@dataclass
class LLMCallLog:
    timestamp: datetime
    agent_id: str
    model: str
    model_type: str
    tokens_in: int
    tokens_out: int
    latency_ms: float
    cost_estimate: float
    provider: str
    fallback_used: bool


@dataclass
class DailyBudget:
    date: datetime
    total_cost: float
    call_count: int
    total_tokens_in: int
    total_tokens_out: int
    fallback_call_count: int


@dataclass
class LLMConfig:
    """Configuration for a single LLM provider."""

    api_key: str
    base_url: str
    model_name: str
    cost_per_million_input: float
    cost_per_million_output: float


class LLMRateLimiter:
    def __init__(
        self,
        max_concurrent_calls: int = 5,
        min_cycle_interval_seconds: int = 60,
        daily_budget_threshold: float = 10.0,
        fallback_model: str = "claude-3-haiku-20240307",
        fallback_timeout_seconds: float = 10.0,
    ):
        self.semaphore = asyncio.Semaphore(max_concurrent_calls)
        self.min_cycle_interval = min_cycle_interval_seconds
        self.daily_budget_threshold = daily_budget_threshold
        self.fallback_model = fallback_model
        self.fallback_timeout_seconds = fallback_timeout_seconds

        self._agent_last_cycle: dict[str, float] = {}
        self._call_logs: list[LLMCallLog] = []
        self._budget_by_date: dict[str, DailyBudget] = {}

        self.primary_config = self._load_primary_config()
        self.fallback_config = self._load_fallback_config()

        self._model_costs = {
            "claude-3-opus-20240229": {"in": 15.0, "out": 75.0},
            "claude-3-sonnet-20240229": {"in": 3.0, "out": 15.0},
            "claude-3-haiku-20240307": {"in": 0.25, "out": 1.25},
            "claude-3-5-sonnet-20241022": {"in": 3.0, "out": 15.0},
            "claude-sonnet-4-6": {"in": 3.0, "out": 15.0},
        }

    def _load_primary_config(self) -> LLMConfig:
        return LLMConfig(
            api_key=os.getenv("LLM_PRIMARY_API_KEY", os.getenv("LLM_API_KEY", "")),
            base_url=os.getenv(
                "LLM_PRIMARY_BASE_URL",
                os.getenv("LLM_BASE_URL", "https://api.anthropic.com"),
            ).rstrip("/"),
            model_name=os.getenv(
                "LLM_PRIMARY_MODEL_NAME",
                os.getenv("LLM_MODEL_NAME", "claude-sonnet-4-6"),
            ),
            cost_per_million_input=float(os.getenv("LLM_PRIMARY_COST_INPUT", "3.0")),
            cost_per_million_output=float(os.getenv("LLM_PRIMARY_COST_OUTPUT", "15.0")),
        )

    def _load_fallback_config(self) -> LLMConfig:
        return LLMConfig(
            api_key=os.getenv("LLM_FALLBACK_API_KEY", os.getenv("LLM_API_KEY", "")),
            base_url=os.getenv(
                "LLM_FALLBACK_BASE_URL",
                os.getenv("LLM_BASE_URL", "https://api.anthropic.com"),
            ).rstrip("/"),
            model_name=os.getenv("LLM_FALLBACK_MODEL_NAME", "claude-3-haiku-20240307"),
            cost_per_million_input=float(os.getenv("LLM_FALLBACK_COST_INPUT", "0.25")),
            cost_per_million_output=float(
                os.getenv("LLM_FALLBACK_COST_OUTPUT", "1.25")
            ),
        )

    def get_primary_config(self) -> LLMConfig:
        return self.primary_config

    def get_fallback_config(self) -> LLMConfig:
        return self.fallback_config

    def should_use_fallback(self, model: str) -> tuple[bool, str]:
        today = datetime.now(UTC).strftime("%Y-%m-%d")
        budget = self._budget_by_date.get(
            today,
            DailyBudget(
                date=datetime.now(UTC),
                total_cost=0,
                call_count=0,
                total_tokens_in=0,
                total_tokens_out=0,
                fallback_call_count=0,
            ),
        )

        if budget.total_cost >= self.daily_budget_threshold:
            logger.bind(
                event="budget_guard",
                model=model,
                daily_spend=f"${budget.total_cost:.4f}",
                threshold=f"${self.daily_budget_threshold:.2f}",
            ).warning("Daily budget threshold exceeded, using fallback model")
            return True, self.fallback_config.model_name

        return False, model

    def mark_fallback_needed(
        self, reason: str, original_model: str
    ) -> tuple[bool, str]:
        logger.bind(
            event="llm_fallback",
            reason=reason,
            original_model=original_model,
            fallback_model=self.fallback_config.model_name,
        ).warning(f"Switching to fallback model: {reason}")

        return True, self.fallback_config.model_name

    def can_proceed(self, agent_id: str) -> tuple[bool, Optional[float]]:
        now = time.time()
        last_cycle = self._agent_last_cycle.get(agent_id, 0)
        elapsed = now - last_cycle

        if elapsed < self.min_cycle_interval:
            wait_time = self.min_cycle_interval - elapsed
            return False, wait_time

        return True, None

    def record_cycle_start(self, agent_id: str) -> None:
        self._agent_last_cycle[agent_id] = time.time()

    async def acquire(self, agent_id: str) -> bool:
        can_proceed, wait_time = self.can_proceed(agent_id)
        if not can_proceed:
            logger.bind(
                event="rate_limited",
                agent_id=agent_id,
                wait_seconds=f"{wait_time:.2f}",
            ).warning(f"Agent {agent_id} rate-limited, wait {wait_time:.2f}s")
            return False

        await self.semaphore.acquire()
        self.record_cycle_start(agent_id)
        return True

    def release(self) -> None:
        try:
            self.semaphore.release()
        except ValueError:
            pass

    def estimate_cost(self, model: str, tokens_in: int, tokens_out: int) -> float:
        if model == self.primary_config.model_name:
            costs = {
                "in": self.primary_config.cost_per_million_input,
                "out": self.primary_config.cost_per_million_output,
            }
        elif model == self.fallback_config.model_name:
            costs = {
                "in": self.fallback_config.cost_per_million_input,
                "out": self.fallback_config.cost_per_million_output,
            }
        else:
            costs = self._model_costs.get(
                model,
                self._model_costs.get(
                    "claude-3-haiku-20240307", {"in": 0.25, "out": 1.25}
                ),
            )

        cost_in = (tokens_in / 1_000_000) * costs["in"]
        cost_out = (tokens_out / 1_000_000) * costs["out"]
        return cost_in + cost_out

    def log_call(
        self,
        agent_id: str,
        model: str,
        tokens_in: int,
        tokens_out: int,
        latency_ms: float,
        provider: str = "anthropic",
        model_type: str = "primary",
        fallback_used: bool = False,
    ) -> None:
        cost = self.estimate_cost(model, tokens_in, tokens_out)

        log = LLMCallLog(
            timestamp=datetime.now(UTC),
            agent_id=agent_id,
            model=model,
            model_type=model_type,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            latency_ms=latency_ms,
            cost_estimate=cost,
            provider=provider,
            fallback_used=fallback_used,
        )

        self._call_logs.append(log)

        today = datetime.now(UTC).strftime("%Y-%m-%d")
        if today not in self._budget_by_date:
            self._budget_by_date[today] = DailyBudget(
                date=datetime.now(UTC),
                total_cost=0,
                call_count=0,
                total_tokens_in=0,
                total_tokens_out=0,
                fallback_call_count=0,
            )

        budget = self._budget_by_date[today]
        budget.total_cost += cost
        budget.call_count += 1
        budget.total_tokens_in += tokens_in
        budget.total_tokens_out += tokens_out
        if fallback_used:
            budget.fallback_call_count += 1

        logger.bind(
            event="llm_call",
            agent_id=agent_id,
            model=model,
            model_type=model_type,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            latency_ms=f"{latency_ms:.2f}",
            cost=f"${cost:.6f}",
            daily_spend=f"${budget.total_cost:.4f}",
            fallback_used=fallback_used,
        ).info(f"LLM call logged: {model} ({model_type}) for {agent_id}")

    def get_stats(self) -> dict:
        today = datetime.now(UTC).strftime("%Y-%m-%d")
        budget = self._budget_by_date.get(today)

        return {
            "daily_budget": {
                "date": today,
                "total_cost": budget.total_cost if budget else 0,
                "call_count": budget.call_count if budget else 0,
                "total_tokens_in": budget.total_tokens_in if budget else 0,
                "total_tokens_out": budget.total_tokens_out if budget else 0,
                "threshold": self.daily_budget_threshold,
                "fallback_call_count": budget.fallback_call_count if budget else 0,
            },
            "primary_model": self.primary_config.model_name,
            "fallback_model": self.fallback_config.model_name,
            "semaphore": {
                "max_concurrent": self.semaphore._value
                + self.semaphore._waiters.count()
                if hasattr(self.semaphore, "_waiters")
                else 5,
                "available": self.semaphore._value,
            },
            "agent_cycles": {
                agent_id: {"last_cycle_ago_seconds": time.time() - last_cycle}
                for agent_id, last_cycle in self._agent_last_cycle.items()
            },
        }


llm_rate_limiter = LLMRateLimiter(
    max_concurrent_calls=int(os.getenv("LLM_MAX_CONCURRENT", "5")),
    min_cycle_interval_seconds=int(os.getenv("LLM_MIN_CYCLE_INTERVAL", "60")),
    daily_budget_threshold=float(os.getenv("LLM_DAILY_BUDGET_USD", "10.0")),
    fallback_model=os.getenv("LLM_FALLBACK_MODEL_NAME", "claude-3-haiku-20240307"),
    fallback_timeout_seconds=float(os.getenv("LLM_FALLBACK_TIMEOUT_SECONDS", "10.0")),
)
