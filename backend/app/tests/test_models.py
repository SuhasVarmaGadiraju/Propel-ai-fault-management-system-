import pytest
import uuid
from app import create_app
from app.database import db
from app.models import (
    Feeder, FeederStatus,
    Transformer, TransformerStatus,
    Pole, PoleStatus, PoleType,
    Device, DeviceStatus,
    Telemetry, TelemetryEvent
)


@pytest.fixture
def test_app():
    """Create testing app configured with SQLite in-memory database."""
    app = create_app("testing")
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


def test_models_and_relationships(test_app):
    """Test entity creation, foreign keys, self-referential relationships, and nullable topology."""
    with test_app.app_context():
        # 1. Create Feeder
        feeder = Feeder(
            feeder_code="FDR-TEST-01",
            name="Feeder 1 Test",
            status=FeederStatus.ACTIVE,
            description="Test feeder line"
        )
        db.session.add(feeder)
        db.session.commit()
        assert feeder.id is not None

        # 2. Create Transformer
        trf = Transformer(
            transformer_code="TRF-TEST-01-A",
            feeder_id=feeder.id,
            latitude=17.3850,
            longitude=78.4866,
            capacity_kva=250.0,
            households_served=45,
            status=TransformerStatus.ACTIVE
        )
        db.session.add(trf)
        db.session.commit()
        assert trf.feeder.feeder_code == "FDR-TEST-01"

        # 3. Create Parent Pole (Root of radial topology)
        parent_pole = Pole(
            pole_code="POL-TEST-001",
            transformer_id=trf.id,
            feeder_id=feeder.id,
            parent_pole_id=None,  # Root pole has no parent
            seq_on_line=1,
            latitude=17.3851,
            longitude=78.4867,
            ward="Ward 10",
            pincode="500001",
            pole_type=PoleType.TRANSFORMER_POLE,
            device_installed=True,
            status=PoleStatus.ACTIVE
        )
        db.session.add(parent_pole)
        db.session.commit()

        # 4. Create Child Pole connected to Parent Pole
        child_pole = Pole(
            pole_code="POL-TEST-002",
            transformer_id=trf.id,
            feeder_id=feeder.id,
            parent_pole_id=parent_pole.id,  # Linked to parent pole
            seq_on_line=2,
            latitude=17.3855,
            longitude=78.4870,
            ward="Ward 10",
            pincode="500001",
            pole_type=PoleType.SUSPENSION,
            device_installed=True,
            status=PoleStatus.ACTIVE
        )
        db.session.add(child_pole)
        db.session.commit()

        # 5. Create Unknown Topology Pole (60% case: parent_pole_id=None, seq_on_line=None)
        unknown_top_pole = Pole(
            pole_code="POL-TEST-003",
            transformer_id=trf.id,
            feeder_id=feeder.id,
            parent_pole_id=None,
            seq_on_line=None,
            latitude=17.3860,
            longitude=78.4875,
            device_installed=False,
            status=PoleStatus.ACTIVE
        )
        db.session.add(unknown_top_pole)
        db.session.commit()

        # 6. Create Device
        device = Device(
            device_id="DEV-MAC-TEST-01",
            pole_id=child_pole.id,
            firmware_version="1.2.0",
            battery_mv=3800,
            last_rssi=-65,
            active=True,
            status=DeviceStatus.ACTIVE
        )
        db.session.add(device)
        db.session.commit()

        # Verify self-referential relationships
        assert len(parent_pole.children_poles) == 1
        assert parent_pole.children_poles[0].pole_code == "POL-TEST-002"
        assert child_pole.parent_pole.pole_code == "POL-TEST-001"

        # Verify device relationship
        assert child_pole.device.device_id == "DEV-MAC-TEST-01"
        assert device.pole.pole_code == "POL-TEST-002"

        # Verify unknown topology fields are NULL
        assert unknown_top_pole.parent_pole_id is None
        assert unknown_top_pole.seq_on_line is None
        assert unknown_top_pole.device_installed is False
        assert unknown_top_pole.device is None

        # Verify transformer relationship backpopulates
        assert len(trf.poles) == 3
