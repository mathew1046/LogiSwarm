from fastapi import APIRouter, Query

from app.api.schemas.feeds import FeedHealthResponse
from app.api.schemas.projects import Envelope, EnvelopeMeta
from app.feeds.aggregator import FeedAggregator

router = APIRouter(prefix="/feeds", tags=["feeds"])
aggregator = FeedAggregator()


@router.get("/health", response_model=Envelope)
async def get_feed_health(
    region_id: str = Query(default="se_asia", min_length=1),
) -> Envelope:
    """Return feed connector health with degradation detection and event counts."""
    health = await aggregator.get_connectors_health(region_id=region_id, lookback_minutes=60)

    return Envelope(
        data=[FeedHealthResponse.model_validate(item) for item in health],
        error=None,
        meta=EnvelopeMeta(total=len(health), limit=len(health), offset=0),
    )
