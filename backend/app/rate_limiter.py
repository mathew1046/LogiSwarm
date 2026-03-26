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
    tokens_in: int
    tokens_out: int
    latency_ms: float
    cost_estimate: float
    provider: str


@dataclass
class DailyBudget:
    date: datetime
    total_cost: float
    call_count: int
    total_tokens_in: int
    total_tokens_out: int


class LLMRateLimiter:
    def __init__(
        self,
        max_concurrent_calls: int = 5,
        min_cycle_interval_seconds: int = 60,
        daily_budget_threshold: float = 10.0,
        fallback_model: str = "claude-3-haiku-20240307",
    ):
        self.semaphore = asyncio.Semaphore(max_concurrent_calls)
        self.min_cycle_interval = min_cycle_interval_seconds
        self.daily_budget_threshold = daily_budget_threshold
        self.fallback_model = fallback_model

        self._agent_last_cycle: dict[str, float] = {}
        self._call_logs: list[LLMCallLog] = []
        self._budget_by_date: dict[str, DailyBudget] = {}

        self._model_costs = {
            "claude-3-opus-20240229": {"in": 0.015, "out": 0.075},
            "claude-3-sonnet-20240229": {"in": 0.003, "out": 0.015},
            "claude-3-haiku-20240307": {"in": 0.00025, "out": 0.00125},
        }

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
        costs = self._model_costs.get(
            model, self._model_costs["claude-3-haiku-20240307"]
        )
        cost_in = (tokens_in / 1000) * costs["in"]
        cost_out = (tokens_out / 1000) * costs["out"]
        return cost_in + cost_out

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
            ),
        )

        if budget.total_cost >= self.daily_budget_threshold:
            logger.bind(
                event="budget_guard",
                model=model,
                daily_spend=f"${budget.total_cost:.4f}",
                threshold=f"${self.daily_budget_threshold:.2f}",
            ).warning("Daily budget threshold exceeded, using fallback model")
            return True, self.fallback_model

        return False, model

    def log_call(
        self,
        agent_id: str,
        model: str,
        tokens_in: int,
        tokens_out: int,
        latency_ms: float,
        provider: str = "anthropic",
    ) -> None:
        cost = self.estimate_cost(model, tokens_in, tokens_out)

        log = LLMCallLog(
            timestamp=datetime.now(UTC),
            agent_id=agent_id,
            model=model,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            latency_ms=latency_ms,
            cost_estimate=cost,
            provider=provider,
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
            )

        budget = self._budget_by_date[today]
        budget.total_cost += cost
        budget.call_count += 1
        budget.total_tokens_in += tokens_in
        budget.total_tokens_out += tokens_out

        logger.bind(
            event="llm_call",
            agent_id=agent_id,
            model=model,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            latency_ms=f"{latency_ms:.2f}",
            cost=f"${cost:.6f}",
            daily_spend=f"${budget.total_cost:.4f}",
        ).info(f"LLM call logged: {model} for {agent_id}")

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
            },
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
    fallback_model=os.getenv("LLM_FALLBACK_MODEL", "claude-3-haiku-20240307"),
)
