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

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Extra, Field


class PortMetrics(BaseModel):
    """Port operational metrics."""

    model_config = ConfigDict(extra=Extra.allow)

    port_id: str
    berth_occupancy_pct: float = Field(ge=0.0, le=100.0)
    crane_gmph: float = Field(ge=0.0)
    crane_nmph: float = Field(ge=0.0)
    yard_utilization_pct: float = Field(ge=0.0, le=100.0)
    truck_turnaround_min: float = Field(ge=0.0)
    reefer_plug_availability_pct: float = Field(ge=0.0, le=100.0)
    dwell_time_import_days: float = Field(ge=0.0)
    dwell_time_export_days: float = Field(ge=0.0)
    timestamp: datetime


class VesselMetrics(BaseModel):
    """Vessel tracking and performance metrics."""

    model_config = ConfigDict(extra=Extra.allow)

    vessel_id: str
    ais_vessel_count_expected: int = Field(ge=0)
    ais_vessel_count_observed: int = Field(ge=0)
    avg_delay_hours: float = Field(ge=0.0)
    eta_accuracy_pct: float = Field(ge=0.0, le=100.0)
    port_stay_hours: float = Field(ge=0.0)
    timestamp: datetime


class FreightEconomics(BaseModel):
    """Freight pricing and economics data for routes."""

    model_config = ConfigDict(extra=Extra.allow)

    route_id: str
    spot_rate_usd_per_teu: float = Field(ge=0.0)
    baf_usd_per_teu: float = Field(ge=0.0)
    pss_usd_per_teu: float = Field(ge=0.0)
    demurrage_usd_per_day: float = Field(ge=0.0)
    detention_usd_per_day: float = Field(ge=0.0)
    rate_volatility_7d_pct: float = Field(ge=0.0, le=100.0)
    timestamp: datetime


class WeatherImpact(BaseModel):
    """Weather conditions and their impact on operations."""

    model_config = ConfigDict(extra=Extra.allow)

    region_id: str
    wind_speed_kts: float = Field(ge=0.0, le=200.0)
    wave_height_m: float = Field(ge=0.0, le=30.0)
    visibility_nm: float = Field(ge=0.0, le=20.0)
    canal_draft_m: float = Field(ge=0.0)
    storm_probability_72h: float = Field(ge=0.0, le=100.0)
    water_level_m: float = Field(ge=0.0)
    timestamp: datetime


class RiskSignals(BaseModel):
    """Risk assessment signals for a region."""

    model_config = ConfigDict(extra=Extra.allow)

    region_id: str
    geopolitical_score_0_100: float = Field(ge=0.0, le=100.0)
    strike_probability_pct: float = Field(ge=0.0, le=100.0)
    conflict_proximity_km: float = Field(ge=0.0)
    sanctions_status: Literal["NONE", "WATCH", "ACTIVE", "SEVERE"]
    port_security_level_marsec: Literal["NONE", "LOW", "MEDIUM", "HIGH", "EXCLUSIVE"]
    timestamp: datetime


class InventoryStatus(BaseModel):
    """Inventory levels and status for warehouses."""

    model_config = ConfigDict(extra=Extra.allow)

    warehouse_id: str
    sku_id: str
    warehouse_utilization_pct: float = Field(ge=0.0, le=100.0)
    days_of_supply: float = Field(ge=0.0)
    order_fill_rate_pct: float = Field(ge=0.0, le=100.0)
    safety_stock_days: float = Field(ge=0.0)
    timestamp: datetime


class FinancialImpact(BaseModel):
    """Financial impact calculations for disruptions."""

    model_config = ConfigDict(extra=Extra.allow)

    disruption_id: str
    estimated_delay_cost_usd_per_day: float = Field(ge=0.0)
    reroute_cost_usd: float = Field(ge=0.0)
    recovery_timeline_days: float = Field(ge=0.0)
    timestamp: datetime


class SustainabilityMetrics(BaseModel):
    """Environmental and sustainability metrics for routes."""

    model_config = ConfigDict(extra=Extra.allow)

    route_id: str
    co2_kg_per_teu_km: float = Field(ge=0.0)
    fuel_type_mix_pct: float = Field(ge=0.0, le=100.0)
    eexi_rating: str
    cii_rating: str
    slow_steaming_adoption_pct: float = Field(ge=0.0, le=100.0)
    timestamp: datetime