import os
import random
import logging
from datetime import datetime, timezone
from app.database import db
from app.models import (
    Feeder, FeederStatus,
    Transformer, TransformerStatus,
    Pole, PoleStatus, PoleType,
    Device, DeviceStatus
)

logger = logging.getLogger("init_db")


def init_db(app):
    """
    Idempotent database schema initialization.
    Uses a PostgreSQL advisory lock when running against PostgreSQL to prevent
    concurrent DDL race conditions (e.g. duplicate key errors on ENUM creation)
    when multiple Gunicorn worker processes start up.
    """
    with app.app_context():
        engine = db.engine
        dialect_name = engine.dialect.name
        if dialect_name == "postgresql":
            with engine.connect() as conn:
                conn.execute(db.text("SELECT pg_advisory_lock(987654321);"))
                try:
                    db.create_all()
                    conn.commit()
                finally:
                    conn.execute(db.text("SELECT pg_advisory_unlock(987654321);"))
                    conn.commit()
        else:
            db.create_all()


def seed_database_if_empty(app):
    """
    Seeds initial grid topology data if database contains no Feeders.
    """
    with app.app_context():
        init_db(app)
        if Feeder.query.first() is not None:
            logger.info("Database already contains records. Skipping seed.")
            return

        logger.info("Seeding initial grid topology data...")
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

        base_coords = [
            (17.3850, 78.4866),
            (17.4401, 78.3489),
            (17.3616, 78.4747),
        ]

        transformers = []
        for feeder_idx, feeder in enumerate(feeders):
            lat_base, lng_base = base_coords[feeder_idx]
            for t_num in range(1, 6):
                trf_code = f"TRF-{feeder.feeder_code.split('-')[2]}-{t_num:02d}"
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

        db.session.add_all(transformers)
        db.session.commit()

        known_topology_trf_ids = {trf.id for idx, trf in enumerate(transformers) if idx % 5 in (0, 1)}
        firmware_versions = ["1.0.0", "1.1.2", "1.2.0", "2.0.1"]
        wards = [f"Ward-{w}" for w in range(1, 16)]
        pincodes = ["500001", "500032", "500081", "500084", "500090"]

        total_poles = 0
        total_devices = 0

        for trf_idx, trf in enumerate(transformers):
            num_poles_for_trf = random.randint(52, 60)
            has_known_topology = trf.id in known_topology_trf_ids

            parent_pole_obj = None
            seq_counter = 1

            for p_idx in range(1, num_poles_for_trf + 1):
                pole_code = f"POL-{trf.transformer_code.replace('TRF-', '')}-{p_idx:03d}"

                if has_known_topology:
                    seq_on_line = seq_counter
                    if p_idx > 3 and random.random() < 0.10 and parent_pole_obj:
                        parent_id = parent_pole_obj.parent_pole_id or parent_pole_obj.id
                    else:
                        parent_id = parent_pole_obj.id if parent_pole_obj else None
                    seq_counter += 1
                else:
                    parent_id = None
                    seq_on_line = None

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
                db.session.flush()

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
        logger.info(f"Database seeded successfully with {total_poles} poles and {total_devices} devices.")


if __name__ == "__main__":
    from app import create_app
    app = create_app()
    seed_database_if_empty(app)
