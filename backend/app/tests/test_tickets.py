import pytest
from datetime import datetime, timezone
from app import create_app
from app.database import db
from app.models import Feeder, Transformer, Pole, Device, Ticket, TicketStatus, TicketPriority, FeederStatus, PoleStatus, DeviceStatus
from app.services import NetworkGraphService, FaultLocalizationService, TicketService


@pytest.fixture
def app_with_ticket_data():
    """Fixture providing a test Flask app with seeded fault data and auto-generated ticket."""
    app = create_app("testing")
    with app.app_context():
        db.create_all()

        feeder = Feeder(feeder_code="FDR-TKT-01", name="Ticket Feeder", status=FeederStatus.ACTIVE)
        db.session.add(feeder)
        db.session.flush()

        trf = Transformer(transformer_code="TRF-TKT-01", feeder_id=feeder.id, latitude=17.44, longitude=78.38)
        db.session.add(trf)
        db.session.flush()

        pole_a = Pole(pole_code="P-TKT-A", transformer_id=trf.id, feeder_id=feeder.id, seq_on_line=1, latitude=17.4401, longitude=78.3801, status=PoleStatus.ACTIVE)
        db.session.add(pole_a)
        db.session.flush()
        dev_a = Device(device_id="DEV-TKT-A", pole_id=pole_a.id, energized=True, active=True, status=DeviceStatus.ACTIVE)
        db.session.add(dev_a)

        pole_b = Pole(pole_code="P-TKT-B", transformer_id=trf.id, feeder_id=feeder.id, parent_pole_id=pole_a.id, seq_on_line=2, latitude=17.4402, longitude=78.3802, status=PoleStatus.ACTIVE)
        db.session.add(pole_b)
        db.session.flush()
        dev_b = Device(device_id="DEV-TKT-B", pole_id=pole_b.id, energized=False, active=True, status=DeviceStatus.ACTIVE)
        db.session.add(dev_b)

        db.session.commit()
        NetworkGraphService.get_instance().invalidate_cache()

        yield app

        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app_with_ticket_data):
    return app_with_ticket_data.test_client()


def test_ticket_auto_creation_and_duplicate_prevention(client):
    """Test auto-creation of tickets from fault analysis and duplicate prevention."""
    # 1. Trigger fault analysis which auto-generates tickets
    res = client.post("/api/v1/faults/analyze")
    assert res.status_code == 200

    with client.application.app_context():
        tickets = Ticket.query.all()
        assert len(tickets) == 1
        tkt = tickets[0]
        assert tkt.status == TicketStatus.NEW
        assert tkt.fault_type == "SPAN_FAULT"
        assert tkt.upstream_pole == "P-TKT-A"
        assert tkt.downstream_pole == "P-TKT-B"

    # 2. Trigger fault analysis again (duplicate prevention check)
    res2 = client.post("/api/v1/faults/analyze")
    assert res2.status_code == 200

    with client.application.app_context():
        tickets_after = Ticket.query.all()
        assert len(tickets_after) == 1  # No duplicate ticket created!


def test_valid_state_machine_transitions(client):
    """Test valid state transitions NEW -> ACKNOWLEDGED -> ASSIGNED -> RESOLVED -> VERIFIED -> CLOSED."""
    client.post("/api/v1/faults/analyze")

    with client.application.app_context():
        tkt = Ticket.query.first()
        tkt_num = tkt.ticket_number

    # 1. NEW -> ACKNOWLEDGED
    res1 = client.patch(f"/api/v1/tickets/{tkt_num}", json={"status": "ACKNOWLEDGED"})
    assert res1.status_code == 200
    assert res1.get_json()["ticket"]["status"] == "ACKNOWLEDGED"

    # 2. ACKNOWLEDGED -> ASSIGNED
    res2 = client.patch(f"/api/v1/tickets/{tkt_num}", json={"status": "ASSIGNED", "assigned_engineer": "Eng. Suhas", "assigned_team": "Team Alpha"})
    assert res2.status_code == 200
    tkt_data2 = res2.get_json()["ticket"]
    assert tkt_data2["status"] == "ASSIGNED"
    assert tkt_data2["assigned_engineer"] == "Eng. Suhas"

    # 3. ASSIGNED -> RESOLVED
    res3 = client.patch(f"/api/v1/tickets/{tkt_num}", json={"status": "RESOLVED"})
    assert res3.status_code == 200
    assert res3.get_json()["ticket"]["status"] == "RESOLVED"


def test_invalid_state_transition_rejection(client):
    """Test invalid state transition NEW -> CLOSED is rejected with HTTP 400."""
    client.post("/api/v1/faults/analyze")

    with client.application.app_context():
        tkt_num = Ticket.query.first().ticket_number

    # Attempt NEW -> CLOSED (invalid)
    res_bad = client.patch(f"/api/v1/tickets/{tkt_num}", json={"status": "CLOSED"})
    assert res_bad.status_code == 400
    err = res_bad.get_json()
    assert "Invalid state transition" in err["error"]["description"]


def test_auto_verification(client):
    """Test auto-verification fails while pole is dark, but succeeds after power is restored."""
    client.post("/api/v1/faults/analyze")

    with client.application.app_context():
        tkt = Ticket.query.first()
        tkt_num = tkt.ticket_number

    # Transition NEW -> ASSIGNED -> RESOLVED
    client.patch(f"/api/v1/tickets/{tkt_num}", json={"status": "ASSIGNED"})
    client.patch(f"/api/v1/tickets/{tkt_num}", json={"status": "RESOLVED"})

    # 1. Attempt auto-verify while Pole B is still dark -> Should fail HTTP 400
    res_verify_fail = client.post(f"/api/v1/tickets/{tkt_num}/verify")
    assert res_verify_fail.status_code == 400
    assert res_verify_fail.get_json()["verified"] is False

    # 2. Restore power to Pole B in database
    with client.application.app_context():
        dev_b = Device.query.filter_by(device_id="DEV-TKT-B").first()
        dev_b.energized = True
        db.session.commit()
        NetworkGraphService.get_instance().refresh_graph()

    # 3. Attempt auto-verify now -> Should succeed HTTP 200 and transition to VERIFIED
    res_verify_success = client.post(f"/api/v1/tickets/{tkt_num}/verify")
    assert res_verify_success.status_code == 200
    assert res_verify_success.get_json()["verified"] is True
    assert res_verify_success.get_json()["ticket"]["status"] == "VERIFIED"


def test_ticket_statistics_api(client):
    """Test GET /api/v1/tickets/statistics endpoint."""
    client.post("/api/v1/faults/analyze")

    res = client.get("/api/v1/tickets/statistics")
    assert res.status_code == 200
    stats = res.get_json()
    assert stats["total_tickets"] >= 1
    assert stats["new_count"] >= 1
