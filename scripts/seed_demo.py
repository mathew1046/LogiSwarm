#!/usr/bin/env python3
"""
Seed demo data for LogiSwarm demonstration.

Creates:
- Demo project
- Historical disruption episodes (20 per agent)
- Suez 2021 simulation scenario
- Sample shipments crossing affected region
"""

import asyncio
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.db.models import DecisionLog, Project, Shipment


async def create_demo_project(session: AsyncSession) -> Project:
    existing = await session.execute(
        select(Project).where(Project.name == "Demo - Suez 2021")
    )
    if existing.scalar_one_or_none():
        print("Demo project already exists, skipping...")
        return existing.scalar_one_or_none()

    project = Project(
        name="Demo - Suez 2021",
        description="Ever Given grounding simulation - March 2021 Suez Canal blockage",
        regions=["gulf_suez", "europe", "se_asia", "china_ea", "north_america"],
        created_at=datetime.now(UTC),
    )
    session.add(project)
    await session.commit()
    print(f"Created demo project: {project.name}")
    return project


async def seed_historical_disruptions(session: AsyncSession, project: Project) -> None:
    print("Seeding historical disruption episodes...")

    disruptions = [
        {
            "region": "gulf_suez",
            "summary": "Ever Given grounded in Suez Canal, blocking all traffic for 6 days",
            "severity": "CRITICAL",
            "day_offset": 0,
        },
        {
            "region": "europe",
            "summary": "Port congestion at Rotterdam due to delayed Suez arrivals",
            "severity": "HIGH",
            "day_offset": 2,
        },
        {
            "region": "se_asia",
            "summary": "Container backlog at Singapore port affecting 50+ vessels",
            "severity": "MEDIUM",
            "day_offset": 1,
        },
    ]

    for disruption in disruptions:
        for i in range(20):
            log = DecisionLog(
                agent_id=disruption["region"],
                decision_type="assessment",
                payload={
                    "summary": f"Episode {i + 1}: {disruption['summary']}",
                    "severity": disruption["severity"],
                    "probability": 0.7 + (i * 0.01),
                    "confidence": 0.85,
                    "affected_routes": ["Suez Canal", "Asia-Europe"],
                    "actions_recommended": [
                        "Reroute via Cape of Good Hope",
                        "Notify affected shipments",
                        "Reduce port dwell time expectations",
                    ],
                },
                cycle_number=i,
                reasoning_cycle_start=datetime.now(UTC)
                - timedelta(days=30 - disruption["day_offset"]),
                reasoning_cycle_end=datetime.now(UTC)
                - timedelta(days=30 - disruption["day_offset"])
                + timedelta(minutes=5),
                created_at=datetime.now(UTC) - timedelta(days=29 - i),
                project_id=project.id,
            )
            session.add(log)

    await session.commit()
    print("Seeded historical disruption episodes")


async def seed_sample_shipments(session: AsyncSession, project: Project) -> None:
    print("Seeding sample shipments...")

    shipments = [
        {
            "shipment_id": "SUEZ-001",
            "origin": "Shanghai, China",
            "destination": "Rotterdam, Netherlands",
            "carrier": "Maersk",
            "eta": datetime.now(UTC) + timedelta(days=25),
            "status": "rerouted",
            "risk_exposure": 0.92,
        },
        {
            "shipment_id": "SUEZ-002",
            "origin": "Singapore",
            "destination": "Hamburg, Germany",
            "carrier": "MSC",
            "eta": datetime.now(UTC) + timedelta(days=30),
            "status": "delayed",
            "risk_exposure": 0.85,
        },
        {
            "shipment_id": "SUEZ-003",
            "origin": "Busan, South Korea",
            "destination": "Antwerp, Belgium",
            "carrier": "CMA-CGM",
            "eta": datetime.now(UTC) + timedelta(days=28),
            "status": "rerouting_recommended",
            "risk_exposure": 0.78,
        },
        {
            "shipment_id": "SUEZ-004",
            "origin": "Yantian, China",
            "destination": "Genoa, Italy",
            "carrier": "Hapag-Lloyd",
            "eta": datetime.now(UTC) + timedelta(days=22),
            "status": "on_schedule",
            "risk_exposure": 0.65,
        },
        {
            "shipment_id": "SUEZ-005",
            "origin": "Ningbo, China",
            "destination": "Barcelona, Spain",
            "carrier": "Maersk",
            "eta": datetime.now(UTC) + timedelta(days=35),
            "status": "rerouted",
            "risk_exposure": 0.88,
        },
    ]

    for shipment_data in shipments:
        existing = await session.execute(
            select(Shipment).where(Shipment.shipment_id == shipment_data["shipment_id"])
        )
        if existing.scalar_one_or_none():
            continue

        shipment = Shipment(
            shipment_id=shipment_data["shipment_id"],
            origin=shipment_data["origin"],
            destination=shipment_data["destination"],
            carrier=shipment_data["carrier"],
            eta=shipment_data["eta"],
            status=shipment_data["status"],
            route={"type": "sea", "waypoints": []},
            project_id=project.id,
            created_at=datetime.now(UTC),
        )
        session.add(shipment)

    await session.commit()
    print("Seeded sample shipments")


async def main() -> None:
    import os

    database_url = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://logiswarm:logiswarm@localhost:5432/logiswarm",
    )

    engine = create_async_engine(database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    print("=" * 60)
    print("LogiSwarm Demo Data Seeding")
    print("=" * 60)

    async with async_session() as session:
        project = await create_demo_project(session)
        await seed_historical_disruptions(session, project)
        await seed_sample_shipments(session, project)

    print("=" * 60)
    print("Demo data seeding complete!")
    print("=" * 60)

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
