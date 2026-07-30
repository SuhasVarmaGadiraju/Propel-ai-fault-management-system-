#!/usr/bin/env python3
"""
Database Seeding Script for Electrical Distribution Network Domain Models.

Generates:
- 3 Feeders (11kV lines)
- 15 Transformers (5 per feeder)
- ~850 Poles across 15 transformers (~50-60 poles per transformer)
- Radial topology with parent-child pole chains for 40% of transformers
- 60% of transformers with unknown topology (parent_pole_id=None, seq_on_line=None)
- ~9% of poles without IoT devices (device_installed=False)
- ~91% of poles with physical IoT Devices attached
"""

import sys
import os
import random
import logging
from datetime import datetime, timezone

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app import create_app
from app.database import db
from app.models import (
    Feeder, FeederStatus,
    Transformer, TransformerStatus,
    Pole, PoleStatus, PoleType,
    Device, DeviceStatus
)

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] [%(levelname)s]: %(message)s")
logger = logging.getLogger("seed_database")


def seed_database():
    app = create_app(os.getenv("FLASK_ENV", "development"))
    with app.app_context():
        logger.info("Initializing database tables...")
        db.create_all()

        # Check if database is already seeded
        if Feeder.query.first() is not None:
            logger.info("Database is already seeded. Clearing existing data...")
            db.session.query(Device).delete()
            db.session.query(Pole).delete()
            db.session.query(Transformer).delete()
            db.session.query(Feeder).delete()
            db.session.commit()

        logger.info("Seeding Feeders...")
        feeders = [
            Feeder(
                feeder_code="FDR-HYD-NORTH-01",
                name="North Zone 11kV Feeder Line A",
                status=FeederStatus.ACTIVE,
                description="Primary radial line servicing North Hyderabad residential sector"
            ),
            Feeder(
                feeder_code="FDR-HYD-CENTRAL-02",
                name="Central Zone 11kV Feeder Line B",
                status=FeederStatus.ACTIVE,
                description="High-density commercial radial line servicing Central Tech Park"
            ),
            Feeder(
                feeder_code="FDR-HYD-SOUTH-03",
                name="South Zone 11kV Feeder Line C",
                status=FeederStatus.ACTIVE,
                description="Industrial sector 11kV feeder line servicing South Industrial Hub"
            ),
        ]
        db.session.add_all(feeders)
        db.session.commit()
        logger.info(f"Created {len(feeders)} Feeders.")

        logger.info("Seeding Transformers...")
        base_coords = [
            (17.3850, 78.4866),  # North
            (17.4401, 78.3489),  # Central
            (17.3616, 78.4747),  # South
        ]

        transformers = []
        trf_counter = 1
        for feeder_idx, feeder in enumerate(feeders):
            lat_base, lng_base = base_coords[feeder_idx]
            for t_num in range(1, 6):  # 5 transformers per feeder = 15 total
                trf_code = f"TRF-{feeder.feeder_code.split('-')[2]}-{t_num:02d}"
                # 40% known topology (indices 1 & 2), 60% unknown topology (indices 3, 4, 5)
                trf = Transformer(
                    transformer_code=trf_code,
                    feeder_id=feeder.id,
                    latitude=lat_base + (t_num * 0.005) + random.uniform(-0.001, 0.001),
                    longitude=lng_base + (t_num * 0.005) + random.uniform(-0.001, 0.001),
                    capacity_kva=random.choice([100.0, 160.0, 250.0, 500.0]),
                    households_served=random.randint(20, 120),
                    status=TransformerStatus.ACTIVE
                )
                transformers.append(trf)
                trf_counter += 1

        db.session.add_all(transformers)
        db.session.commit()
        logger.info(f"Created {len(transformers)} Transformers across 3 Feeders.")

        logger.info("Seeding Poles (~850 total) & Devices...")
        total_poles = 0
        total_devices = 0

        # Mark 40% of transformers (6 out of 15) as having known radial topology
        # 60% of transformers (9 out of 15) will have NULL topology (parent_pole_id=None, seq_on_line=None)
        known_topology_trf_ids = {trf.id for idx, trf in enumerate(transformers) if idx % 5 in (0, 1)}

        firmware_versions = ["1.0.0", "1.1.2", "1.2.0", "2.0.1"]
        wards = [f"Ward-{w}" for w in range(1, 16)]
        pincodes = ["500001", "500032", "500081", "500084", "500090"]

        for trf_idx, trf in enumerate(transformers):
            num_poles_for_trf = random.randint(52, 60)  # ~56 poles * 15 = ~840-850 poles
            has_known_topology = trf.id in known_topology_trf_ids

            parent_pole_obj = None
            seq_counter = 1

            for p_idx in range(1, num_poles_for_trf + 1):
                pole_code = f"POL-{trf.transformer_code.replace('TRF-', '')}-{p_idx:03d}"

                # Topology assignment:
                if has_known_topology:
                    seq_on_line = seq_counter
                    # Branch lines logic: ~10% of poles branch off an earlier parent pole
                    if p_idx > 3 and random.random() < 0.10 and parent_pole_obj:
                        parent_id = parent_pole_obj.parent_pole_id or parent_pole_obj.id
                    else:
                        parent_id = parent_pole_obj.id if parent_pole_obj else None
                    seq_counter += 1
                else:
                    # 60% of transformers have UNKNOWN topology
                    parent_id = None
                    seq_on_line = None

                # Device installation assignment (~9% without device, ~91% with device)
                device_installed = random.random() >= 0.09
                device_code = f"DEV-MAC-{trf_idx:02d}-{p_idx:03d}" if device_installed else None

                pole = Pole(
                    pole_code=pole_code,
                    transformer_id=trf.id,
                    feeder_id=trf.feeder_id,
                    parent_pole_id=parent_id,
                    seq_on_line=seq_on_line,
                    latitude=trf.latitude + (p_idx * 0.0003) + random.uniform(-0.0001, 0.0001),
                    longitude=trf.longitude + (p_idx * 0.0003) + random.uniform(-0.0001, 0.0001),
                    ward=random.choice(wards),
                    pincode=random.choice(pincodes),
                    pole_type=PoleType.TRANSFORMER_POLE if p_idx == 1 else (PoleType.JUNCTION if (has_known_topology and parent_id and random.random() < 0.15) else PoleType.SUSPENSION),
                    device_installed=device_installed,
                    current_device_id=device_code,
                    status=PoleStatus.ACTIVE
                )
                db.session.add(pole)
                db.session.flush()  # Obtain pole.id for relationship

                # Create physical Device object if device_installed is True
                if device_installed:
                    device = Device(
                        device_id=device_code,
                        pole_id=pole.id,
                        firmware_version=random.choice(firmware_versions),
                        battery_mv=random.randint(3600, 4200),
                        last_rssi=random.randint(-85, -50),
                        installed_at=datetime.now(timezone.utc),
                        active=True,
                        status=DeviceStatus.ACTIVE
                    )
                    db.session.add(device)
                    total_devices += 1

                if has_known_topology:
                    parent_pole_obj = pole

                total_poles += 1

        db.session.commit()

        # Verification statistics
        unknown_topology_poles = Pole.query.filter(Pole.parent_pole_id.is_(None), Pole.seq_on_line.is_(None)).count()
        no_device_poles = Pole.query.filter(Pole.device_installed.is_(False)).count()

        logger.info("======================================================")
        logger.info("         DATABASE SEEDING COMPLETED SUCCESSFULLY      ")
        logger.info("======================================================")
        logger.info(f"✓ Total Feeders Created      : {Feeder.query.count()}")
        logger.info(f"✓ Total Transformers Created : {Transformer.query.count()}")
        logger.info(f"✓ Total Poles Created        : {total_poles}")
        logger.info(f"✓ Total IoT Devices Created  : {total_devices}")
        logger.info(f"✓ Poles without Devices (~9%): {no_device_poles} ({no_device_poles/total_poles*100:.1f}%)")
        logger.info(f"✓ Unknown Topology Poles (~60%): {unknown_topology_poles} ({unknown_topology_poles/total_poles*100:.1f}%)")
        logger.info("======================================================")


if __name__ == "__main__":
    seed_database()
