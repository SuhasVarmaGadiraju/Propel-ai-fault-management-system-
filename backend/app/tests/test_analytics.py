import pytest
from app import create_app
from app.database import db
from app.models import Feeder, Transformer, Pole, Device, Ticket, TicketStatus, TicketPriority, FeederStatus, PoleStatus, DeviceStatus
from app.services import NetworkGraphService, AnalyticsService, TicketService


@pytest.fixture
def app_with_analytics_data():
    """Fixture providing a test Flask app with seeded network and ticket records."""
    app = create_app("testing")
    with app.app_context():
        db.create_all()

        feeder = Feeder(feeder_code="FDR-ALY-01", name="Analytics Feeder", status=FeederStatus.ACTIVE)
        db.session.add(feeder)
        db.session.flush()

        trf = Transformer(transformer_code="TRF-ALY-01", feeder_id=feeder.id, latitude=17.44, longitude=78.38)
        db.session.add(trf)
        db.session.flush()

        pole_a = Pole(pole_code="P-ALY-A", transformer_id=trf.id, feeder_id=feeder.id, seq_on_line=1, latitude=17.4401, longitude=78.3801, status=PoleStatus.ACTIVE)
        db.session.add(pole_a)
        db.session.flush()

        dev_a = Device(device_id="DEV-ALY-A", pole_id=pole_a.id, energized=True, active=True, status=DeviceStatus.ACTIVE)
        db.session.add(dev_a)

        ticket = Ticket(
            ticket_number="TKT-ALY-0001",
            incident_id="INC-ALY-0001",
            fault_type="SPAN_FAULT",
            feeder_code="FDR-ALY-01",
            transformer_code="TRF-ALY-01",
            priority=TicketPriority.HIGH,
            status=TicketStatus.NEW,
            estimated_households=24,
            confidence=95
        )
        db.session.add(ticket)
        db.session.commit()

        NetworkGraphService.get_instance().invalidate_cache()

        yield app

        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app_with_analytics_data):
    return app_with_analytics_data.test_client()


def test_analytics_overview_endpoint(client):
    """Test GET /api/v1/analytics/overview endpoint."""
    res = client.get("/api/v1/analytics/overview")
    assert res.status_code == 200
    data = res.get_json()

    assert "total_poles" in data
    assert "instrumented_poles" in data
    assert "active_faults" in data
    assert "network_health" in data
    assert isinstance(data["network_health"], (int, float))


def test_analytics_faults_endpoint(client):
    """Test GET /api/v1/analytics/faults endpoint."""
    res = client.get("/api/v1/analytics/faults")
    assert res.status_code == 200
    data = res.get_json()

    assert "by_feeder" in data
    assert "by_transformer" in data
    assert "by_fault_type" in data
    assert "by_confidence_bucket" in data


def test_analytics_tickets_endpoint(client):
    """Test GET /api/v1/analytics/tickets endpoint."""
    res = client.get("/api/v1/analytics/tickets")
    assert res.status_code == 200
    data = res.get_json()

    assert "by_status" in data
    assert "by_priority" in data
    assert data["by_status"]["NEW"] >= 1
    assert data["by_priority"]["HIGH"] >= 1


def test_analytics_reliability_endpoint(client):
    """Test GET /api/v1/analytics/reliability endpoint."""
    res = client.get("/api/v1/analytics/reliability")
    assert res.status_code == 200
    data = res.get_json()

    assert "mttr_minutes" in data
    assert "network_availability_percent" in data
    assert isinstance(data["network_availability_percent"], (int, float))


def test_analytics_simulator_endpoint(client):
    """Test GET /api/v1/analytics/simulator endpoint."""
    res = client.get("/api/v1/analytics/simulator")
    assert res.status_code == 200
    data = res.get_json()

    assert "total_simulations" in data
    assert "scenario_counts" in data


def test_analytics_export_endpoints(client):
    """Test CSV and JSON export endpoints."""
    # 1. Export tickets as CSV
    res_csv = client.get("/api/v1/analytics/export/tickets?format=csv")
    assert res_csv.status_code == 200
    assert "text/csv" in res_csv.content_type
    assert b"TKT-ALY-0001" in res_csv.data

    # 2. Export simulator history as JSON
    res_json = client.get("/api/v1/analytics/export/simulator?format=json")
    assert res_json.status_code == 200
    assert "application/json" in res_json.content_type
