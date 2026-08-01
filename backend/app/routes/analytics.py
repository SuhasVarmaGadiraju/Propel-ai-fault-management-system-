from flask import Blueprint, request, jsonify, Response
from app.services import AnalyticsService

analytics_bp = Blueprint("analytics", __name__)


@analytics_bp.route("/overview", methods=["GET"])
def get_overview():
    """
    GET /api/v1/analytics/overview
    Returns overall system KPIs, active/open counts, and network health %.
    """
    data = AnalyticsService.get_overview()
    return jsonify(data), 200


@analytics_bp.route("/faults", methods=["GET"])
def get_fault_analytics():
    """
    GET /api/v1/analytics/faults
    Returns fault breakdown grouped by feeder, transformer, fault type, and confidence bucket.
    """
    data = AnalyticsService.get_fault_analytics()
    return jsonify(data), 200


@analytics_bp.route("/tickets", methods=["GET"])
def get_ticket_analytics():
    """
    GET /api/v1/analytics/tickets
    Returns repair ticket status counts and priority distribution.
    """
    data = AnalyticsService.get_ticket_analytics()
    return jsonify(data), 200


@analytics_bp.route("/reliability", methods=["GET"])
def get_reliability_metrics():
    """
    GET /api/v1/analytics/reliability
    Returns MTTR, average outage size, availability %, and location KPIs.
    """
    data = AnalyticsService.get_reliability_metrics()
    return jsonify(data), 200


@analytics_bp.route("/simulator", methods=["GET"])
def get_simulator_analytics():
    """
    GET /api/v1/analytics/simulator
    Returns simulator execution history metrics and scenario counts.
    """
    data = AnalyticsService.get_simulator_analytics()
    return jsonify(data), 200


@analytics_bp.route("/export/<dataset_type>", methods=["GET"])
def export_data(dataset_type: str):
    """
    GET /api/v1/analytics/export/<dataset_type>?format=csv|json
    Exports Faults, Tickets, or Simulator history in downloadable CSV or JSON format.
    """
    format_type = request.args.get("format", "csv").lower()

    try:
        content, mimetype = AnalyticsService.export_dataset(dataset_type, format_type)
        filename = f"propel_{dataset_type}_export.{format_type}"

        return Response(
            content,
            mimetype=mimetype,
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        ), 200
    except ValueError as val_err:
        return jsonify({
            "error": {
                "code": 400,
                "name": "Bad Request",
                "description": str(val_err)
            }
        }), 400
