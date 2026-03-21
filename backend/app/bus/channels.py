ALERT_CHANNEL_TEMPLATE = "agent.{region_id}.alert"
BROADCAST_CHANNEL_TEMPLATE = "agent.{region_id}.broadcast"
ORCHESTRATOR_CASCADE_CHANNEL = "orchestrator.cascade"
ORCHESTRATOR_REROUTE_CHANNEL = "orchestrator.reroute"


def alert_channel(region_id: str) -> str:
    """Build the per-region alert channel name."""
    return ALERT_CHANNEL_TEMPLATE.format(region_id=region_id)


def broadcast_channel(region_id: str) -> str:
    """Build the per-region broadcast channel name."""
    return BROADCAST_CHANNEL_TEMPLATE.format(region_id=region_id)
