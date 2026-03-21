from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.projects import Envelope, EnvelopeMeta, ProjectCreateRequest, ProjectResponse
from app.db.models import Project
from app.db.session import get_db_session

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("", response_model=Envelope)
async def create_project(
    payload: ProjectCreateRequest,
    session: AsyncSession = Depends(get_db_session),
) -> Envelope:
    project = Project(name=payload.name, status=payload.status, config=payload.config)
    session.add(project)
    await session.commit()
    await session.refresh(project)

    return Envelope(data=ProjectResponse.model_validate(project), error=None, meta=None)


@router.get("/{project_id}", response_model=Envelope)
async def get_project(
    project_id: UUID,
    session: AsyncSession = Depends(get_db_session),
) -> Envelope:
    result = await session.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    return Envelope(data=ProjectResponse.model_validate(project), error=None, meta=None)


@router.get("", response_model=Envelope)
async def list_projects(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_db_session),
) -> Envelope:
    total_stmt = select(func.count()).select_from(Project)
    total = (await session.execute(total_stmt)).scalar_one()

    stmt = select(Project).order_by(Project.created_at.desc()).limit(limit).offset(offset)
    projects = (await session.execute(stmt)).scalars().all()

    return Envelope(
        data=[ProjectResponse.model_validate(project) for project in projects],
        error=None,
        meta=EnvelopeMeta(total=total, limit=limit, offset=offset),
    )
