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

import uuid
from datetime import UTC, datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.orchestrator.propagation_model import (
    DisruptionPropagationModel,
    PropagationResult,
    Severity,
    TradeEdge,
)


class ScenarioCategory(str, Enum):
    """Category classification for historical disruption scenarios."""

    CANAL = "CANAL"
    PORT = "PORT"
    WEATHER = "WEATHER"
    GEOPOLITICAL = "GEOPOLITICAL"
    CYBER = "CYBER"
    LABOR = "LABOR"
    PANDEMIC = "PANDEMIC"
    INFRASTRUCTURE = "INFRASTRUCTURE"


class HistoricalScenario(BaseModel):
    """Historical disruption scenario for reference and pattern matching."""

    model_config = ConfigDict(extra="allow")

    scenario_id: str
    name: str
    date_start: datetime
    date_end: datetime
    trigger_region: str
    affected_regions: list[str]
    severity: Severity
    financial_impact_usd: float = Field(ge=0)
    duration_days: float = Field(ge=1, le=365)
    description: str
    cascade_effects: list[str] = Field(default_factory=list)
    mitigation_strategies: list[str] = Field(default_factory=list)
    category: ScenarioCategory
    sources: list[str] = Field(default_factory=list)


class Scenario(BaseModel):
    """A what-if disruption scenario for planning and analysis."""

    model_config = ConfigDict(extra="allow")

    scenario_id: str
    name: str
    trigger_region: str
    severity: Severity
    affected_routes: list[str] = Field(default_factory=list)
    duration_days: float = Field(ge=0.5, le=365)
    created_at: datetime
    propagation_result: PropagationResult | None = None
    mitigation_strategy: str | None = None
    mitigation_reroute_percentage: float | None = None
    mitigation_result: PropagationResult | None = None


class ScenarioCreate(BaseModel):
    """Request body for creating a new scenario."""

    name: str = Field(min_length=3, max_length=200)
    trigger_region: str = Field(min_length=1)
    severity: Severity
    affected_routes: list[str] = Field(default_factory=list)
    duration_days: float = Field(default=1.0, ge=0.5, le=365)


class ScenarioMitigation(BaseModel):
    """Request body for adding mitigation to a scenario."""

    mitigation_strategy: str = Field(min_length=3, max_length=500)
    reroute_percentage: float = Field(default=0.3, ge=0.0, le=1.0)


class ScenarioComparison(BaseModel):
    """Comparison between current impact and mitigated impact."""

    model_config = ConfigDict(extra="allow")

    scenario_id: str
    current_impact: PropagationResult
    mitigated_impact: PropagationResult | None
    improvement: dict[str, Any]
    recommendations: list[str]


class ScenarioStore:
    """In-memory storage for scenarios (can be replaced with DB persistence)."""

    def __init__(self) -> None:
        self._scenarios: dict[str, Scenario] = {}

    def save(self, scenario: Scenario) -> Scenario:
        self._scenarios[scenario.scenario_id] = scenario
        return scenario

    def get(self, scenario_id: str) -> Scenario | None:
        return self._scenarios.get(scenario_id)

    def list(self, limit: int = 50, offset: int = 0) -> list[Scenario]:
        scenarios = sorted(
            self._scenarios.values(),
            key=lambda s: s.created_at,
            reverse=True,
        )
        return scenarios[offset : offset + limit]

    def delete(self, scenario_id: str) -> bool:
        if scenario_id in self._scenarios:
            del self._scenarios[scenario_id]
            return True
        return False


scenario_store = ScenarioStore()


class ScenarioBuilder:
    """Build and analyze what-if disruption scenarios."""

    def __init__(self, edges: list[TradeEdge] | None = None) -> None:
        self.propagation_model = DisruptionPropagationModel(edges=edges)

    def create_scenario(self, request: ScenarioCreate) -> Scenario:
        """Create a new scenario and compute its propagation impact."""
        propagation_result = self.propagation_model.propagate(
            trigger_region=request.trigger_region,
            severity=request.severity,
            max_hops=2,
        )

        scenario = Scenario(
            scenario_id=str(uuid.uuid4()),
            name=request.name,
            trigger_region=request.trigger_region,
            severity=request.severity,
            affected_routes=request.affected_routes,
            duration_days=request.duration_days,
            created_at=datetime.now(UTC),
            propagation_result=propagation_result,
        )

        return scenario_store.save(scenario)

    def add_mitigation(
        self, scenario_id: str, mitigation: ScenarioMitigation
    ) -> Scenario | None:
        """Add mitigation strategy and compute mitigated impact."""
        scenario = scenario_store.get(scenario_id)
        if scenario is None:
            return None

        scenario.mitigation_strategy = mitigation.mitigation_strategy
        scenario.mitigation_reroute_percentage = mitigation.reroute_percentage

        severity_reduction = self._compute_severity_reduction(
            scenario.severity, mitigation.reroute_percentage
        )
        mitigated_severity = self._reduce_severity(
            scenario.severity, severity_reduction
        )

        scenario.mitigation_result = self.propagation_model.propagate(
            trigger_region=scenario.trigger_region,
            severity=mitigated_severity,
            max_hops=2,
        )

        return scenario_store.save(scenario)

    def compare_impact(self, scenario_id: str) -> ScenarioComparison | None:
        """Compare current impact with mitigated impact for a scenario."""
        scenario = scenario_store.get(scenario_id)
        if scenario is None or scenario.propagation_result is None:
            return None

        current = scenario.propagation_result
        mitigated = scenario.mitigation_result

        recommendations = self._generate_recommendations(scenario)

        improvement: dict[str, Any] = {}
        if mitigated:
            improvement = {
                "regions_affected_reduction": len(current.affected_regions)
                - len(mitigated.affected_regions),
                "delay_hours_reduction": round(
                    current.estimated_delay_propagation_hours
                    - mitigated.estimated_delay_propagation_hours,
                    2,
                ),
                "cascade_score_reduction": round(
                    sum(n.cascade_score for n in current.affected_regions)
                    - sum(n.cascade_score for n in mitigated.affected_regions),
                    4,
                ),
                "mitigation_effectiveness": scenario.mitigation_reroute_percentage
                if scenario.mitigation_reroute_percentage
                else 0.0,
            }

        return ScenarioComparison(
            scenario_id=scenario_id,
            current_impact=current,
            mitigated_impact=mitigated,
            improvement=improvement,
            recommendations=recommendations,
        )

    def _compute_severity_reduction(
        self, severity: Severity, reroute_percentage: float
    ) -> float:
        """Compute severity reduction factor based on reroute percentage."""
        base_reduction = reroute_percentage * 0.5
        severity_multipliers = {"LOW": 0.5, "MEDIUM": 0.3, "HIGH": 0.2, "CRITICAL": 0.1}
        return base_reduction * severity_multipliers.get(severity, 0.3)

    def _reduce_severity(self, severity: Severity, reduction: float) -> Severity:
        """Reduce severity level based on reduction factor."""
        severity_order = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
        current_idx = severity_order.index(severity)
        steps = int(reduction * 3)
        new_idx = min(current_idx + steps, len(severity_order) - 1)
        return severity_order[new_idx]  # type: ignore[return-value]

    def _generate_recommendations(self, scenario: Scenario) -> list[str]:
        """Generate actionable recommendations for the scenario."""
        recommendations = []

        if scenario.severity in ("HIGH", "CRITICAL"):
            recommendations.append(
                f"Prioritize {scenario.trigger_region} monitoring. "
                f"Consider activating backup suppliers/routes immediately."
            )

        if scenario.propagation_result:
            if len(scenario.propagation_result.affected_regions) > 2:
                recommendations.append(
                    "Multi-region cascade risk detected. "
                    "Coordinate with downstream partners proactively."
                )

            for region in scenario.propagation_result.affected_regions[:3]:
                if region.delay_hours > 48:
                    recommendations.append(
                        f"{region.region_id}: Estimated delay {region.delay_hours:.0f}h. "
                        f"Consider inventory buffer adjustments."
                    )

        if scenario.mitigation_strategy:
            recommendations.append(f"Mitigation: {scenario.mitigation_strategy}")

        if not recommendations:
            recommendations.append("Monitor situation. No immediate action required.")

        return recommendations


HISTORICAL_SCENARIOS: list[HistoricalScenario] = [
    HistoricalScenario(
        scenario_id="suez-2021-evergiven",
        name="Suez Canal Blockage (Ever Given)",
        date_start=datetime(2021, 3, 23, tzinfo=UTC),
        date_end=datetime(2021, 3, 29, tzinfo=UTC),
        trigger_region="choke_suez",
        affected_regions=["gulf_suez", "europe", "se_asia"],
        severity="CRITICAL",
        financial_impact_usd=9_600_000_000.0,
        duration_days=6.0,
        description=(
            "Ever Given container ship ran aground in the Suez Canal, blocking "
            "~12% of global trade for 6 days. Over 400 vessels queued at both "
            "ends, causing cascading delays across Asia-Europe supply chains."
        ),
        cascade_effects=[
            "400+ vessels delayed at canal approaches",
            "Asia-Europe transit times increased by 10-15 days via Cape of Good Hope",
            "Port congestion at Rotterdam, Singapore, and Jebel Ali",
            "Spot container rates surged 30% within one week",
        ],
        mitigation_strategies=[
            "Emergency dredging and tug operations to refloat vessel",
            "Cape of Good Hope rerouting for queued vessels",
            "Priority scheduling at destination ports to clear backlog",
        ],
        category=ScenarioCategory.CANAL,
        sources=[
            "https://en.wikipedia.org/wiki/2021_Suez_Canal_obstruction",
            "https://www.bbc.com/news/business-56533662",
        ],
    ),
    HistoricalScenario(
        scenario_id="red-sea-houthi-2023",
        name="Red Sea Houthi Attacks on Shipping",
        date_start=datetime(2023, 11, 19, tzinfo=UTC),
        date_end=datetime(2024, 6, 30, tzinfo=UTC),
        trigger_region="choke_bab_el_mandeb",
        affected_regions=["gulf_suez", "europe", "se_asia", "africa"],
        severity="CRITICAL",
        financial_impact_usd=175_000_000_000.0,
        duration_days=224.0,
        description=(
            "Yemen's Houthi forces launched sustained attacks on commercial "
            "vessels in the Red Sea and Bab-el-Mandeb Strait. Suez Canal traffic "
            "dropped 50% year-over-year; major carriers diverted around Africa."
        ),
        cascade_effects=[
            "Suez Canal trade volume dropped 50% YoY in early 2024",
            "Cape of Good Hope transit surged 74% above prior year",
            "Container spot rates tripled on Asia-Europe lanes",
            "10+ day average delivery delays for Europe-bound cargo",
        ],
        mitigation_strategies=[
            "Naval convoy operations (Operation Prosperity Guardian)",
            "Cape of Good Hope rerouting as standard practice",
            "Air freight substitution for high-value cargo",
            "Inventory buffer increases at European distribution centers",
        ],
        category=ScenarioCategory.GEOPOLITICAL,
        sources=[
            "https://www.imf.org/en/blogs/Articles/2024/03/07/red-sea-attacks-disrupt-global-trade",
            "https://www.reuters.com/world/middle-east/houthi-attacks-red-sea-shipping-2024-01-12/",
        ],
    ),
    HistoricalScenario(
        scenario_id="panama-drought-2023",
        name="Panama Canal Drought Restrictions",
        date_start=datetime(2023, 7, 1, tzinfo=UTC),
        date_end=datetime(2024, 3, 31, tzinfo=UTC),
        trigger_region="choke_panama",
        affected_regions=["latin_america", "north_america", "china_ea"],
        severity="HIGH",
        financial_impact_usd=50_000_000_000.0,
        duration_days=274.0,
        description=(
            "El Niño-driven drought reduced Gatun Lake water levels, forcing "
            "Panama Canal Authority to cut daily transits from 36 to 22 vessels. "
            "Draft restrictions reduced maximum cargo per transit by ~25%."
        ),
        cascade_effects=[
            "Daily vessel transits reduced from 36 to 22",
            "Wait times extended to 10+ days for non-reserved slots",
            "US East Coast to Asia routes diverted via Suez or Cape",
            "LNG and grain exports from US Gulf faced significant delays",
        ],
        mitigation_strategies=[
            "Slot reservation auction system for priority transit",
            "Rerouting via Suez Canal for Asia-bound cargo",
            "Water conservation measures at canal locks",
            "Rail intermodal alternatives for US domestic freight",
        ],
        category=ScenarioCategory.CANAL,
        sources=[
            "https://www.imf.org/en/Blogs/Articles/2023/11/15/climate-change-is-disrupting-global-trade",
            "https://www.reuters.com/business/environment/panama-canal-drought-2023-10-30/",
        ],
    ),
    HistoricalScenario(
        scenario_id="baltimore-bridge-2024",
        name="Baltimore Key Bridge Collapse",
        date_start=datetime(2024, 3, 26, tzinfo=UTC),
        date_end=datetime(2024, 6, 10, tzinfo=UTC),
        trigger_region="north_america",
        affected_regions=["north_america", "europe"],
        severity="HIGH",
        financial_impact_usd=4_000_000_000.0,
        duration_days=76.0,
        description=(
            "Container ship Dali struck the Francis Scott Key Bridge, causing "
            "total collapse and blocking the Port of Baltimore. The port handled "
            "record volumes of cars, coal, and agricultural equipment."
        ),
        cascade_effects=[
            "Port of Baltimore fully closed for 11 weeks",
            "Auto imports rerouted to Newark, Savannah, and Norfolk",
            "Coal exports delayed, affecting European energy supply",
            "Construction material supply chains disrupted mid-Atlantic region",
        ],
        mitigation_strategies=[
            "Cargo rerouting to Ports of Newark, Savannah, and Norfolk",
            "Temporary shipping channel cleared for limited traffic",
            "Federal emergency funding for bridge debris removal",
            "Inventory pre-positioning by affected importers",
        ],
        category=ScenarioCategory.INFRASTRUCTURE,
        sources=[
            "https://www.reuters.com/world/us/baltimore-bridge-port-blockade-wont-trigger-new-supply-chain-crisis-experts-say-2024-03-27/",
            "https://en.wikipedia.org/wiki/Francis_Scott_Key_Bridge_collapse",
        ],
    ),
    HistoricalScenario(
        scenario_id="la-lb-congestion-2021",
        name="LA/Long Beach Port Congestion Crisis",
        date_start=datetime(2021, 6, 1, tzinfo=UTC),
        date_end=datetime(2022, 3, 31, tzinfo=UTC),
        trigger_region="cluster_la_longbeach",
        affected_regions=["north_america", "china_ea"],
        severity="HIGH",
        financial_impact_usd=100_000_000_000.0,
        duration_days=303.0,
        description=(
            "Post-COVID demand surge overwhelmed LA/Long Beach port complex. "
            "Peak congestion saw 100+ container ships anchored offshore with "
            "wait times exceeding 2 weeks, crippling US West Coast imports."
        ),
        cascade_effects=[
            "100+ vessels at anchor during peak congestion",
            "Average wait time exceeded 18 days at peak",
            "Warehouse capacity in Southern California at 99% utilization",
            "Retail inventory shortages nationwide through holiday season",
        ],
        mitigation_strategies=[
            "24/7 port operations mandate by White House",
            "Off-dock container staging areas",
            "Rail shuttle services to inland distribution centers",
            "Import diversification to East Coast and Gulf ports",
        ],
        category=ScenarioCategory.PORT,
        sources=[
            "https://www.whitehouse.gov/briefing-room/statements-releases/2021/10/13/fact-sheet-biden-harris-administration-actions-to-address-backlog-at-ports-across-the-country/",
            "https://www.reuters.com/business/us-west-coast-port-congestion-2021-11-01/",
        ],
    ),
    HistoricalScenario(
        scenario_id="semiconductor-shortage-2020",
        name="Global Semiconductor Shortage",
        date_start=datetime(2020, 7, 1, tzinfo=UTC),
        date_end=datetime(2023, 3, 31, tzinfo=UTC),
        trigger_region="china_ea",
        affected_regions=["china_ea", "north_america", "europe", "se_asia", "gulf_suez", "south_asia", "latin_america", "africa"],
        severity="HIGH",
        financial_impact_usd=240_000_000_000.0,
        duration_days=365.0,
        description=(
            "COVID-driven demand shifts, factory shutdowns, and a winter storm "
            "in Texas created a severe global chip shortage. Automotive OEMs "
            "lost an estimated $210B in revenue; electronics supply chains "
            "faced 20+ week lead times."
        ),
        cascade_effects=[
            "Automotive production cut by 7.7M vehicles globally in 2021",
            "Chip lead times extended to 20+ weeks",
            "Consumer electronics prices surged 15-25%",
            "Factory shutdowns at Ford, GM, Toyota, and VW",
        ],
        mitigation_strategies=[
            "Long-term supply agreements with TSMC and Samsung",
            "CHIPS Act funding for domestic semiconductor fabs",
            "Inventory buffering of critical chip types",
            "Product redesign to use available chip alternatives",
        ],
        category=ScenarioCategory.INFRASTRUCTURE,
        sources=[
            "https://www.reuters.com/technology/global-chip-shortage-2021-09-23/",
            "https://en.wikipedia.org/wiki/2020%E2%80%932023_global_chip_shortage",
        ],
    ),
    HistoricalScenario(
        scenario_id="notpetya-2017",
        name="NotPetya Cyberattack on Global Shipping",
        date_start=datetime(2017, 6, 27, tzinfo=UTC),
        date_end=datetime(2017, 7, 7, tzinfo=UTC),
        trigger_region="europe",
        affected_regions=["europe", "north_america", "se_asia", "china_ea", "gulf_suez", "south_asia", "latin_america", "africa"],
        severity="HIGH",
        financial_impact_usd=10_000_000_000.0,
        duration_days=10.0,
        description=(
            "NotPetya ransomware attack crippled Maersk Line's global IT "
            "infrastructure, forcing manual operations at ports worldwide. "
            "Total global damages estimated at $10B across all affected firms."
        ),
        cascade_effects=[
            "Maersk terminal operations halted at 76 ports globally",
            "Manual booking and container tracking for 10+ days",
            "Shipping delays cascaded through Europe and Asia trade lanes",
            "Insurance claims exceeded $3B across affected companies",
        ],
        mitigation_strategies=[
            "Complete IT infrastructure rebuild from scratch",
            "Network segmentation and zero-trust architecture adoption",
            "Offline backup booking and tracking procedures",
            "Industry-wide cybersecurity information sharing (CSO Alliance)",
        ],
        category=ScenarioCategory.CYBER,
        sources=[
            "https://en.wikipedia.org/wiki/NotPetya",
            "https://www.wired.com/story/notpetya-cyberattack-ukraine-russia-code-crashed-the-world/",
        ],
    ),
    HistoricalScenario(
        scenario_id="west-coast-labor-2022",
        name="West Coast Port Labor Dispute (PMA/ILWU)",
        date_start=datetime(2022, 7, 1, tzinfo=UTC),
        date_end=datetime(2023, 7, 1, tzinfo=UTC),
        trigger_region="north_america",
        affected_regions=["north_america", "se_asia", "china_ea"],
        severity="HIGH",
        financial_impact_usd=10_000_000_000.0,
        duration_days=365.0,
        description=(
            "Prolonged contract negotiations between the Pacific Maritime "
            "Association and ILWU created uncertainty at 29 West Coast ports. "
            "Work slowdowns and intermittent stoppages put an estimated $2B/day "
            "in trade at risk, diverting cargo to East Coast and Gulf ports."
        ),
        cascade_effects=[
            "Cargo diversion to East Coast ports increased 30%+",
            "Importers pre-shipped inventory ahead of potential strike",
            "Asia-US West Coast shipping rates spiked on uncertainty",
            "Supply chain planning disrupted by contract negotiation timeline",
        ],
        mitigation_strategies=[
            "Cargo diversification to East Coast and Gulf ports",
            "Early shipment of critical inventory ahead of deadlines",
            "Federal mediation to accelerate contract resolution",
            "Dual-sourcing from Mexico and Canadian port alternatives",
        ],
        category=ScenarioCategory.LABOR,
        sources=[
            "https://www.reuters.com/world/us/west-coast-port-labor-talks-2023-06-01/",
            "https://en.wikipedia.org/wiki/International_Longshore_and_Warehouse_Union",
        ],
    ),
    HistoricalScenario(
        scenario_id="thailand-floods-2011",
        name="Thailand Industrial Floods",
        date_start=datetime(2011, 7, 25, tzinfo=UTC),
        date_end=datetime(2012, 1, 16, tzinfo=UTC),
        trigger_region="se_asia",
        affected_regions=["se_asia", "china_ea", "north_america", "europe"],
        severity="HIGH",
        financial_impact_usd=46_500_000_000.0,
        duration_days=175.0,
        description=(
            "Severe flooding inundated major industrial estates in central "
            "Thailand, destroying hard drive factories and automotive parts "
            "plants. Global HDD prices doubled; Toyota and Honda cut production."
        ),
        cascade_effects=[
            "40% of global HDD production capacity destroyed",
            "HDD prices doubled within weeks",
            "Toyota and Honda cut global output by 200K+ vehicles",
            "Japanese electronics firms relocated production to other ASEAN nations",
        ],
        mitigation_strategies=[
            "Emergency HDD sourcing from alternative manufacturers",
            "Automotive parts dual-sourcing from China and Indonesia",
            "Flood barrier construction at rebuilt industrial estates",
            "Supply chain mapping to identify single-source dependencies",
        ],
        category=ScenarioCategory.WEATHER,
        sources=[
            "https://en.wikipedia.org/wiki/2011_Thailand_floods",
            "https://www.reuters.com/article/us-thailand-floods-idUSTRE7A03JM20111101/",
        ],
    ),
    HistoricalScenario(
        scenario_id="russia-ukraine-2022",
        name="Russia-Ukraine War Supply Chain Disruption",
        date_start=datetime(2022, 2, 24, tzinfo=UTC),
        date_end=datetime(2023, 2, 24, tzinfo=UTC),
        trigger_region="europe",
        affected_regions=["europe", "africa", "south_asia", "gulf_suez"],
        severity="CRITICAL",
        financial_impact_usd=500_000_000_000.0,
        duration_days=365.0,
        description=(
            "Russia's invasion of Ukraine disrupted Black Sea grain corridors, "
            "energy markets, and neon/chip supply chains. Global food prices "
            "hit record highs; European energy costs surged 400%."
        ),
        cascade_effects=[
            "Black Sea grain exports halted for 5 months",
            "Global wheat prices surged 60% in 3 months",
            "European natural gas prices increased 400%",
            "Neon gas shortage (50% of global supply from Ukraine) impacted chip production",
        ],
        mitigation_strategies=[
            "UN-brokered Black Sea Grain Initiative",
            "European LNG import terminal construction",
            "Neon gas production diversification to US and China",
            "Strategic petroleum reserve releases",
        ],
        category=ScenarioCategory.GEOPOLITICAL,
        sources=[
            "https://en.wikipedia.org/wiki/Impact_of_the_Russo-Ukrainian_war_on_global_supply_chains",
            "https://www.reuters.com/world/europe/russia-ukraine-war-supply-chain-impact-2022-03-01/",
        ],
    ),
]
