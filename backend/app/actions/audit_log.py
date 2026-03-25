from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.memory import ZepEpisodicMemory
from app.db.models import DecisionLog


DecisionType = Literal["AUTO_ACT", "RECOMMEND", "MONITOR"]
DecisionOutcome = Literal["correct", "incorrect"]


class DecisionLogCreatePayload(BaseModel):
    """Input payload used to record one decision trace row."""

    project_id: str = Field(min_length=1)
    region_id: str = Field(min_length=1)
    decision_type: DecisionType
    confidence: float = Field(ge=0.0, le=1.0)
    input_events: dict[str, Any] = Field(default_factory=dict)
    output_action: dict[str, Any] = Field(default_factory=dict)
    human_override: bool = False
    outcome: DecisionOutcome | None = None


class DecisionFeedbackPayload(BaseModel):
    """Feedback marker for decision correctness and optional human override."""

    correct: bool
    human_override: bool = False
    notes: str | None = Field(default=None, max_length=2000)


class DecisionFeedbackResult(BaseModel):
    """Result returned when feedback is written and propagated to memory."""

    model_config = ConfigDict(extra="allow")

    decision_id: UUID
    outcome: DecisionOutcome
    memory_episode_id: str | None = None


class DecisionLogResponse(BaseModel):
    """Serializable response representation for decision audit rows."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: str
    region_id: str
    decision_type: str
    confidence: float
    input_events: dict[str, Any]
    output_action: dict[str, Any]
    human_override: bool
    outcome: str | None
    created_at: datetime


class DecisionAuditService:
    """DB-backed decision audit logger with feedback-to-memory propagation."""

    def __init__(self) -> None:
        self.memory = ZepEpisodicMemory()

    async def create_decision(
        self,
        payload: DecisionLogCreatePayload,
        session: AsyncSession,
    ) -> DecisionLog:
        """Persist a decision audit record."""
        row = DecisionLog(
            project_id=payload.project_id,
            region_id=payload.region_id,
            decision_type=payload.decision_type,
            confidence=payload.confidence,
            input_events=payload.input_events,
            output_action=payload.output_action,
            human_override=payload.human_override,
            outcome=payload.outcome,
        )
        session.add(row)
        await session.commit()
        await session.refresh(row)
        return row

    async def list_decisions(
        self,
        *,
        session: AsyncSession,
        project_id: str | None,
        region_id: str | None,
        limit: int,
        offset: int,
    ) -> tuple[list[DecisionLog], int]:
        """List decision logs with optional project/region filters and pagination."""
        total_stmt = select(func.count()).select_from(DecisionLog)
        data_stmt = select(DecisionLog)

        if project_id:
            total_stmt = total_stmt.where(DecisionLog.project_id == project_id)
            data_stmt = data_stmt.where(DecisionLog.project_id == project_id)

        if region_id:
            total_stmt = total_stmt.where(DecisionLog.region_id == region_id)
            data_stmt = data_stmt.where(DecisionLog.region_id == region_id)

        total = (await session.execute(total_stmt)).scalar_one()

        rows = (
            (
                await session.execute(
                    data_stmt
                    .order_by(DecisionLog.created_at.desc())
                    .limit(limit)
                    .offset(offset)
                )
            )
            .scalars()
            .all()
        )

        return rows, total

    async def apply_feedback(
        self,
        *,
        decision_id: UUID,
        payload: DecisionFeedbackPayload,
        session: AsyncSession,
    ) -> DecisionFeedbackResult | None:
        """Mark a decision as correct/incorrect and push the outcome into episodic memory."""
        stmt = select(DecisionLog).where(DecisionLog.id == decision_id)
        row = (await session.execute(stmt)).scalar_one_or_none()
        if row is None:
            return None

        row.outcome = "correct" if payload.correct else "incorrect"
        row.human_override = payload.human_override

        if payload.notes:
            output_action = dict(row.output_action or {})
            output_action["feedback_notes"] = payload.notes
            row.output_action = output_action

        await session.commit()
        await session.refresh(row)

        episode_id = await self._propagate_feedback_to_memory(row)

        return DecisionFeedbackResult(
            decision_id=row.id,
            outcome="correct" if payload.correct else "incorrect",
            memory_episode_id=episode_id,
        )

    async def _propagate_feedback_to_memory(self, row: DecisionLog) -> str | None:
        """Write a compact feedback episode so future reasoning can learn from outcomes."""
        summary = (
            f"Decision {row.id} for region {row.region_id} was marked {row.outcome}. "
            f"Type={row.decision_type}; confidence={row.confidence:.2f}; "
            f"action={row.output_action}."
        )
        resolution = (
            "Human feedback confirmed this decision as effective"
            if row.outcome == "correct"
            else "Human feedback marked this decision as ineffective"
        )

        try:
            episode = await self.memory.write_resolved_episode(
                region_id=row.region_id,
                severity=self._severity_from_confidence(row.confidence),
                duration_hours=0.0,
                resolution=resolution,
                episode_summary=summary,
            )
        except Exception:
            return None

        return episode.episode_id

    @staticmethod
    def _severity_from_confidence(confidence: float) -> str:
        if confidence >= 0.9:
            return "CRITICAL"
        if confidence >= 0.75:
            return "HIGH"
        if confidence >= 0.5:
            return "MEDIUM"
        return "LOW"


decision_audit_service = DecisionAuditService()
