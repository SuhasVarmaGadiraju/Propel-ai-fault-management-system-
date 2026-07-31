import pytest
from app import create_app
from app.database import db
from app.models import Feeder, Transformer, Pole, Device, FeederStatus, PoleStatus, DeviceStatus
from app.services import NetworkGraphService


@pytest.fixture
def app_with_graph_data():
    """Fixture providing a test Flask app with seeded network graph hierarchy."""
    app = create_app("testing")
    with app.app_context():
        db.create_all()

        # 1. Feeder
        feeder = Feeder(feeder_code="FDR-GRAPH-01", name="Graph Feeder", status=FeederStatus.ACTIVE)
        db.session.add(feeder)
        db.session.flush()

        # 2. Transformer
        trf = Transformer(transformer_code="TRF-GRAPH-01", feeder_id=feeder.id, latitude=17.44, longitude=78.38)
        db.session.add(trf)
        db.session.flush()

        # 3. Root Pole (Seq 1)
        root_pole = Pole(
            pole_code="P-ROOT-01",
            transformer_id=trf.id,
            feeder_id=feeder.id,
            seq_on_line=1,
            latitude=17.4401,
            longitude=78.3801,
            status=PoleStatus.ACTIVE
        )
        db.session.add(root_pole)
        db.session.flush()

        # 4. Child Pole 1 (Seq 2, parent = root_pole)
        child_pole_1 = Pole(
            pole_code="P-CHILD-01",
            transformer_id=trf.id,
            feeder_id=feeder.id,
            parent_pole_id=root_pole.id,
            seq_on_line=2,
            latitude=17.4402,
            longitude=78.3802,
            status=PoleStatus.ACTIVE
        )
        db.session.add(child_pole_1)
        db.session.flush()

        # 5. Grandchild Pole (Seq 3, parent = child_pole_1)
        grandchild_pole = Pole(
            pole_code="P-GRANDCHILD-01",
            transformer_id=trf.id,
            feeder_id=feeder.id,
            parent_pole_id=child_pole_1.id,
            seq_on_line=3,
            latitude=17.4403,
            longitude=78.3803,
            status=PoleStatus.ACTIVE
        )
        db.session.add(grandchild_pole)

        # 6. Unknown Topology Pole (parent = None, seq = None)
        unknown_pole = Pole(
            pole_code="P-UNKNOWN-01",
            transformer_id=trf.id,
            feeder_id=feeder.id,
            parent_pole_id=None,
            seq_on_line=None,
            latitude=17.4409,
            longitude=78.3809,
            status=PoleStatus.ACTIVE
        )
        db.session.add(unknown_pole)

        # 7. Device attached to grandchild
        device = Device(
            device_id="DEV-GRAPH-01",
            pole_id=grandchild_pole.id,
            firmware_version="1.5.0",
            active=True,
            status=DeviceStatus.ACTIVE
        )
        db.session.add(device)
        db.session.commit()

        # Clear NetworkGraphService cache before yield
        graph_service = NetworkGraphService.get_instance()
        graph_service.invalidate_cache()

        yield app

        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app_with_graph_data):
    return app_with_graph_data.test_client()


def test_graph_construction_and_references(app_with_graph_data):
    """Test building graph in memory and verifying parent/child pointers."""
    with app_with_graph_data.app_context():
        service = NetworkGraphService.get_instance()
        service.build_graph(force_rebuild=True)

        feeder = service.get_feeder("FDR-GRAPH-01")
        assert feeder is not None
        assert len(feeder.transformers) == 1

        tr = service.get_transformer("TRF-GRAPH-01")
        assert tr is not None
        assert len(tr.poles) == 4

        root_pole = service.get_pole("P-ROOT-01")
        assert root_pole is not None
        assert root_pole.parent is None
        assert len(root_pole.children) == 1
        assert root_pole.children[0].code == "P-CHILD-01"

        child_1 = service.get_pole("P-CHILD-01")
        assert child_1 is not None
        assert child_1.parent is root_pole
        assert len(child_1.children) == 1
        assert child_1.children[0].code == "P-GRANDCHILD-01"


def test_unknown_topology_handling(app_with_graph_data):
    """Test poles with parent_pole_id = None and seq_on_line = None have topology_known = False."""
    with app_with_graph_data.app_context():
        service = NetworkGraphService.get_instance()
        service.build_graph()

        unknown_pole = service.get_pole("P-UNKNOWN-01")
        assert unknown_pole is not None
        assert unknown_pole.topology_known is False
        assert unknown_pole.parent is None


def test_path_and_descendant_traversal(app_with_graph_data):
    """Test ancestor path tracing and descendant subtree traversal."""
    with app_with_graph_data.app_context():
        service = NetworkGraphService.get_instance()
        service.build_graph()

        grandchild = service.get_pole("P-GRANDCHILD-01")
        path = service.get_path_to_transformer(grandchild)
        path_codes = [p.code for p in path]
        assert path_codes == ["P-ROOT-01", "P-CHILD-01", "P-GRANDCHILD-01"]

        root = service.get_pole("P-ROOT-01")
        descendants = service.get_descendants(root)
        desc_codes = [p.code for p in descendants]
        assert "P-CHILD-01" in desc_codes
        assert "P-GRANDCHILD-01" in desc_codes
        assert len(descendants) == 2


def test_network_graph_rest_apis(client):
    """Test REST API endpoints /api/v1/network/statistics, /tree, /pole/<id>, and /rebuild."""
    # 1. Statistics API
    res_stats = client.get("/api/v1/network/statistics")
    assert res_stats.status_code == 200
    stats = res_stats.get_json()
    assert stats["total_feeders"] == 1
    assert stats["total_transformers"] == 1
    assert stats["total_poles"] == 4
    assert stats["unknown_topology_count"] == 1

    # 2. Tree API
    res_tree = client.get("/api/v1/network/tree")
    assert res_tree.status_code == 200
    tree_data = res_tree.get_json()
    assert len(tree_data["feeders"]) == 1

    # 3. Pole Detail API
    res_pole = client.get("/api/v1/network/pole/P-GRANDCHILD-01")
    assert res_pole.status_code == 200
    pole_info = res_pole.get_json()
    assert pole_info["code"] == "P-GRANDCHILD-01"
    assert pole_info["parent_code"] == "P-CHILD-01"
    assert pole_info["path_to_root"] == ["P-ROOT-01", "P-CHILD-01", "P-GRANDCHILD-01"]

    # 4. Rebuild API
    res_rebuild = client.post("/api/v1/network/rebuild")
    assert res_rebuild.status_code == 200
    rebuild_info = res_rebuild.get_json()
    assert rebuild_info["status"] == "success"
