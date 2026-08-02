import traceback
import logging
from flask import Blueprint, jsonify, request
from app.services import NetworkGraphService

logger = logging.getLogger("network_graph_routes")
network_graph_bp = Blueprint("network_graph", __name__)


@network_graph_bp.route("/statistics", methods=["GET"])
def get_network_statistics():
    """
    GET /api/v1/network/statistics
    Returns overall graph metrics, node counts, max depth, branching factor, and topology coverage.
    """
    try:
        service = NetworkGraphService.get_instance()
        stats = service.get_graph_statistics()
        return jsonify(stats), 200
    except Exception as e:
        tb = traceback.format_exc()
        logger.error(f"GET /api/v1/network/statistics failed: {e}\n{tb}")
        print("\n" + "=" * 80)
        print("GET /api/v1/network/statistics FAILED")
        print(tb)
        print("=" * 80 + "\n")
        return jsonify({"error": {"code": 500, "name": "Internal Server Error", "description": str(e), "traceback": tb}}), 500


@network_graph_bp.route("/tree", methods=["GET"])
def get_network_tree():
    """
    GET /api/v1/network/tree
    Returns the full radial network tree structure (Feeder -> Transformer -> Root Poles -> Children).
    Supports optional ?feeder_id= query parameter to filter by feeder.
    """
    try:
        service = NetworkGraphService.get_instance()
        if not service.is_built():
            service.build_graph()

        feeder_filter = request.args.get("feeder_id", "").strip()

        if feeder_filter:
            feeder = service.get_feeder(feeder_filter)
            if not feeder:
                return jsonify({
                    "error": {
                        "code": 404,
                        "name": "Not Found",
                        "description": f"Feeder '{feeder_filter}' not found in network graph."
                    }
                }), 404
            return jsonify({"feeders": [feeder.to_dict(include_tree=True)]}), 200

        unique_feeders = list({f.id: f for f in service._feeders.values()}.values())
        tree_data = [f.to_dict(include_tree=True) for f in unique_feeders]
        return jsonify({"feeders": tree_data}), 200
    except Exception as e:
        tb = traceback.format_exc()
        logger.error(f"GET /api/v1/network/tree failed: {e}\n{tb}")
        print("\n" + "=" * 80)
        print("GET /api/v1/network/tree FAILED")
        print(tb)
        print("=" * 80 + "\n")
        return jsonify({"error": {"code": 500, "name": "Internal Server Error", "description": str(e), "traceback": tb}}), 500


@network_graph_bp.route("/feeder/<feeder_ref>", methods=["GET"])
def get_feeder_node(feeder_ref: str):
    """
    GET /api/v1/network/feeder/<feeder_ref>
    Returns feeder node details and linked transformers.
    """
    try:
        service = NetworkGraphService.get_instance()
        feeder = service.get_feeder(feeder_ref)
        if not feeder:
            return jsonify({
                "error": {
                    "code": 404,
                    "name": "Not Found",
                    "description": f"Feeder '{feeder_ref}' not found."
                }
            }), 404

        return jsonify(feeder.to_dict(include_tree=True)), 200
    except Exception as e:
        tb = traceback.format_exc()
        logger.error(f"GET /api/v1/network/feeder/{feeder_ref} failed: {e}\n{tb}")
        print("\n" + "=" * 80)
        print(f"GET /api/v1/network/feeder/{feeder_ref} FAILED")
        print(tb)
        print("=" * 80 + "\n")
        return jsonify({"error": {"code": 500, "name": "Internal Server Error", "description": str(e), "traceback": tb}}), 500


@network_graph_bp.route("/transformer/<transformer_ref>", methods=["GET"])
def get_transformer_node(transformer_ref: str):
    """
    GET /api/v1/network/transformer/<transformer_ref>
    Returns transformer node details and connected root poles.
    """
    try:
        service = NetworkGraphService.get_instance()
        tr = service.get_transformer(transformer_ref)
        if not tr:
            return jsonify({
                "error": {
                    "code": 404,
                    "name": "Not Found",
                    "description": f"Transformer '{transformer_ref}' not found."
                }
            }), 404

        return jsonify(tr.to_dict(include_poles=True)), 200
    except Exception as e:
        tb = traceback.format_exc()
        logger.error(f"GET /api/v1/network/transformer/{transformer_ref} failed: {e}\n{tb}")
        print("\n" + "=" * 80)
        print(f"GET /api/v1/network/transformer/{transformer_ref} FAILED")
        print(tb)
        print("=" * 80 + "\n")
        return jsonify({"error": {"code": 500, "name": "Internal Server Error", "description": str(e), "traceback": tb}}), 500


@network_graph_bp.route("/pole/<pole_ref>", methods=["GET"])
def get_pole_node(pole_ref: str):
    """
    GET /api/v1/network/pole/<pole_ref>
    Returns pole node details, parent link, children list, path to transformer, and descendants.
    """
    try:
        service = NetworkGraphService.get_instance()
        pole = service.get_pole(pole_ref)
        if not pole:
            return jsonify({
                "error": {
                    "code": 404,
                    "name": "Not Found",
                    "description": f"Pole '{pole_ref}' not found."
                }
            }), 404

        path = service.get_path_to_transformer(pole)
        descendants = service.get_descendants(pole)

        pole_dict = pole.to_dict(include_children=True, depth=1)
        pole_dict["path_to_root"] = [p.code for p in path]
        pole_dict["descendants_count"] = len(descendants)
        pole_dict["descendants_codes"] = [p.code for p in descendants]

        return jsonify(pole_dict), 200
    except Exception as e:
        tb = traceback.format_exc()
        logger.error(f"GET /api/v1/network/pole/{pole_ref} failed: {e}\n{tb}")
        print("\n" + "=" * 80)
        print(f"GET /api/v1/network/pole/{pole_ref} FAILED")
        print(tb)
        print("=" * 80 + "\n")
        return jsonify({"error": {"code": 500, "name": "Internal Server Error", "description": str(e), "traceback": tb}}), 500


@network_graph_bp.route("/rebuild", methods=["POST"])
def rebuild_network_graph():
    """
    POST /api/v1/network/rebuild
    Triggers an in-memory graph cache invalidation and rebuild.
    """
    try:
        service = NetworkGraphService.get_instance()
        service.refresh_graph()
        stats = service.get_graph_statistics()
        return jsonify({
            "status": "success",
            "message": "In-memory network graph rebuilt successfully.",
            "statistics": stats
        }), 200
    except Exception as e:
        tb = traceback.format_exc()
        logger.error(f"POST /api/v1/network/rebuild failed: {e}\n{tb}")
        print("\n" + "=" * 80)
        print("POST /api/v1/network/rebuild FAILED")
        print(tb)
        print("=" * 80 + "\n")
        return jsonify({"error": {"code": 500, "name": "Internal Server Error", "description": str(e), "traceback": tb}}), 500
