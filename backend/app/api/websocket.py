from __future__ import annotations

import asyncio
import json
import logging
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)

router = APIRouter(tags=["websocket"])


class ConnectionManager:
    """Manage WebSocket connections for real-time updates."""

    def __init__(self) -> None:
        self.active_connections: dict[str, list[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, project_id: str) -> None:
        await websocket.accept()
        async with self._lock:
            if project_id not in self.active_connections:
                self.active_connections[project_id] = []
            self.active_connections[project_id].append(websocket)
        logger.info(f"WebSocket connected for project {project_id}")

    async def disconnect(self, websocket: WebSocket, project_id: str) -> None:
        async with self._lock:
            if project_id in self.active_connections:
                try:
                    self.active_connections[project_id].remove(websocket)
                    if not self.active_connections[project_id]:
                        del self.active_connections[project_id]
                except ValueError:
                    pass
        logger.info(f"WebSocket disconnected for project {project_id}")

    async def broadcast(
        self, project_id: str, message_type: str, data: dict[str, Any]
    ) -> int:
        """Broadcast a message to all connections for a project."""
        message = {
            "type": message_type,
            "data": data,
            "timestamp": datetime.now(UTC).isoformat(),
        }
        message_json = json.dumps(message)

        async with self._lock:
            connections = self.active_connections.get(project_id, []).copy()

        disconnected: list[WebSocket] = []
        sent_count = 0

        for connection in connections:
            try:
                await connection.send_text(message_json)
                sent_count += 1
            except Exception as exc:
                logger.warning(f"Failed to send WebSocket message: {exc}")
                disconnected.append(connection)

        for conn in disconnected:
            await self.disconnect(conn, project_id)

        return sent_count

    async def broadcast_global(self, message_type: str, data: dict[str, Any]) -> int:
        """Broadcast a message to all connected clients."""
        total_sent = 0
        async with self._lock:
            project_ids = list(self.active_connections.keys())

        for project_id in project_ids:
            sent = await self.broadcast(project_id, message_type, data)
            total_sent += sent

        return total_sent

    def get_connection_count(self, project_id: str | None = None) -> int:
        """Get the number of active connections."""
        if project_id:
            return len(self.active_connections.get(project_id, []))
        return sum(len(conns) for conns in self.active_connections.values())


manager = ConnectionManager()


@router.websocket("/ws/agents/{project_id}")
async def websocket_agent_updates(websocket: WebSocket, project_id: str) -> None:
    """
    WebSocket endpoint for real-time agent updates.

    Message types:
    - agent_pulse: Periodic heartbeat with agent status (every 30s)
    - disruption_alert: Immediate alert when detected
    - route_update: Route recommendation updates
    - eta_update: Predictive ETA changes
    """
    await manager.connect(websocket, project_id)
    pulse_interval = 30

    try:
        pulse_task = asyncio.create_task(
            _send_agent_pulse(websocket, project_id, interval_seconds=pulse_interval)
        )

        while True:
            try:
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=60.0,
                )
                try:
                    message = json.loads(data)
                    await _handle_client_message(websocket, project_id, message)
                except json.JSONDecodeError:
                    await websocket.send_json(
                        {
                            "type": "error",
                            "data": {"message": "Invalid JSON message"},
                            "timestamp": datetime.now(UTC).isoformat(),
                        }
                    )
            except asyncio.TimeoutError:
                pass

    except WebSocketDisconnect:
        pass
    except Exception as exc:
        logger.error(f"WebSocket error for project {project_id}: {exc}")
    finally:
        pulse_task.cancel()
        try:
            await pulse_task
        except asyncio.CancelledError:
            pass
        await manager.disconnect(websocket, project_id)


async def _send_agent_pulse(
    websocket: WebSocket, project_id: str, interval_seconds: int = 30
) -> None:
    """Send periodic agent pulse messages to keep connection alive."""
    from app.orchestrator.orchestrator import swarm_orchestrator

    while True:
        try:
            await asyncio.sleep(interval_seconds)

            risk_map = swarm_orchestrator.get_global_risk_map()
            agent_count = len(risk_map)

            pulse_data = {
                "project_id": project_id,
                "agent_count": agent_count,
                "risk_map": risk_map,
                "connection_count": manager.get_connection_count(project_id),
            }

            await websocket.send_json(
                {
                    "type": "agent_pulse",
                    "data": pulse_data,
                    "timestamp": datetime.now(UTC).isoformat(),
                }
            )

        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.warning(f"Agent pulse send failed: {exc}")
            raise


async def _handle_client_message(
    websocket: WebSocket, project_id: str, message: dict[str, Any]
) -> None:
    """Handle incoming client messages over WebSocket."""
    message_type = message.get("type")

    if message_type == "ping":
        await websocket.send_json(
            {
                "type": "pong",
                "data": {"project_id": project_id},
                "timestamp": datetime.now(UTC).isoformat(),
            }
        )
    elif message_type == "subscribe":
        channels = message.get("channels", [])
        await websocket.send_json(
            {
                "type": "subscribed",
                "data": {"channels": channels, "project_id": project_id},
                "timestamp": datetime.now(UTC).isoformat(),
            }
        )
    else:
        await websocket.send_json(
            {
                "type": "error",
                "data": {"message": f"Unknown message type: {message_type}"},
                "timestamp": datetime.now(UTC).isoformat(),
            }
        )


async def broadcast_disruption_alert(
    project_id: str,
    region_id: str,
    severity: str,
    confidence: float,
    reasoning: str,
    affected_routes: list[str],
) -> None:
    """Broadcast a disruption alert to all connected clients."""
    await manager.broadcast(
        project_id=project_id,
        message_type="disruption_alert",
        data={
            "region_id": region_id,
            "severity": severity,
            "confidence": confidence,
            "reasoning": reasoning,
            "affected_routes": affected_routes,
        },
    )


async def broadcast_route_update(
    project_id: str,
    shipment_id: str,
    predicted_eta: str,
    delay_hours: float,
    disrupted_regions: list[str],
) -> None:
    """Broadcast a route/ETA update to all connected clients."""
    await manager.broadcast(
        project_id=project_id,
        message_type="route_update",
        data={
            "shipment_id": shipment_id,
            "predicted_eta": predicted_eta,
            "delay_hours": delay_hours,
            "disrupted_regions": disrupted_regions,
        },
    )


async def broadcast_global_disruption(
    region_id: str,
    severity: str,
    confidence: float,
    reasoning: str,
) -> None:
    """Broadcast a disruption alert to all projects."""
    await manager.broadcast_global(
        message_type="disruption_alert",
        data={
            "region_id": region_id,
            "severity": severity,
            "confidence": confidence,
            "reasoning": reasoning,
        },
    )
