import pytest
from app import create_app
from app.database import db
from app.models import Feeder, Transformer, Pole, Device, FeederStatus, TransformerStatus


@pytest.fixture
def app_with_db():
    """Fixture providing a Flask app instance with test database and base Feeders/Transformers."""
    app = create_app("testing")
    with app.app_context():
        db.create_all()

        # Seed 1 Feeder and 1 Transformer for relationship validation tests
        feeder = Feeder(
            feeder_code="FDR-TEST-100",
            name="Test Feeder",
            status=FeederStatus.ACTIVE
        )
        db.session.add(feeder)
        db.session.flush()

        trf = Transformer(
            transformer_code="TRF-TEST-100",
            feeder_id=feeder.id,
            latitude=17.4400,
            longitude=78.3800,
            capacity_kva=100.0,
            status=TransformerStatus.ACTIVE
        )
        db.session.add(trf)
        db.session.commit()

        yield app

        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app_with_db):
    return app_with_db.test_client()


def test_import_missing_headers(client):
    """Test importing CSV with missing required columns."""
    bad_csv = "pole_id,ward,pincode\nPOL-1,Ward-1,500001\n"
    response = client.post(
        "/api/v1/pole-registry/import",
        data=bad_csv,
        content_type="text/csv"
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["total_rows"] == 0
    assert len(data["errors"]) > 0
    assert "Missing required CSV columns" in data["errors"][0]["error"]


def test_import_invalid_coordinates(client):
    """Test importing CSV with out-of-range GPS coordinates."""
    csv_data = (
        "pole_id,lat,lon,feeder_id,dt_id,seq_on_line,parent_pole_id,pole_type,ward,pincode,device_id\n"
        "POL-BAD-GPS,120.0,78.38,FDR-TEST-100,TRF-TEST-100,,,SUSPENSION,Ward-1,500001,\n"
    )
    response = client.post(
        "/api/v1/pole-registry/import",
        data=csv_data,
        content_type="text/csv"
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["skipped_count"] == 1
    assert data["imported_count"] == 0
    assert "Invalid GPS coordinates" in data["errors"][0]["error"]


def test_import_unknown_feeder(client):
    """Test importing CSV referencing non-existent Feeder."""
    csv_data = (
        "pole_id,lat,lon,feeder_id,dt_id,seq_on_line,parent_pole_id,pole_type,ward,pincode,device_id\n"
        "POL-NO-FDR,17.44,78.38,FDR-NONEXISTENT,TRF-TEST-100,,,SUSPENSION,Ward-1,500001,\n"
    )
    response = client.post(
        "/api/v1/pole-registry/import",
        data=csv_data,
        content_type="text/csv"
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["skipped_count"] == 1
    assert "Feeder 'FDR-NONEXISTENT' not found" in data["errors"][0]["error"]


def test_import_success_and_upsert(client):
    """Test successful CSV import followed by re-import update (UPSERT)."""
    csv_data = (
        "pole_id,lat,lon,feeder_id,dt_id,seq_on_line,parent_pole_id,pole_type,ward,pincode,device_id\n"
        "POL-GOOD-01,17.4401,78.3801,FDR-TEST-100,TRF-TEST-100,1,,TRANSFORMER_POLE,Ward-1,500001,DEV-01\n"
        "POL-GOOD-02,17.4404,78.3804,FDR-TEST-100,TRF-TEST-100,2,POL-GOOD-01,SUSPENSION,Ward-1,500001,DEV-02\n"
        "POL-UNK-TOP,17.4408,78.3808,FDR-TEST-100,TRF-TEST-100,,,SUSPENSION,Ward-2,500001,\n"
    )
    # First Import (Insertion)
    response1 = client.post(
        "/api/v1/pole-registry/import",
        data=csv_data,
        content_type="text/csv"
    )
    assert response1.status_code == 200
    data1 = response1.get_json()
    assert data1["imported_count"] == 3
    assert data1["updated_count"] == 0
    assert data1["skipped_count"] == 0

    # Second Import with modified ward (UPSERT Update)
    csv_data_updated = (
        "pole_id,lat,lon,feeder_id,dt_id,seq_on_line,parent_pole_id,pole_type,ward,pincode,device_id\n"
        "POL-GOOD-01,17.4401,78.3801,FDR-TEST-100,TRF-TEST-100,1,,TRANSFORMER_POLE,Ward-UPDATED,500001,DEV-01\n"
    )
    response2 = client.post(
        "/api/v1/pole-registry/import",
        data=csv_data_updated,
        content_type="text/csv"
    )
    assert response2.status_code == 200
    data2 = response2.get_json()
    assert data2["imported_count"] == 0
    assert data2["updated_count"] == 1


def test_statistics_and_list_api(client):
    """Test statistics API and paginated pole search query API."""
    # Seed 2 poles
    csv_data = (
        "pole_id,lat,lon,feeder_id,dt_id,seq_on_line,parent_pole_id,pole_type,ward,pincode,device_id\n"
        "POL-STAT-01,17.44,78.38,FDR-TEST-100,TRF-TEST-100,1,,TRANSFORMER_POLE,Ward-10,500001,DEV-S1\n"
        "POL-STAT-02,17.45,78.39,FDR-TEST-100,TRF-TEST-100,,,SUSPENSION,Ward-20,500002,\n"
    )
    client.post("/api/v1/pole-registry/import", data=csv_data, content_type="text/csv")

    # 1. Statistics API
    stat_res = client.get("/api/v1/pole-registry/statistics")
    assert stat_res.status_code == 200
    stats = stat_res.get_json()
    assert stats["total_poles"] == 2
    assert stats["total_feeders"] == 1
    assert stats["total_transformers"] == 1
    assert stats["unknown_topology_count"] == 1
    assert stats["poles_without_devices"] == 1

    # 2. List & Search API
    list_res = client.get("/api/v1/pole-registry?ward=Ward-10")
    assert list_res.status_code == 200
    list_data = list_res.get_json()
    assert list_data["pagination"]["total_records"] == 1
    assert list_data["poles"][0]["pole_code"] == "POL-STAT-01"

    # 3. Pole Detail API
    detail_res = client.get("/api/v1/pole-registry/POL-STAT-01")
    assert detail_res.status_code == 200
    detail = detail_res.get_json()
    assert detail["pole_code"] == "POL-STAT-01"
    assert detail["device_installed"] is True
    assert detail["device"]["device_id"] == "DEV-S1"
