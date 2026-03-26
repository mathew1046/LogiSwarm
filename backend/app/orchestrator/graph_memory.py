from __future__ import annotations

import logging
import re
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger(__name__)


class GraphEntity(BaseModel):
    """Extracted entity from a disruption event."""

    model_config = ConfigDict(extra="allow")

    name: str = Field(min_length=1)
    entity_type: str
    relevance: float = Field(ge=0.0, le=1.0)


class GraphRelationship(BaseModel):
    """Relationship between two entities."""

    model_config = ConfigDict(extra="allow")

    source: str
    target: str
    relationship_type: str
    weight: float = Field(ge=0.0, le=1.0)
    context: str = ""


class GraphMemoryUpdate(BaseModel):
    """Result of a graph memory update operation."""

    model_config = ConfigDict(extra="allow")

    region_id: str
    disruption_id: str
    nodes_added: int
    edges_added: int
    entities: list[GraphEntity]
    relationships: list[GraphRelationship]
    propagated_to: list[str]
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class GraphMemoryExtractor:
    """Extract entities and relationships from disruption events for graph memory updates."""

    ENTITY_PATTERNS: dict[str, list[str]] = {
        "port": [
            r"(?i)\b(rotterdam|hamburg|antwerp|singapore|shanghai|ningbo|busan|los\s*angeles|long\s*beach|"
            r"hong\s*kong|dubai|felixstowe|bremen|houston|new\s*york|charleston|oakland|tokyo|yokohama|tianjin|"
            r"qingdao|guangzhou|shenzhen|tanjung\s*priok|laem\s*chabang|caImporto|colombo|durban|cape\s*town)\b"
        ],
        "vessel": [
            r"(?i)\b(vessel|ship|container\s*ship|tanker|bulk\s*carrier|ferry|barge)\s*[A-Za-z]{{2,}}\d*\b",
            r"(?i)\bM[V|S|V]\s*[A-Za-z]{{2,}}\b",
        ],
        "chokepoint": [
            r"(?i)\b(suez\s*canal|panama\s*canal|strait\s*of\s*malacca|bab\s*el\s*mandeb|bosporus|dardanelles|"
            r"strait\s*of\s*hormuz|cape\s*of\s*good\s*hope|english\s*channel| Singapore\s*strait)\b"
        ],
        "weather": [
            r"(?i)\b(typhoon|hurricane|cyclone|storm|monsoon|fog|blizzard|heatwave|drought|flood)\b"
        ],
        "event_type": [
            r"(?i)\b(strike|blockade|closure|congestion|accident|explosion|fire|grounding|collision|"
            r"piracy|sanction|war|conflict|labor\s*dispute|equipment\s*failure)"
        ],
        "commodity": [
            r"(?i)\b(oil|gas|coal|grain|wheat|corn|soy|rice|steel|iron|ore|container|automobile|electronics|"
            r"pharmaceuticals|chemicals|fertilizer|coffee|tea)"
        ],
    }

    RELATIONSHIP_TYPES: dict[str, str] = {
        "caused": "caused_by",
        "delayed": "delayed",
        "rerouted": "rerouted_via",
        "affected": "affected",
        "impacted": "impacted",
        "disrupted": "disrupted",
        "blocked": "blocked",
        "closed": "closed",
    }

    def __init__() -> None:
        pass

    def extract_entities(
        self, disruption_text: str, region_id: str
    ) -> list[GraphEntity]:
        """Extract all known entity types from disruption text."""
        entities: list[GraphEntity] = []
        text = str(disruption_text or "")

        for entity_type, patterns in self.ENTITY_PATTERNS.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text)
                for match in matches:
                    name = match.group(0).strip().title()[:100]
                    if name and not any(e.name == name for e in entities):
                        entities.append(
                            GraphEntity(
                                name=name,
                                entity_type=entity_type,
                                relevance=self._calculate_relevance(match, text),
                            )
                        )

        return entities

    def extract_relationships(
        self, entities: list[GraphEntity], disruption_summary: str
    ) -> list[GraphRelationship]:
        """Derive relationships between entities based on disruption context."""
        relationships: list[GraphRelationship] = []
        summary = str(disruption_summary or "").lower()

        for rel_keyword, rel_type in self.RELATIONSHIP_TYPES.items():
            if rel_keyword in summary:
                for i, source in enumerate(entities):
                    for target in entities[i + 1 :]:
                        if source.entity_type != target.entity_type:
                            relationships.append(
                                GraphRelationship(
                                    source=source.name,
                                    target=target.name,
                                    relationship_type=rel_type,
                                    weight=0.7,
                                    context=disruption_summary[:200],
                                )
                            )

        return relationships

    def _calculate_relevance(self, match: re.Match, text: str) -> float:
        """Calculate relevance score based on position and context."""
        pos = match.start()
        text_len = max(len(text), 1)
        rel_score = 1.0 - (pos / text_len) * 0.3
        return min(1.0, rel_score)


class GraphMemoryManager:
    """Manage graph memory updates and propagation to neighboring agents."""

    def __init__(self):
        self.extractor = GraphMemoryExtractor()
        self._graph_updates: dict[str, list[GraphMemoryUpdate]] = {}

    async def update_graph_on_resolution(
        self,
        region_id: str,
        disruption_id: str,
        disruption_text: str,
        resolution_summary: str,
        neighbor_regions: list[str] | None = None,
    ) -> GraphMemoryUpdate:
        """Update graph memory when a disruption is resolved."""
        full_text = f"{disruption_text} {resolution_summary}"
        entities = self.extractor.extract_entities(full_text, region_id)
        relationships = self.extractor.extract_relationships(
            entities, resolution_summary
        )

        nodes_added = len(entities)
        edges_added = len(relationships)

        update = GraphMemoryUpdate(
            region_id=region_id,
            disruption_id=disruption_id,
            nodes_added=nodes_added,
            edges_added=edges_added,
            entities=entities,
            relationships=relationships,
            propagated_to=neighbor_regions or [],
        )

        if region_id not in self._graph_updates:
            self._graph_updates[region_id] = []
        self._graph_updates[region_id].append(update)

        logger.info(
            f"Graph memory updated: added {nodes_added} nodes, {edges_added} edges for region {region_id}"
        )

        return update

    def get_region_graph_updates(
        self, region_id: str, limit: int = 10
    ) -> list[GraphMemoryUpdate]:
        """Retrieve recent graph updates for a region."""
        updates = self._graph_updates.get(region_id, [])
        return updates[-limit:]

    def get_neighbor_context(
        self, region_id: str, neighbor_ids: list[str]
    ) -> list[dict[str, Any]]:
        """Get graph context updates from neighboring agents."""
        context: list[dict[str, Any]] = []

        for neighbor_id in neighbor_ids:
            updates = self.get_region_graph_updates(neighbor_id, limit=3)
            for update in updates:
                context.append(
                    {
                        "region_id": update.region_id,
                        "disruption_id": update.disruption_id,
                        "entities": [e.model_dump() for e in update.entities],
                        "relationships": [r.model_dump() for r in update.relationships],
                        "updated_at": update.updated_at.isoformat(),
                    }
                )

        return context


graph_memory_manager = GraphMemoryManager()
