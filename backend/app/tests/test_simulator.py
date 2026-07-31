import pytest
from app import create_app
from app.database import db
from app.models import Feeder, Transformer, Pole, Device, Ticket, TicketStatus, FeederStatus, PoleStatus, DeviceStatus
from app.services import NetworkGraphService, SimulatorService, TicketService, FaultLocalizationService


@pytest.fixture
def app_with_sim_data():
    """Fixture providing a test Flask app with seeded radial network hierarchy (2 transformers, 4 poles)."""
    app = create_app("testing")
    with app.app_context():
        db.create_all()

        feeder = Feeder(feeder_code="FDR-SIM-01", name="Sim Feeder", status=FeederStatus.ACTIVE)
        db.session.add(feeder)
        db.session.flush()

        trf1 = Transformer(transformer_code="TRF-SIM-01", feeder_id=feeder.id, latitude=17.44, longitude=78.38)
        db.session.add(trf1)

        trf2 = Transformer(transformer_code="TRF-SIM-02", feeder_id=feeder.id, latitude=17.45, longitude=78.39)
        db.session.add(trf2)
        db.session.flush()

        # TRF2 Pole & Device (Always Energized)
        pole_trf2 = Pole(pole_code="P-SIM-TRF2", transformer_id=trf2.id, feeder_id=feeder.id, seq_on_line=1, latitude=17.4501, longitude=78.3901, status=PoleStatus.ACTIVE)
        db.session.add(pole_trf2)
        db.session.flush()
        dev_trf2 = Device(device_id="DEV-SIM-TRF2", pole_id=pole_trf2.id, energized=True, active=True, status=DeviceStatus.ACTIVE)
        db.session.add(dev_trf2)

        # TRF1 Pole A (Upstream Root)
        pole_a = Pole(pole_code="P-SIM-A", transformer_id=trf1.id, feeder_id=feeder.id, seq_on_line=1, latitude=17.4401, longitude=78.3801, status=PoleStatus.ACTIVE)
        db.session.add(pole_a)
        db.session.flush()
        dev_a = Device(device_id="DEV-SIM-A", pole_id=pole_a.id, energized=True, active=True, status=DeviceStatus.ACTIVE)
        db.session.add(dev_a)

        # TRF1 Pole B (Child of A)
        pole_b = Pole(pole_code="P-SIM-B", transformer_id=trf1.id, feeder_id=feeder.id, parent_pole_id=pole_a.id, seq_on_line=2, latitude=17.4402, longitude=78.3802, status=PoleStatus.ACTIVE)
        db.session.add(pole_b)
        db.session.flush()
        dev_b = Device(device_id="DEV-SIM-B", pole_id=pole_b.id, energized=True, active=True, status=DeviceStatus.ACTIVE)
        db.session.add(dev_b)

        # TRF1 Pole C (Child of B - Grandchild of A)
        pole_c = Pole(pole_code="P-SIM-C", transformer_id=trf1.id, feeder_id=feeder.id, parent_pole_id=pole_b.id, seq_on_line=3, latitude=17.4403, longitude=78.3803, status=PoleStatus.ACTIVE)
        db.session.add(pole_c)
        db.session.flush()
        dev_c = Device(device_id="DEV-SIM-C", pole_id=pole_c.id, energized=True, active=True, status=DeviceStatus.ACTIVE)
        db.session.add(dev_c)

        db.session.commit()
        NetworkGraphService.get_instance().invalidate_cache()
        SimulatorService._history.clear()

        yield app

        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app_with_sim_data):
    return app_with_sim_data.test_client()


def test_small_span_fault_produces_span_fault(app_with_sim_data):
    """Test running small_span_fault scenario produces SPAN_FAULT, 1 ticket, and 0 sensor anomalies."""
    with app_with_sim_data.app_context():
        res = SimulatorService.run_scenario("small_span_fault", feeder_ref="FDR-SIM-01", pole_ref="P-SIM-A")
        assert res["status"] == "success"

        loc = res["fault_localization"]
        assert loc["summary"]["total_incidents"] == 1
        assert loc["summary"]["span_faults"] == 1
        assert loc["summary"]["sensor_anomalies"] == 0

        assert len(res["tickets_created"]) == 1
        ticket = res["tickets_created"][0]
        assert ticket["fault_type"] == "SPAN_FAULT"
        assert ticket["upstream_pole"] == "P-SIM-A"
        assert ticket["downstream_pole"] == "P-SIM-B"


def test_large_span_fault_produces_span_fault(app_with_sim_data):
    """Test running large_span_fault scenario produces SPAN_FAULT and 0 sensor anomalies."""
    with app_with_sim_data.app_context():
        res = SimulatorService.run_scenario("large_span_fault", feeder_ref="FDR-SIM-01", pole_ref="P-SIM-A")
        assert res["status"] == "success"

        loc = res["fault_localization"]
        assert loc["summary"]["total_incidents"] == 1
        assert loc["summary"]["sensor_anomalies"] == 0
        assert len(res["tickets_created"]) == 1


def test_transformer_fault_simulation(app_with_sim_data):
    """Test running transformer_failure scenario generates TRANSFORMER_FAULT and 0 sensor anomalies."""
    with app_with_sim_data.app_context():
        res = SimulatorService.run_scenario("transformer_failure", transformer_ref="TRF-SIM-01")
        assert res["status"] == "success"
        loc = res["fault_localization"]
        assert loc["summary"]["transformer_faults"] == 1
        assert loc["summary"]["sensor_anomalies"] == 0
        assert res["fault_localization"]["incidents"][0]["fault_type"] == "TRANSFORMER_FAULT"


def test_feeder_fault_simulation(app_with_sim_data):
    """Test running feeder_failure scenario generates FEEDER_FAULT and 0 sensor anomalies."""
    with app_with_sim_data.app_context():
        res = SimulatorService.run_scenario("feeder_failure", feeder_ref="FDR-SIM-01")
        assert res["status"] == "success"
        loc = res["fault_localization"]
        assert loc["summary"]["feeder_faults"] == 1
        assert loc["summary"]["sensor_anomalies"] == 0
        assert res["fault_localization"]["incidents"][0]["fault_type"] == "FEEDER_FAULT"


def test_sensor_anomaly_simulation(app_with_sim_data):
    """Test running sensor_anomaly scenario generates 0 tickets and 1 sensor anomaly."""
    with app_with_sim_data.app_context():
        res = SimulatorService.run_scenario("sensor_anomaly", pole_ref="P-SIM-A")
        assert res["status"] == "success"
        assert len(res["fault_localization"]["incidents"]) == 0
        assert len(res["fault_localization"]["sensor_anomalies"]) >= 1
        assert len(res["tickets_created"]) == 0


def test_electrical_consistency_validator(app_with_sim_data):
    """Test validate_telemetry_consistency rejects impossible electrical states."""
    with app_with_sim_data.app_context():
        graph_service = NetworkGraphService.get_instance()
        graph_service.build_graph()

        # Impossible payload: Pole B is dark, but descendant Pole C is energized
        invalid_payloads = [
            {"pole_id": "P-SIM-B", "energized": False},
            {"pole_id": "P-SIM-C", "energized": True}
        ]

        with pytest.raises(ValueError) as exc_info:
            SimulatorService.validate_telemetry_consistency(invalid_payloads, graph_service, scenario_id="small_span_fault")
        assert "Invalid electrical state" in str(exc_info.value)


def test_power_restoration_and_auto_verification(app_with_sim_data):
    """Test power restoration scenario re-energizes poles and auto-verifies RESOLVED tickets."""
    with app_with_sim_data.app_context():
        # 1. Run span outage to create ticket
        SimulatorService.run_scenario("small_span_fault", pole_ref="P-SIM-A")

        # 2. Transition ticket NEW -> ASSIGNED -> RESOLVED
        tkt = Ticket.query.first()
        tkt_num = tkt.ticket_number
        TicketService.transition_status(tkt_num, "ASSIGNED")
        TicketService.transition_status(tkt_num, "RESOLVED")

        # 3. Restore power via Simulator
        res_restore = SimulatorService.restore_network(target_ref="FDR-SIM-01")
        assert res_restore["status"] == "success"
        assert res_restore["tickets_auto_verified_count"] >= 1

        tkt_after = Ticket.query.filter_by(ticket_number=tkt_num).first()
        assert tkt_after.status == TicketStatus.VERIFIED


def test_simulator_rest_apis(client):
    """Test REST API endpoints /scenarios, /run, /restore, /reset, and /history."""
    res_scenarios = client.get("/api/v1/simulator/scenarios")
    assert res_scenarios.status_code == 200
    assert len(res_scenarios.get_json()) >= 7

    res_run = client.post("/api/v1/simulator/run", json={"scenario_id": "small_span_fault", "pole_id": "P-SIM-A"})
    assert res_run.status_code == 200

    res_history = client.get("/api/v1/simulator/history")
    assert res_history.status_code == 200
    assert len(res_history.get_json()) >= 1

    res_restore = client.post("/api/v1/simulator/restore")
    assert res_restore.status_code == 200

    res_reset = client.post("/api/v1/simulator/reset")
    assert res_reset.status_code == 200
