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

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class TransportMode(str, Enum):
    SEA = "sea"
    AIR = "air"
    RAIL = "rail"


@dataclass
class TransportNode:
    node_id: str
    name: str
    node_type: str
    lat: float
    lon: float
    modes: list[TransportMode]

    def can_handle(self, mode: TransportMode) -> bool:
        return mode in self.modes


@dataclass
class TransportEdge:
    source: str
    target: str
    mode: TransportMode
    distance_km: float
    base_cost: float
    time_hours: float
    reliability: float


@dataclass
class ModeTransfer:
    location: str
    from_mode: TransportMode
    to_mode: TransportMode
    transfer_time_hours: float
    transfer_cost: float
    handling_requirements: list[str]


MULTIMODAL_NODES: dict[str, TransportNode] = {
    "shanghai": TransportNode(
        "shanghai",
        "Shanghai",
        "port",
        31.2,
        121.5,
        [TransportMode.SEA, TransportMode.AIR],
    ),
    "singapore": TransportNode(
        "singapore",
        "Singapore",
        "port",
        1.3,
        103.8,
        [TransportMode.SEA, TransportMode.AIR],
    ),
    "rotterdam": TransportNode(
        "rotterdam",
        "Rotterdam",
        "port",
        51.9,
        4.5,
        [TransportMode.SEA, TransportMode.AIR, TransportMode.RAIL],
    ),
    "hamburg": TransportNode(
        "hamburg",
        "Hamburg",
        "port",
        53.5,
        10.0,
        [TransportMode.SEA, TransportMode.AIR, TransportMode.RAIL],
    ),
    "los_angeles": TransportNode(
        "los_angeles",
        "Los Angeles",
        "port",
        33.7,
        -118.3,
        [TransportMode.SEA, TransportMode.AIR, TransportMode.RAIL],
    ),
    "dubai": TransportNode(
        "dubai", "Dubai", "port", 25.3, 55.3, [TransportMode.SEA, TransportMode.AIR]
    ),
    "frankfurt": TransportNode(
        "frankfurt",
        "Frankfurt",
        "airport",
        50.0,
        8.6,
        [TransportMode.AIR, TransportMode.RAIL],
    ),
    "chicago": TransportNode(
        "chicago",
        "Chicago",
        "hub",
        41.9,
        -87.6,
        [TransportMode.AIR, TransportMode.RAIL],
    ),
    "chengdu": TransportNode(
        "chengdu",
        "Chengdu",
        "hub",
        30.7,
        104.1,
        [TransportMode.AIR, TransportMode.RAIL],
    ),
}


MODE_SPEEDS: dict[TransportMode, float] = {
    TransportMode.SEA: 25.0,
    TransportMode.AIR: 900.0,
    TransportMode.RAIL: 120.0,
}

MODE_COST_MULTIPLIERS: dict[TransportMode, float] = {
    TransportMode.SEA: 1.0,
    TransportMode.AIR: 5.0,
    TransportMode.RAIL: 2.0,
}

MODE_RELIABILITY: dict[TransportMode, float] = {
    TransportMode.SEA: 0.92,
    TransportMode.AIR: 0.98,
    TransportMode.RAIL: 0.95,
}


def build_multimodal_graph() -> dict[str, list[dict[str, Any]]]:
    graph: dict[str, list[dict[str, Any]]] = {
        node_id: [] for node_id in MULTIMODAL_NODES
    }

    sea_routes = [
        ("shanghai", "singapore", 2900),
        ("shanghai", "rotterdam", 10500),
        ("shanghai", "los_angeles", 10500),
        ("singapore", "rotterdam", 8300),
        ("singapore", "dubai", 3600),
        ("rotterdam", "hamburg", 350),
        ("los_angeles", "chicago", 2800),
        ("dubai", "rotterdam", 5500),
        ("dubai", "singapore", 3600),
    ]

    for source, target, distance_km in sea_routes:
        if source in graph and target in graph:
            time_hours = distance_km / MODE_SPEEDS[TransportMode.SEA]
            cost = distance_km * MODE_COST_MULTIPLIERS[TransportMode.SEA] * 0.001
            reliability = MODE_RELIABILITY[TransportMode.SEA]
            graph[source].append(
                {
                    "target": target,
                    "mode": TransportMode.SEA,
                    "distance_km": distance_km,
                    "cost": cost,
                    "time": time_hours,
                    "reliability": reliability,
                }
            )

    air_routes = [
        ("shanghai", "frankfurt", 8800),
        ("shanghai", "los_angeles", 10500),
        ("shanghai", "chengdu", 1600),
        ("singapore", "frankfurt", 10300),
        ("frankfurt", "rotterdam", 350),
        ("frankfurt", "hamburg", 400),
        ("frankfurt", "chicago", 7000),
        ("los_angeles", "chicago", 2800),
        ("chengdu", "frankfurt", 8000),
    ]

    for source, target, distance_km in air_routes:
        if source in graph and target in graph:
            time_hours = distance_km / MODE_SPEEDS[TransportMode.AIR]
            cost = distance_km * MODE_COST_MULTIPLIERS[TransportMode.AIR] * 0.001
            reliability = MODE_RELIABILITY[TransportMode.AIR]
            graph[source].append(
                {
                    "target": target,
                    "mode": TransportMode.AIR,
                    "distance_km": distance_km,
                    "cost": cost,
                    "time": time_hours,
                    "reliability": reliability,
                }
            )

    rail_routes = [
        ("rotterdam", "hamburg", 380),
        ("hamburg", "frankfurt", 390),
        ("frankfurt", "chengdu", 9500),
        ("chengdu", "shanghai", 1650),
        ("chicago", "los_angeles", 3000),
    ]

    for source, target, distance_km in rail_routes:
        if source in graph and target in graph:
            time_hours = distance_km / MODE_SPEEDS[TransportMode.RAIL]
            cost = distance_km * MODE_COST_MULTIPLIERS[TransportMode.RAIL] * 0.001
            reliability = MODE_RELIABILITY[TransportMode.RAIL]
            graph[source].append(
                {
                    "target": target,
                    "mode": TransportMode.RAIL,
                    "distance_km": distance_km,
                    "cost": cost,
                    "time": time_hours,
                    "reliability": reliability,
                }
            )

    return graph


MULTIMODAL_GRAPH = build_multimodal_graph()


def get_available_modes(origin: str, destination: str) -> list[list[TransportMode]]:
    origin_node = MULTIMODAL_NODES.get(origin)
    dest_node = MULTIMODAL_NODES.get(destination)

    if not origin_node or not dest_node:
        return []

    origin_modes = set(origin_node.modes)
    dest_modes = set(dest_node.modes)

    if origin_modes & dest_modes:
        return [[mode] for mode in (origin_modes & dest_modes)]

    valid_combinations = []

    for origin_mode in origin_modes:
        for dest_mode in dest_modes:
            valid_combinations.append([origin_mode, dest_mode])

    return valid_combinations
