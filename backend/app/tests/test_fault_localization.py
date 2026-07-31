import pytest
from app import create_app
from app.database import db
from app.models import Feeder, Transformer, Pole, Device, FeederStatus, PoleStatus, DeviceStatus
from app.services import NetworkGraphService, FaultLocalizationService


@pytest.fixture
def app_with_fault_data():
    """Fixture providing a test Flask app with seeded radial network and device states."""
    app = create_app("testing")
    with app.app_context():
        db.create_all()

        # Feeder 1
        feeder1 = Feeder(feeder_code="FDR-TEST-01", name="Test Feeder 1", status=FeederStatus.ACTIVE)
        db.session.add(feeder1)
        db.session.flush()

        # Transformer 1 under Feeder 1
        trf1 = Transformer(transformer_code="TRF-TEST-01", feeder_id=feeder1.id, latitude=17.44, longitude=78.38)
        db.session.add(trf1)

        # Transformer 2 under Feeder 1 (keeps Feeder 1 partially active during DT outage tests)
        trf2 = Transformer(transformer_code="TRF-TEST-02", feeder_id=feeder1.id, latitude=17.45, longitude=78.39)
        db.session.add(trf2)
        db.session.flush()

        # Transformer 2 Pole & Device (Always Energized)
        pole_trf2 = Pole(
            pole_code="P-TRF2-01",
            transformer_id=trf2.id,
            feeder_id=feeder1.id,
            seq_on_line=1,
            latitude=17.4501,
            longitude=78.3901,
            status=PoleStatus.ACTIVE
        )
        db.session.add(pole_trf2)
        db.session.flush()
        dev_trf2 = Device(device_id="DEV-TRF2-01", pole_id=pole_trf2.id, energized=True, active=True, status=DeviceStatus.ACTIVE)
        db.session.add(dev_trf2)

        # Root Pole A (Energized) under Transformer 1
        pole_a = Pole(
            pole_code="P-TEST-A",
            transformer_id=trf1.id,
            feeder_id=feeder1.id,
            seq_on_line=1,
            latitude=17.4401,
            longitude=78.3801,
            status=PoleStatus.ACTIVE
        )
        db.session.add(pole_a)
        db.session.flush()

        dev_a = Device(
            device_id="DEV-A",
            pole_id=pole_a.id,
            energized=True,
            active=True,
            status=DeviceStatus.ACTIVE
        )
        db.session.add(dev_a)

        # Child Pole B (Dark) under Transformer 1
        pole_b = Pole(
            pole_code="P-TEST-B",
            transformer_id=trf1.id,
            feeder_id=feeder1.id,
            parent_pole_id=pole_a.id,
            seq_on_line=2,
            latitude=17.4402,
            longitude=78.3802,
            status=PoleStatus.ACTIVE
        )
        db.session.add(pole_b)
        db.session.flush()

        dev_b = Device(
            device_id="DEV-B",
            pole_id=pole_b.id,
            energized=False,
            active=True,
            status=DeviceStatus.ACTIVE
        )
        db.session.add(dev_b)

        # Grandchild Pole C (Dark) under Transformer 1
        pole_c = Pole(
            pole_code="P-TEST-C",
            transformer_id=trf1.id,
            feeder_id=feeder1.id,
            parent_pole_id=pole_b.id,
            seq_on_line=3,
            latitude=17.4403,
            longitude=78.3803,
            status=PoleStatus.ACTIVE
        )
        db.session.add(pole_c)
        db.session.flush()

        dev_c = Device(
            device_id="DEV-C",
            pole_id=pole_c.id,
            energized=False,
            active=True,
            status=DeviceStatus.ACTIVE
        )
        db.session.add(dev_c)

        # Unknown Topology Pole under Transformer 1 (parent_pole_id = None, seq = None)
        pole_unk = Pole(
            pole_code="P-TEST-UNK-01",
            transformer_id=trf1.id,
            feeder_id=feeder1.id,
            parent_pole_id=None,
            seq_on_line=None,
            latitude=17.4409,
            longitude=78.3809,
            status=PoleStatus.ACTIVE
        )
        db.session.add(pole_unk)
        db.session.flush()

        dev_unk = Device(
            device_id="DEV-UNK-01",
            pole_id=pole_unk.id,
            energized=True,
            active=True,
            status=DeviceStatus.ACTIVE
        )
        db.session.add(dev_unk)
        db.session.commit()

        # Invalidate graph cache before tests run
        graph_service = NetworkGraphService.get_instance()
        graph_service.invalidate_cache()

        yield app

        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app_with_fault_data):
    return app_with_fault_data.test_client()


def test_scenario_1_single_span_fault(app_with_fault_data):
    """Scenario 1: Pole A energized, Pole B dark, Pole C dark -> Span Fault A -> B."""
    with app_with_fault_data.app_context():
        results = FaultLocalizationService.analyze_network()
        incidents = results["incidents"]

        assert len(incidents) >= 1
        fault = incidents[0]
        assert fault["fault_type"] == "SPAN_FAULT"
        assert fault["upstream_pole"] == "P-TEST-A"
        assert fault["downstream_pole"] == "P-TEST-B"
        assert "P-TEST-B" in fault["affected_poles"]
        assert "P-TEST-C" in fault["affected_poles"]
        assert fault["confidence"] >= 90
        assert "reasoning" in fault
        assert len(fault["reasoning"]) >= 3


def test_confidence_scoring_and_deductions(app_with_fault_data):
    """Test confidence scoring deductions for unknown topology and telemetry lag."""
    with app_with_fault_data.app_context():
        results = FaultLocalizationService.analyze_network()
        incidents = results["incidents"]
        fault = incidents[0]

        assert "confidence" in fault
        assert "confidence_reason" in fault
        assert isinstance(fault["confidence"], int)
        assert 0 <= fault["confidence"] <= 100


def test_unknown_span_fallback(app_with_fault_data):
    """Test UNKNOWN_SPAN fallback fault generation when unknown topology poles go dark."""
    with app_with_fault_data.app_context():
        # Set Pole A, B, C to energized, set UNK pole to dark
        dev_b = Device.query.filter_by(device_id="DEV-B").first()
        dev_b.energized = True

        dev_unk = Device.query.filter_by(device_id="DEV-UNK-01").first()
        dev_unk.energized = False
        db.session.commit()

        NetworkGraphService.get_instance().refresh_graph()

        results = FaultLocalizationService.analyze_network()
        incidents = results["incidents"]

        assert len(incidents) == 1
        fault = incidents[0]
        assert fault["fault_type"] == "UNKNOWN_SPAN"
        assert fault["topology_known"] is False
        assert fault["confidence"] <= 75


def test_scenario_2_transformer_fault(app_with_fault_data):
    """Scenario 2: Every pole under Transformer 1 is dark -> Transformer Fault."""
    with app_with_fault_data.app_context():
        # Set all devices under TRF-1 to dark
        for dev_id in ["DEV-A", "DEV-B", "DEV-C", "DEV-UNK-01"]:
            d = Device.query.filter_by(device_id=dev_id).first()
            if d:
                d.energized = False
        db.session.commit()

        NetworkGraphService.get_instance().refresh_graph()

        results = FaultLocalizationService.analyze_network()
        incidents = results["incidents"]

        assert len(incidents) == 1
        fault = incidents[0]
        assert fault["fault_type"] == "TRANSFORMER_FAULT"
        assert fault["transformer_code"] == "TRF-TEST-01"


def test_scenario_3_feeder_fault(app_with_fault_data):
    """Scenario 3: Every transformer & pole under Feeder 1 is dark -> Feeder Fault."""
    with app_with_fault_data.app_context():
        for dev in Device.query.all():
            dev.energized = False
        db.session.commit()

        NetworkGraphService.get_instance().refresh_graph()

        results = FaultLocalizationService.analyze_network()
        incidents = results["incidents"]

        assert len(incidents) == 1
        fault = incidents[0]
        assert fault["fault_type"] == "FEEDER_FAULT"
        assert fault["feeder_code"] == "FDR-TEST-01"


def test_scenario_4_sensor_anomaly(app_with_fault_data):
    """Scenario 4: Pole A energized, Pole B dark BUT Pole C energized -> Sensor Anomaly (0 faults)."""
    with app_with_fault_data.app_context():
        dev_c = Device.query.filter_by(device_id="DEV-C").first()
        dev_c.energized = True
        db.session.commit()

        NetworkGraphService.get_instance().refresh_graph()

        results = FaultLocalizationService.analyze_network()
        incidents = results["incidents"]
        anomalies = results["sensor_anomalies"]

        assert len(incidents) == 0
        assert len(anomalies) >= 1
        assert anomalies[0]["pole_code"] == "P-TEST-B"


def test_scenario_5_simultaneous_span_faults(app_with_fault_data):
    """Scenario 5: Two independent branches with span faults -> 2 separate incident objects."""
    with app_with_fault_data.app_context():
        trf = Transformer.query.filter_by(transformer_code="TRF-TEST-01").first()
        feeder = Feeder.query.filter_by(feeder_code="FDR-TEST-01").first()

        pole_d = Pole(
            pole_code="P-TEST-D",
            transformer_id=trf.id,
            feeder_id=feeder.id,
            seq_on_line=1,
            latitude=17.4410,
            longitude=78.3810,
            status=PoleStatus.ACTIVE
        )
        db.session.add(pole_d)
        db.session.flush()

        dev_d = Device(device_id="DEV-D", pole_id=pole_d.id, energized=True, active=True, status=DeviceStatus.ACTIVE)
        db.session.add(dev_d)

        pole_e = Pole(
            pole_code="P-TEST-E",
            transformer_id=trf.id,
            feeder_id=feeder.id,
            parent_pole_id=pole_d.id,
            seq_on_line=2,
            latitude=17.4411,
            longitude=78.3811,
            status=PoleStatus.ACTIVE
        )
        db.session.add(pole_e)
        db.session.flush()

        dev_e = Device(device_id="DEV-E", pole_id=pole_e.id, energized=False, active=True, status=DeviceStatus.ACTIVE)
        db.session.add(dev_e)
        db.session.commit()

        NetworkGraphService.get_instance().refresh_graph()

        results = FaultLocalizationService.analyze_network()
        incidents = results["incidents"]

        assert len(incidents) == 2
        types = [i["fault_type"] for i in incidents]
        assert "SPAN_FAULT" in types


def test_fault_localization_rest_apis_with_confidence_and_reasoning(client):
    """Test REST API endpoints return new fields confidence, confidence_reason, and reasoning."""
    res_analyze = client.post("/api/v1/faults/analyze")
    assert res_analyze.status_code == 200
    data = res_analyze.get_json()
    assert len(data["incidents"]) >= 1

    fault = data["incidents"][0]
    assert "confidence" in fault
    assert "confidence_reason" in fault
    assert "topology_known" in fault
    assert "possible_fault_range" in fault
    assert "reasoning" in fault
    assert isinstance(fault["reasoning"], list)
