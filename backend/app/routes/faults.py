from flask import Blueprint, jsonify
from app.services import FaultLocalizationService, TicketService

faults_bp = Blueprint("faults", __name__)


@faults_bp.route("/analyze", methods=["POST"])
def analyze_faults():
    """
    POST /api/v1/faults/analyze
    Executes the deterministic fault localization algorithm across the distribution network
    and automatically generates repair tickets for confirmed fault incidents.
    """
    results = FaultLocalizationService.analyze_network()
    
    # Auto-generate repair tickets for confirmed incidents
    if results.get("incidents"):
        TicketService.process_fault_incidents(results["incidents"])

    return jsonify(results), 200


@faults_bp.route("/latest", methods=["GET"])
def get_latest_faults():
    """
    GET /api/v1/faults/latest
    Returns cached or latest fault localization analysis results.
    """
    results = FaultLocalizationService.get_latest_results()
    return jsonify(results), 200
