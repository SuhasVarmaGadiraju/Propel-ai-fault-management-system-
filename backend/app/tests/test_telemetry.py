import pytest
from datetime import datetime, timezone
from app import create_app
from app.database import db
from app.models import Feeder, Transformer, Pole, Device, Telemetry, FeederStatus, TransformerStatus, PoleStatus, DeviceStatus, TelemetryEvent


@pytest.fixture
def app_with_device():
    """Fixture providing a test Flask app with seeded Pole and Device."""
    app = create_app("testing")
    with app.app_context():
        db.create_all()

        feeder = Feeder(feeder_code="FDR-TEL-01", name="Tel Feeder", status=FeederStatus.ACTIVE)
        db.session.add(feeder)
        db.session.flush()

        trf = Transformer(transformer_code="TRF-TEL-01", feeder_id=feeder.id, latitude=17.44, longitude=78.38)
        db.session.add(trf)
        db.session.flush()

        pole = Pole(
            pole_code="P-024431",
            transformer_id=trf.id,
            feeder_id=feeder.id,
            latitude=17.4401,
            longitude=78.3801,
            device_installed=True,
            status=PoleStatus.ACTIVE
        )
        db.session.add(pole)
        db.session.flush()

        device = Device(
            device_id="KSPDB-SD07-D0112-4431",
            pole_id=pole.id,
            firmware_version="1.4.2",
            active=True,
            status=DeviceStatus.ACTIVE
        )
        db.session.add(device)
        db.session.commit()

        yield app

        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app_with_device):
    return app_with_device.test_client()


def test_single_telemetry_ingestion(client):
    """Test ingesting a single valid telemetry payload matching assignment format."""
    payload = {
        "device_id": "KSPDB-SD07-D0112-4431",
        "pole_id": "P-024431",
        "event": "power_lost",
        "energized": False,
        "ts": "2026-07-29T02:14:07.412Z",
        "seq": 100,
        "battery_mv": 3480,
        "rssi": -91,
        "fw": "1.4.2"
    }
    response = client.post("/api/v1/telemetry", json=payload)
    assert response.status_code == 201
    data = response.get_json()
    assert data["status"] == "success"
    assert data["out_of_order"] is False

    # Verify device state updated
    with client.application.app_context():
        dev = Device.query.filter_by(device_id="KSPDB-SD07-D0112-4431").first()
        assert dev.last_sequence == 100
        assert dev.energized is False
        assert dev.last_event == "power_lost"
        assert dev.battery_mv == 3480
        assert dev.last_rssi == -91


def test_duplicate_telemetry_detection(client):
    """Test at-least-once delivery duplicate detection using (device_id, sequence_number)."""
    payload = {
        "device_id": "KSPDB-SD07-D0112-4431",
        "pole_id": "P-024431",
        "event": "heartbeat",
        "energized": True,
        "ts": "2026-07-29T02:15:00.000Z",
        "seq": 101,
        "battery_mv": 3800,
        "rssi": -65,
        "fw": "1.4.2"
    }

    # First transmission
    res1 = client.post("/api/v1/telemetry", json=payload)
    assert res1.status_code == 201

    # Second transmission of identical sequence
    res2 = client.post("/api/v1/telemetry", json=payload)
    assert res2.status_code == 200
    data2 = res2.get_json()
    assert data2["status"] == "duplicate"

    # Verify database contains only 1 record for sequence 101
    with client.application.app_context():
        count = Telemetry.query.filter_by(sequence_number=101).count()
        assert count == 1


def test_out_of_order_sequence_handling(client):
    """Test out-of-order sequence arrival sets out_of_order=True without regressing device state."""
    payload_newer = {
        "device_id": "KSPDB-SD07-D0112-4431",
        "pole_id": "P-024431",
        "event": "heartbeat",
        "energized": True,
        "ts": "2026-07-29T02:20:00.000Z",
        "seq": 200,
        "battery_mv": 4000,
        "rssi": -60,
        "fw": "1.4.2"
    }
    client.post("/api/v1/telemetry", json=payload_newer)

    # Late arriving older sequence (seq 150 < device last_sequence 200)
    payload_older = {
        "device_id": "KSPDB-SD07-D0112-4431",
        "pole_id": "P-024431",
        "event": "power_restored",
        "energized": True,
        "ts": "2026-07-29T02:18:00.000Z",
        "seq": 150,
        "battery_mv": 3900,
        "rssi": -70,
        "fw": "1.4.2"
    }
    res_older = client.post("/api/v1/telemetry", json=payload_older)
    assert res_older.status_code == 201
    data_older = res_older.get_json()
    assert data_older["out_of_order"] is True

    # Verify device state remained at seq 200
    with client.application.app_context():
        dev = Device.query.filter_by(device_id="KSPDB-SD07-D0112-4431").first()
        assert dev.last_sequence == 200


def test_bulk_telemetry_ingestion(client):
    """Test bulk API endpoint with array of telemetry objects."""
    bulk_payload = [
        {
            "device_id": "KSPDB-SD07-D0112-4431",
            "pole_id": "P-024431",
            "event": "boot",
            "energized": True,
            "ts": "2026-07-29T03:00:00.000Z",
            "seq": 300,
            "battery_mv": 4100,
            "rssi": -55,
            "fw": "1.4.2"
        },
        {
            "device_id": "KSPDB-SD07-D0112-4431",
            "pole_id": "P-024431",
            "event": "heartbeat",
            "energized": True,
            "ts": "2026-07-29T03:05:00.000Z",
            "seq": 301,
            "battery_mv": 4090,
            "rssi": -55,
            "fw": "1.4.2"
        },
        {
            # Duplicate item
            "device_id": "KSPDB-SD07-D0112-4431",
            "pole_id": "P-024431",
            "event": "heartbeat",
            "energized": True,
            "ts": "2026-07-29T03:05:00.000Z",
            "seq": 301,
            "battery_mv": 4090,
            "rssi": -55,
            "fw": "1.4.2"
        }
    ]

    res = client.post("/api/v1/telemetry/bulk", json=bulk_payload)
    assert res.status_code == 200
    data = res.get_json()
    assert data["processed"] == 2
    assert data["duplicates"] == 1
    assert data["invalid"] == 0


def test_telemetry_statistics_and_query_api(client):
    """Test telemetry statistics and paginated list API endpoints."""
    payload = {
        "device_id": "KSPDB-SD07-D0112-4431",
        "pole_id": "P-024431",
        "event": "power_restored",
        "energized": True,
        "ts": "2026-07-29T04:00:00.000Z",
        "seq": 400,
        "battery_mv": 4000,
        "rssi": -60,
        "fw": "1.4.2"
    }
    client.post("/api/v1/telemetry", json=payload)

    # 1. Statistics API
    stat_res = client.get("/api/v1/telemetry/statistics")
    assert stat_res.status_code == 200
    stats = stat_res.get_json()
    assert stats["total_telemetry"] >= 1
    assert stats["power_restored"] >= 1

    # 2. Query API
    list_res = client.get("/api/v1/telemetry?event=power_restored")
    assert list_res.status_code == 200
    list_data = list_res.get_json()
    assert list_data["pagination"]["total_records"] >= 1
    assert list_data["telemetry"][0]["event"] == "power_restored"
