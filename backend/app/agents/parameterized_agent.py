from __future__ import annotations

import random
from datetime import UTC, datetime
from typing import Any

from app.agents.base_agent import GeoAgent, PerceptionResult
from app.agents.llm_core import ClaudeReasoningCore
from app.agents.memory import ZepEpisodicMemory
from app.feeds.aggregator import FeedAggregator


class ParameterizedGeoAgent(GeoAgent):
    def __init__(
        self,
        config: dict[str, Any],
        llm_client: Any | None = None,
        zep_client: Any | None = None,
        aggregator: FeedAggregator | None = None,
    ) -> None:
        self.config = config
        self.tier = config.get("tier", 3)
        self.specialization = config.get("specialization", "seaport")
        self.key_locations = config.get("key_locations", [])
        self.prompt_weights = config.get("prompt_weights", {})
        self.seasonal_risks = config.get("seasonal_risks", [])
        self.trade_lanes = config.get("trade_lanes", [])
        self.parent_region = config.get("parent_region")

        bbox = config.get("bbox", (0.0, 0.0, 1.0, 1.0))

        super().__init__(
            region_id=config["region_id"],
            region_name=config["region_name"],
            bbox=bbox,
            llm_client=llm_client or ClaudeReasoningCore(),
            zep_client=zep_client or ZepEpisodicMemory(),
            poll_interval_seconds=config.get("poll_interval_seconds", 180),
            aggregator=aggregator,
        )

    def get_system_prompt(self) -> str:
        spec_desc = {
            "seaport": "major seaport logistics node",
            "seaport_cluster": "cluster of major seaports",
            "airport": "international air cargo hub",
            "air_hub": "air cargo hub serving express and freight",
            "chokepoint": "critical maritime chokepoint",
            "rail_hub": "intermodal rail corridor hub",
            "dry_port": "inland dry port and container depot",
            "regional": "regional logistics monitoring zone",
            "terminal": "terminal and logistics facility",
            "logistics_hub": "multi-modal logistics hub",
        }.get(self.specialization, "logistics monitoring node")

        tier_desc = {
            1: "Tier 1 - Regional monitoring zone covering a major trade corridor",
            2: "Tier 2 - Focused monitoring of a {}",
            3: "Tier 3 - Individual monitoring of a {}",
        }.get(self.tier, "Tier 3 - Individual monitoring node")

        locations_str = ", ".join(self.key_locations[:5]) if self.key_locations else "this area"
        risks_str = "; ".join(self.seasonal_risks) if self.seasonal_risks else "none currently flagged"
        lanes_str = "; ".join(self.trade_lanes[:3]) if self.trade_lanes else "local routes"

        tier_fill = f" {spec_desc}" if self.tier > 1 else ""

        prompt = (
            f"You are the {self.region_name} Geo-Agent (ID: {self.region_id}). "
            f"{tier_desc.format(spec_desc) if '{}' in tier_desc else tier_desc}.\n\n"
            f"Coverage: {locations_str}.\n"
            f"Key shipping lanes: {lanes_str}.\n"
            f"Seasonal risks: {risks_str}.\n\n"
            f"Your specialization: {spec_desc}. "
            f"Monitor vessel movements, port conditions, weather events, and geopolitical signals "
            f"relevant to {locations_str}. "
            f"Assess disruptions, estimate confidence, and recommend actions.\n\n"
            f"Respond with structured JSON: severity (LOW/MEDIUM/HIGH/CRITICAL), "
            f"confidence (0.0-1.0), affected_routes, recommended_actions, and reasoning."
        )
        return prompt

    def status_payload(self) -> dict[str, Any]:
        now = datetime.now(UTC)
        tier_mod = self.tier * 0.1
        spec = self.specialization

        spec_baselines: dict[str, dict[str, float]] = {
            "seaport": {"occupancy": 0.0, "rate": 0.0, "risk": 0.0},
            "air_hub": {"occupancy": -10.0, "rate": 30.0, "risk": -5.0},
            "rail_hub": {"occupancy": 5.0, "rate": -20.0, "risk": 5.0},
            "chokepoint": {"occupancy": 15.0, "rate": 25.0, "risk": 10.0},
            "dry_port": {"occupancy": -5.0, "rate": -15.0, "risk": 0.0},
            "regional": {"occupancy": -8.0, "rate": -10.0, "risk": -3.0},
        }
        baseline = spec_baselines.get(spec, {"occupancy": 0.0, "rate": 0.0, "risk": 0.0})

        return {
            "region_id": self.region_id,
            "region_name": self.region_name,
            "tier": self.tier,
            "specialization": self.specialization,
            "parent_region": self.parent_region,
            "running": bool(self._task and not self._task.done()),
            "last_cycle_at": self.last_cycle_at.isoformat() if self.last_cycle_at else None,
            "poll_interval_seconds": self.poll_interval_seconds,
            "confidence_threshold": self.config.get("confidence_threshold", 0.75),
            "last_assessment": self.last_decision,
            "key_locations": self.key_locations,
            "degradation_status": {
                "mode": self.last_degradation_status.mode if self.last_degradation_status else "NORMAL",
                "is_degraded": self.last_degradation_status is not None and self.last_degradation_status.mode != "NORMAL",
                "degraded_connectors": self.last_degradation_status.degraded_connectors if self.last_degradation_status else [],
                "cached_data_age_minutes": self.last_degradation_status.cached_data_age_minutes if self.last_degradation_status else None,
                "uncertainty_factor": self.last_degradation_status.uncertainty_factor if self.last_degradation_status else 0.0,
            } if self.last_degradation_status else None,
            "port_metrics": {
                "port_id": f"{self.region_id}-main",
                "berth_occupancy_pct": round(random.uniform(45.0 + baseline["occupancy"], 85.0 + baseline["occupancy"]), 2),
                "crane_gmph": round(random.uniform(20.0, 35.0), 2),
                "crane_nmph": round(random.uniform(18.0, 30.0), 2),
                "yard_utilization_pct": round(random.uniform(50.0 + baseline["occupancy"], 90.0 + baseline["occupancy"]), 2),
                "truck_turnaround_min": round(random.uniform(25.0, 65.0), 2),
                "reefer_plug_availability_pct": round(random.uniform(70.0, 98.0), 2),
                "dwell_time_import_days": round(random.uniform(2.0, 7.0), 2),
                "dwell_time_export_days": round(random.uniform(1.5, 5.0), 2),
                "timestamp": now,
            },
            "vessel_metrics": {
                "vessel_id": f"{self.region_id}-vessel-pool",
                "ais_vessel_count_expected": random.randint(15, 45),
                "ais_vessel_count_observed": random.randint(12, 42),
                "avg_delay_hours": round(random.uniform(2.0, 18.0), 2),
                "eta_accuracy_pct": round(random.uniform(75.0, 95.0), 2),
                "port_stay_hours": round(random.uniform(24.0, 72.0), 2),
                "timestamp": now,
            },
            "freight_economics": {
                "route_id": f"{self.region_id}-route-main",
                "spot_rate_usd_per_teu": round(random.uniform(800.0 + baseline["rate"] * 10, 3500.0 + baseline["rate"] * 10), 2),
                "baf_usd_per_teu": round(random.uniform(50.0, 300.0), 2),
                "pss_usd_per_teu": round(random.uniform(100.0, 500.0), 2),
                "demurrage_usd_per_day": round(random.uniform(150.0, 600.0), 2),
                "detention_usd_per_day": round(random.uniform(100.0, 400.0), 2),
                "rate_volatility_7d_pct": round(random.uniform(2.0, 25.0), 2),
                "timestamp": now,
            },
            "weather_impact": {
                "region_id": self.region_id,
                "wind_speed_kts": round(random.uniform(5.0, 45.0), 2),
                "wave_height_m": round(random.uniform(0.5, 4.0), 2),
                "visibility_nm": round(random.uniform(2.0, 10.0), 2),
                "canal_draft_m": round(random.uniform(10.0, 16.0), 2),
                "storm_probability_72h": round(random.uniform(0.0, 30.0), 2),
                "water_level_m": round(random.uniform(8.0, 15.0), 2),
                "timestamp": now,
            },
            "risk_signals": {
                "region_id": self.region_id,
                "geopolitical_score_0_100": round(random.uniform(10.0 + baseline["risk"], 60.0 + baseline["risk"]), 2),
                "strike_probability_pct": round(random.uniform(0.0, 15.0), 2),
                "conflict_proximity_km": round(random.uniform(50.0, 500.0), 2),
                "sanctions_status": random.choice(["NONE", "NONE", "WATCH", "ACTIVE"]),
                "port_security_level_marsec": random.choice(["NONE", "LOW", "MEDIUM", "HIGH"]),
                "timestamp": now,
            },
            "inventory_status": {
                "warehouse_id": f"{self.region_id}-warehouse-main",
                "sku_id": "SKU-GLOBAL-001",
                "warehouse_utilization_pct": round(random.uniform(55.0, 92.0), 2),
                "days_of_supply": round(random.uniform(15.0, 45.0), 2),
                "order_fill_rate_pct": round(random.uniform(85.0, 98.0), 2),
                "safety_stock_days": round(random.uniform(5.0, 20.0), 2),
                "timestamp": now,
            },
            "financial_impact": {
                "disruption_id": f"{self.region_id}-disruption-{now.strftime('%Y%m%d')}",
                "estimated_delay_cost_usd_per_day": round(random.uniform(50000.0, 500000.0), 2),
                "reroute_cost_usd": round(random.uniform(100000.0, 1000000.0), 2),
                "recovery_timeline_days": round(random.uniform(3.0, 21.0), 2),
                "timestamp": now,
            },
            "sustainability_metrics": {
                "route_id": f"{self.region_id}-route-main",
                "co2_kg_per_teu_km": round(random.uniform(10.0, 35.0), 2),
                "fuel_type_mix_pct": round(random.uniform(60.0, 95.0), 2),
                "eexi_rating": random.choice(["A", "B", "C", "D"]),
                "cii_rating": random.choice(["A", "B", "C", "D"]),
                "slow_steaming_adoption_pct": round(random.uniform(10.0, 60.0), 2),
                "timestamp": now,
            },
        }