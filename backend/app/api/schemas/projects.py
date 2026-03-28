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

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


ProjectStatus = Literal["idle", "running", "paused", "completed"]


class ProjectCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    status: ProjectStatus = "idle"
    config: dict[str, Any] = Field(default_factory=dict)


class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    status: ProjectStatus
    created_at: datetime
    config: dict[str, Any]


class EnvelopeMeta(BaseModel):
    total: int | None = None
    limit: int | None = None
    offset: int | None = None


class Envelope(BaseModel):
    data: Any
    error: str | None = None
    meta: EnvelopeMeta | None = None
