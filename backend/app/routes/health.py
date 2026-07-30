from flask import Blueprint, jsonify

health_bp = Blueprint("health", __name__)


@health_bp.route("/health", methods=["GET"])
def health_check():
    """
    Health check endpoint.
    GET /api/v1/health
    """
    return jsonify({
        "status": "healthy",
        "service": "Propel Fault Management Backend"
    }), 200
