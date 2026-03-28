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

from typing import Any, Generic, List, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    model_config = ConfigDict(extra="allow")

    data: List[T]
    next_cursor: Optional[str] = None
    total: int
    has_more: bool = False


class PaginationParams(BaseModel):
    limit: int = Field(default=20, ge=1, le=100)
    cursor: Optional[str] = None


def encode_cursor(cursor_data: dict[str, Any]) -> str:
    import base64
    import json

    json_str = json.dumps(cursor_data, sort_keys=True)
    encoded = base64.urlsafe_b64encode(json_str.encode()).decode()
    return encoded


def decode_cursor(cursor: str) -> Optional[dict[str, Any]]:
    if not cursor:
        return None

    import base64
    import json

    try:
        json_bytes = base64.urlsafe_b64decode(cursor.encode())
        return json.loads(json_bytes)
    except Exception:
        return None


def get_pagination_offset(
    cursor: Optional[str], default_limit: int = 20
) -> tuple[int, int, Optional[dict[str, Any]]]:
    decoded = decode_cursor(cursor) if cursor else None

    if decoded:
        offset = decoded.get("offset", 0)
        limit = decoded.get("limit", default_limit)
        return offset, limit, decoded

    return 0, default_limit, None


def build_next_cursor(
    current_offset: int, limit: int, total_count: int
) -> Optional[str]:
    next_offset = current_offset + limit

    if next_offset >= total_count:
        return None

    return encode_cursor({"offset": next_offset, "limit": limit})


def paginate_list(
    items: List[T], limit: int = 20, cursor: Optional[str] = None
) -> PaginatedResponse[T]:
    offset, effective_limit, _ = get_pagination_offset(cursor, default_limit=limit)

    total = len(items)
    paginated_items = items[offset : offset + effective_limit]

    next_cursor = build_next_cursor(offset, effective_limit, total)
    has_more = (offset + effective_limit) < total

    return PaginatedResponse[T](
        data=paginated_items,
        next_cursor=next_cursor,
        total=total,
        has_more=has_more,
    )
