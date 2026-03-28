from __future__ import annotations

from datetime import UTC, datetime
from typing import Any


class AgentPromptBuilder:
    """Build dynamic system prompts with live memory and neighboring alert context."""

    def __init__(self, max_tokens: int = 4000) -> None:
        self.max_tokens = max_tokens

    def build_prompt(
        self,
        *,
        base_prompt: str,
        memory_lines: list[str] | None = None,
        recent_resolved_lines: list[str] | None = None,
        neighbor_alert_lines: list[str] | None = None,
        degradation_caveat: str | None = None,
        now_utc: datetime | None = None,
    ) -> str:
        """Create a bounded prompt with seasonal and dynamic context injections."""
        now = now_utc or datetime.now(UTC)
        month = now.month
        season = self._season_label(month)

        sections = [
            base_prompt.strip(),
            f"Current season context: {season}",
        ]

        if degradation_caveat:
            sections.append("")
            sections.append(degradation_caveat)

        if recent_resolved_lines:
            sections.append("Recent resolved disruptions (last 30 days):")
            sections.extend(f"- {line}" for line in recent_resolved_lines)

        if neighbor_alert_lines:
            sections.append("Active neighboring region alerts:")
            sections.extend(f"- {line}" for line in neighbor_alert_lines)

        if memory_lines:
            sections.append("Analogous historical memory:")
            sections.extend(f"- {line}" for line in memory_lines)

        prompt = "\n".join(sections)
        return self._trim_to_token_budget(prompt)

    @staticmethod
    def format_memory_line(entry: dict[str, Any]) -> str:
        """Format memory rows into canonical few-shot line style."""
        date_raw = str(entry.get("date") or entry.get("created_at") or "unknown-date")
        summary = str(entry.get("summary") or entry.get("content") or "No summary")
        resolution = str(entry.get("resolution") or "Unknown resolution")
        return f"Similar past event [{date_raw}]: {summary} → Outcome: {resolution}"

    def _trim_to_token_budget(self, prompt: str) -> str:
        # Approximate to stay under configured token budget (~4 chars/token).
        max_chars = self.max_tokens * 4
        if len(prompt) <= max_chars:
            return prompt
        return prompt[: max_chars - 3].rstrip() + "..."

    @staticmethod
    def _season_label(month: int) -> str:
        if month in {12, 1, 2}:
            return "Northern Hemisphere winter"
        if month in {3, 4, 5}:
            return "Northern Hemisphere spring"
        if month in {6, 7, 8}:
            return "Northern Hemisphere summer"
        return "Northern Hemisphere autumn"
