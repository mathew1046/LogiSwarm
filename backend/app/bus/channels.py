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
