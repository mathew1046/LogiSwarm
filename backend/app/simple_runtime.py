from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from itertools import islice
from typing import Any
from uuid import uuid4


@dataclass(frozen=True)
class Place:
    id: str
    name: str
    lat: float
    lon: float
    region: str


PLACES: list[Place] = [
    Place("shanghai", "Shanghai", 31.2304, 121.4737, "East Asia"),
    Place("singapore", "Singapore", 1.3521, 103.8198, "Southeast Asia"),
    Place("mumbai", "Mumbai", 19.0760, 72.8777, "South Asia"),
    Place("dubai", "Dubai", 25.2048, 55.2708, "Gulf"),
    Place("suez", "Suez", 29.9668, 32.5498, "Suez Corridor"),
    Place("rotterdam", "Rotterdam", 51.9244, 4.4777, "Europe"),
    Place("hamburg", "Hamburg", 53.5511, 9.9937, "Europe"),
    Place("lagos", "Lagos", 6.5244, 3.3792, "West Africa"),
    Place("panama", "Panama City", 8.9824, -79.5199, "Latin America"),
    Place("los_angeles", "Los Angeles", 34.0522, -118.2437, "North America"),
]

PLACE_INDEX = {place.id: place for place in PLACES}
PLACE_OPTIONS = [{"id": place.id, "name": place.name, "region": place.region} for place in PLACES]

GRAPH: dict[str, list[str]] = {
    "shanghai": ["singapore", "los_angeles"],
    "singapore": ["shanghai", "mumbai", "suez", "los_angeles"],
    "mumbai": ["singapore", "dubai", "suez"],
    "dubai": ["mumbai", "suez", "lagos"],
    "suez": ["singapore", "mumbai", "dubai", "rotterdam", "hamburg", "lagos"],
    "rotterdam": ["suez", "hamburg", "lagos", "panama"],
    "hamburg": ["suez", "rotterdam"],
    "lagos": ["dubai", "suez", "rotterdam", "panama"],
    "panama": ["lagos", "rotterdam", "los_angeles"],
    "los_angeles": ["shanghai", "singapore", "panama"],
}

WEATHER_BY_PLACE = {
    "shanghai": "Heavy cloud cover with moderate port wind.",
    "singapore": "Humid tropical conditions with intermittent rain.",
    "mumbai": "Monsoon pressure building with rough coastal swells.",
    "dubai": "Hot desert air with stable visibility.",
    "suez": "Dry canal corridor with occasional sand haze.",
    "rotterdam": "Cool Atlantic front with mild berth delays.",
    "hamburg": "Light river fog and slow inbound handling.",
    "lagos": "Thunderstorm activity causing intermittent congestion.",
    "panama": "Canal humidity high with reduced slot reliability.",
    "los_angeles": "Clear weather but inland trucking pressure rising.",
}

NEWS_BY_PLACE = {
    "shanghai": "Export volume remains elevated after factory rebound.",
    "singapore": "Regional transshipment demand remains above baseline.",
    "mumbai": "Dock labor overtime approved to clear cargo backlog.",
    "dubai": "Fuel uplift costs increased across Gulf carriers.",
    "suez": "Canal queues are stable but convoy spacing is tight.",
    "rotterdam": "European inland rail handoff remains constrained.",
    "hamburg": "Terminal handling windows are shorter than normal.",
    "lagos": "Customs processing times are slightly above average.",
    "panama": "Transit bookings remain sensitive to water restrictions.",
    "los_angeles": "Intermodal ramp utilization remains elevated.",
}


def _base_risk(place_id: str) -> float:
    base = {
        "shanghai": 0.34,
        "singapore": 0.28,
        "mumbai": 0.42,
        "dubai": 0.36,
        "suez": 0.61,
        "rotterdam": 0.31,
        "hamburg": 0.33,
        "lagos": 0.47,
        "panama": 0.52,
        "los_angeles": 0.38,
    }
    return base.get(place_id, 0.4)


def _severity(score: float) -> str:
    if score >= 0.75:
        return "CRITICAL"
    if score >= 0.55:
        return "HIGH"
    if score >= 0.35:
        return "MEDIUM"
    return "LOW"


def _path_cost(path: list[str]) -> float:
    total = 0.0
    for idx, place_id in enumerate(path):
        total += _base_risk(place_id) + idx * 0.08
    return round(total, 3)


def _path_eta_hours(path: list[str]) -> float:
    return round((len(path) - 1) * 18.0 + sum(_base_risk(place_id) * 8 for place_id in path), 2)


def _candidate_paths(origin: str, destination: str, max_depth: int = 6) -> list[list[str]]:
    results: list[list[str]] = []

    def dfs(node: str, target: str, visited: list[str]) -> None:
        if len(visited) > max_depth:
            return
        if node == target:
            results.append(visited[:])
            return
        for neighbor in GRAPH.get(node, []):
            if neighbor in visited:
                continue
            dfs(neighbor, target, [*visited, neighbor])

    dfs(origin, destination, [origin])
    results.sort(key=lambda path: (len(path), _path_cost(path)))
    return list(islice(results, 3))


class SimpleRuntime:
    def __init__(self) -> None:
        self.current_shipment: dict[str, Any] | None = None
        self.current_route_plan: dict[str, Any] | None = None
        self.current_simulation: dict[str, Any] | None = None
        self.reports: list[dict[str, Any]] = []

    def _agent_snapshot(self, place_id: str) -> dict[str, Any]:
        place = PLACE_INDEX[place_id]
        risk = _base_risk(place_id)

        if self.current_simulation and self.current_simulation.get("status") == "active":
            active_path = self.current_simulation.get("path", [])
            if place_id in active_path:
                risk = min(risk + 0.18, 0.95)

        return {
            "agent_id": f"agent-{place.id}",
            "place_id": place.id,
            "place_name": place.name,
            "region": place.region,
            "lat": place.lat,
            "lon": place.lon,
            "weather": WEATHER_BY_PLACE[place.id],
            "news": NEWS_BY_PLACE[place.id],
            "risk_score": round(risk, 2),
            "severity": _severity(risk),
            "reasoning": (
                f"{place.name} agent sees weather: {WEATHER_BY_PLACE[place.id]} "
                f"News: {NEWS_BY_PLACE[place.id]} This yields a {_severity(risk).lower()} risk posture."
            ),
            "neighbors": GRAPH.get(place.id, []),
        }

    def get_agents(self) -> list[dict[str, Any]]:
        return [self._agent_snapshot(place.id) for place in PLACES]

    def get_agent_topology(self) -> dict[str, Any]:
        nodes = [
            {
                "id": place.id,
                "label": place.name,
                "region": place.region,
                "lat": place.lat,
                "lon": place.lon,
                "risk_score": self._agent_snapshot(place.id)["risk_score"],
                "severity": self._agent_snapshot(place.id)["severity"],
            }
            for place in PLACES
        ]
        edges = []
        seen: set[tuple[str, str]] = set()
        for source, targets in GRAPH.items():
            for target in targets:
                ordered = sorted((source, target))
                key: tuple[str, str] = (ordered[0], ordered[1])
                if key in seen:
                    continue
                seen.add(key)
                edges.append({"source": source, "target": target})
        return {"nodes": nodes, "edges": edges}

    def set_shipment(self, origin: str, destination: str) -> dict[str, Any]:
        shipment = {
            "shipment_id": str(uuid4()),
            "origin": origin,
            "destination": destination,
            "origin_name": PLACE_INDEX[origin].name,
            "destination_name": PLACE_INDEX[destination].name,
            "updated_at": datetime.now(UTC).isoformat(),
        }
        self.current_shipment = shipment
        return shipment

    def get_shipment(self) -> dict[str, Any] | None:
        return self.current_shipment

    def compute_routes(self, origin: str, destination: str) -> dict[str, Any]:
        paths = _candidate_paths(origin, destination)
        if not paths:
            raise ValueError("No available route between selected places")

        route_options: list[dict[str, Any]] = []
        for index, path in enumerate(paths, start=1):
            agent_reasoning = []
            intercommunication = []
            aggregate_risk = 0.0

            for i, place_id in enumerate(path):
                agent = self._agent_snapshot(place_id)
                aggregate_risk += agent["risk_score"]
                agent_reasoning.append(
                    {
                        "agent_id": agent["agent_id"],
                        "place_id": place_id,
                        "place_name": agent["place_name"],
                        "risk_score": agent["risk_score"],
                        "severity": agent["severity"],
                        "weather": agent["weather"],
                        "news": agent["news"],
                        "reasoning": agent["reasoning"],
                    }
                )
                if i < len(path) - 1:
                    intercommunication.append(
                        {
                            "from": place_id,
                            "to": path[i + 1],
                            "message": (
                                f"{PLACE_INDEX[place_id].name} shares {_severity(agent['risk_score']).lower()} risk, "
                                f"advising {PLACE_INDEX[path[i + 1]].name} to adjust route confidence accordingly."
                            ),
                        }
                    )

            option = {
                "route_id": f"route-option-{index}",
                "name": f"Route Option {index}",
                "path": path,
                "waypoints": [PLACE_INDEX[place_id].name for place_id in path],
                "coordinates": [[PLACE_INDEX[place_id].lon, PLACE_INDEX[place_id].lat] for place_id in path],
                "estimated_hours": _path_eta_hours(path),
                "risk_score": round(aggregate_risk / len(path), 2),
                "estimated_cost_index": round(1.0 + _path_cost(path), 2),
                "agent_reasoning": agent_reasoning,
                "intercommunication": intercommunication,
            }
            route_options.append(option)

        best_option = min(route_options, key=lambda option: (option["risk_score"], option["estimated_hours"]))
        recommendation = {
            "recommended_route_id": best_option["route_id"],
            "recommended_route": best_option,
            "alternatives": route_options,
            "summary": (
                f"The 10 agents prefer {best_option['name']} because it balances lower aggregate risk "
                f"({best_option['risk_score']}) with acceptable travel time ({best_option['estimated_hours']}h)."
            ),
            "generated_at": datetime.now(UTC).isoformat(),
        }
        self.current_route_plan = recommendation
        return recommendation

    def start_simulation(self) -> dict[str, Any]:
        if self.current_shipment is None:
            raise ValueError("No shipment configured")
        if self.current_route_plan is None:
            self.compute_routes(self.current_shipment["origin"], self.current_shipment["destination"])
        if self.current_route_plan is None:
            raise ValueError("No route plan available")

        chosen = self.current_route_plan["recommended_route"]
        now = datetime.now(UTC)
        self.current_simulation = {
            "simulation_id": str(uuid4()),
            "status": "active",
            "phase": "starting",
            "shipment": self.current_shipment,
            "route": chosen,
            "path": chosen["path"],
            "started_at": now.isoformat(),
            "stopped_at": None,
            "manual_stop": False,
        }
        return self.get_simulation_status()

    def stop_simulation(self) -> dict[str, Any]:
        if self.current_simulation is None:
            return {"status": "idle"}
        if self.current_shipment is None:
            return {"status": "idle"}

        self.current_simulation["status"] = "stopped"
        self.current_simulation["phase"] = "stopped"
        self.current_simulation["stopped_at"] = datetime.now(UTC).isoformat()
        self.current_simulation["manual_stop"] = True

        report = {
            "report_id": str(uuid4()),
            "title": f"Simulation Report: {self.current_shipment['origin_name']} → {self.current_shipment['destination_name']}",
            "created_at": datetime.now(UTC).isoformat(),
            "shipment": self.current_shipment,
            "route": self.current_route_plan["recommended_route"] if self.current_route_plan else None,
            "simulation": self.get_simulation_status(),
        }
        self.reports.insert(0, report)
        return self.get_simulation_status()

    def get_simulation_status(self) -> dict[str, Any]:
        if self.current_simulation is None:
            return {"status": "idle", "changes": [], "metrics": {}, "reports_count": len(self.reports)}

        sim = self.current_simulation
        started_at = datetime.fromisoformat(sim["started_at"])
        elapsed_seconds = max((datetime.now(UTC) - started_at).total_seconds(), 0)
        path = sim["path"]
        progress_steps = min(int(elapsed_seconds // 4), len(path)) if sim["status"] == "active" else len(path)

        changes = []
        for index, place_id in enumerate(path[:progress_steps], start=1):
            changes.append(
                {
                    "step": index,
                    "place_id": place_id,
                    "place_name": PLACE_INDEX[place_id].name,
                    "change": f"{PLACE_INDEX[place_id].name} traffic and risk posture updated from agent signals.",
                    "severity": self._agent_snapshot(place_id)["severity"],
                }
            )

        progress = round((progress_steps / max(len(path), 1)) * 100, 1)
        phase = "propagating" if progress_steps < len(path) and sim["status"] == "active" else ("monitoring" if sim["status"] == "active" else "stopped")
        sim["phase"] = phase

        metrics = {
            "progress_percent": progress,
            "active_agents": progress_steps,
            "impacted_places": progress_steps,
            "route_risk_score": sim["route"]["risk_score"],
            "estimated_hours": sim["route"]["estimated_hours"],
            "estimated_cost_index": sim["route"]["estimated_cost_index"],
        }

        return {
            "simulation_id": sim["simulation_id"],
            "status": sim["status"],
            "phase": sim["phase"],
            "started_at": sim["started_at"],
            "stopped_at": sim["stopped_at"],
            "shipment": sim["shipment"],
            "route": sim["route"],
            "changes": changes,
            "metrics": metrics,
            "reports_count": len(self.reports),
        }

    def get_reports(self) -> list[dict[str, Any]]:
        return self.reports


simple_runtime = SimpleRuntime()
