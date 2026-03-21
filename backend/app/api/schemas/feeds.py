from datetime import datetime

from pydantic import BaseModel


class FeedHealthResponse(BaseModel):
    connector: str
    status: str
    last_successful_fetch: datetime | None
    last_latency_ms: float | None
    event_count_last_hour: int
    poll_interval_seconds: int
