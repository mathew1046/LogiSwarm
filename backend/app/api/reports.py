from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Report
from app.db.session import get_db_session
from app.report.report_agent import report_agent

router = APIRouter(prefix="/reports", tags=["reports"])

SupportedLanguage = Literal["en", "zh", "es", "de", "fr", "ja"]


class ReportCreate(BaseModel):
    """Request body for generating a new report."""

    project_id: str = Field(min_length=1)
    disruption_id: UUID | None = None
    report_type: str = Field(default="post_disruption", max_length=64)
    language: SupportedLanguage = Field(
        default="en", description="Report language: en, zh, es, de, fr, ja"
    )


class ReportResponse(BaseModel):
    """Serializable report response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: str
    disruption_id: UUID | None
    report_type: str
    content: str
    language: str
    generated_at: datetime


class ReportListResponse(BaseModel):
    """Paginated report list response."""

    reports: list[ReportResponse]
    total: int
    limit: int
    offset: int


class ReportEnvelope(BaseModel):
    """Standard API envelope for report endpoints."""

    model_config = ConfigDict(extra="allow")

    data: object
    error: str | None = None
    meta: dict[str, Any] | None = None


@router.post("", response_model=ReportEnvelope)
async def generate_report(
    payload: ReportCreate,
    session: AsyncSession = Depends(get_db_session),
) -> ReportEnvelope:
    """Generate a new post-disruption analysis report in the specified language."""
    language = (
        payload.language
        if payload.language in ("en", "zh", "es", "de", "fr", "ja")
        else "en"
    )

    content = await report_agent.generate_report(
        project_id=payload.project_id,
        disruption_id=payload.disruption_id
        or UUID("00000000-0000-0000-0000-000000000000"),
        session=session,
        language=language,
    )

    record = Report(
        project_id=payload.project_id,
        disruption_id=payload.disruption_id,
        report_type=payload.report_type,
        content=content,
        language=language,
    )
    session.add(record)
    await session.commit()
    await session.refresh(record)

    return ReportEnvelope(
        data=_report_to_response(record),
        error=None,
        meta={"generated": True, "language": language},
    )


@router.get("", response_model=ReportEnvelope)
async def list_reports(
    project_id: str | None = Query(default=None),
    disruption_id: UUID | None = Query(default=None),
    report_type: str | None = Query(default=None),
    language: str | None = Query(default=None, description="Filter by language code"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_db_session),
) -> ReportEnvelope:
    """List reports with optional filtering."""
    total_stmt = select(func.count()).select_from(Report)
    data_stmt = select(Report)

    if project_id:
        total_stmt = total_stmt.where(Report.project_id == project_id)
        data_stmt = data_stmt.where(Report.project_id == project_id)

    if disruption_id:
        total_stmt = total_stmt.where(Report.disruption_id == disruption_id)
        data_stmt = data_stmt.where(Report.disruption_id == disruption_id)

    if report_type:
        total_stmt = total_stmt.where(Report.report_type == report_type)
        data_stmt = data_stmt.where(Report.report_type == report_type)

    if language:
        total_stmt = total_stmt.where(Report.language == language)
        data_stmt = data_stmt.where(Report.language == language)

    total = (await session.execute(total_stmt)).scalar_one()

    rows = (
        (
            await session.execute(
                data_stmt.order_by(Report.generated_at.desc())
                .limit(limit)
                .offset(offset)
            )
        )
        .scalars()
        .all()
    )

    responses = [_report_to_response(row) for row in rows]

    return ReportEnvelope(
        data=ReportListResponse(
            reports=responses,
            total=total,
            limit=limit,
            offset=offset,
        ),
        error=None,
        meta=None,
    )


@router.get("/latest", response_model=ReportEnvelope)
async def get_latest_report(
    project_id: str = Query(...),
    session: AsyncSession = Depends(get_db_session),
) -> ReportEnvelope:
    """Get the latest report for a project."""
    stmt = (
        select(Report)
        .where(Report.project_id == project_id)
        .order_by(Report.generated_at.desc())
        .limit(1)
    )
    result = await session.execute(stmt)
    record = result.scalar_one_or_none()

    if record is None:
        raise HTTPException(status_code=404, detail="No reports found for project")

    return ReportEnvelope(data=_report_to_response(record), error=None, meta=None)


@router.get("/{report_id}", response_model=ReportEnvelope)
async def get_report(
    report_id: UUID,
    session: AsyncSession = Depends(get_db_session),
) -> ReportEnvelope:
    """Get full report content by ID."""
    record = await session.get(Report, report_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Report not found")

    return ReportEnvelope(data=_report_to_response(record), error=None, meta=None)


def _report_to_response(record: Report) -> ReportResponse:
    """Convert Report model to ReportResponse."""
    return ReportResponse(
        id=record.id,
        project_id=record.project_id,
        disruption_id=record.disruption_id,
        report_type=record.report_type,
        content=record.content,
        language=record.language,
        generated_at=record.generated_at,
    )
