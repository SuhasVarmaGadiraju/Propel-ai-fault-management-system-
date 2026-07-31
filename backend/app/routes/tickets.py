from flask import Blueprint, request, jsonify
from app.services import TicketService

tickets_bp = Blueprint("tickets", __name__)


@tickets_bp.route("", methods=["GET"])
def list_tickets():
    """
    GET /api/v1/tickets
    Returns a paginated list of repair tickets with search and filtering support.
    """
    page = request.args.get("page", 1, type=int)
    page_size = min(request.args.get("page_size", 20, type=int), 100)
    search = request.args.get("search", "").strip()
    status_filter = request.args.get("status", "").strip()
    priority_filter = request.args.get("priority", "").strip()
    engineer_filter = request.args.get("engineer", "").strip()
    transformer_filter = request.args.get("transformer", "").strip()

    data = TicketService.list_tickets(
        page=page,
        page_size=page_size,
        search=search,
        status_filter=status_filter,
        priority_filter=priority_filter,
        engineer_filter=engineer_filter,
        transformer_filter=transformer_filter
    )
    return jsonify(data), 200


@tickets_bp.route("/statistics", methods=["GET"])
def get_ticket_statistics():
    """
    GET /api/v1/tickets/statistics
    Returns repair ticket lifecycle status counts and priority metrics.
    """
    stats = TicketService.get_ticket_statistics()
    return jsonify(stats), 200


@tickets_bp.route("/<ticket_ref>", methods=["GET"])
def get_ticket_detail(ticket_ref: str):
    """
    GET /api/v1/tickets/<ticket_ref>
    Returns single ticket details by UUID or ticket_number.
    """
    ticket = TicketService.get_ticket(ticket_ref)
    if not ticket:
        return jsonify({
            "error": {
                "code": 404,
                "name": "Not Found",
                "description": f"Repair ticket '{ticket_ref}' not found."
            }
        }), 404

    return jsonify(ticket.to_dict()), 200


@tickets_bp.route("/<ticket_ref>", methods=["PATCH"])
def update_ticket_status(ticket_ref: str):
    """
    PATCH /api/v1/tickets/<ticket_ref>
    Transitions ticket status or updates assigned engineer/team.
    Validates state machine rules (NEW -> ACKNOWLEDGED -> ASSIGNED -> RESOLVED -> VERIFIED -> CLOSED).
    """
    payload = request.get_json(silent=True) or {}
    new_status = payload.get("status")
    assigned_engineer = payload.get("assigned_engineer")
    assigned_team = payload.get("assigned_team")

    if not new_status and not assigned_engineer and not assigned_team:
        return jsonify({
            "error": {
                "code": 400,
                "name": "Bad Request",
                "description": "Request body must specify 'status', 'assigned_engineer', or 'assigned_team'."
            }
        }), 400

    if new_status:
        result, status_code = TicketService.transition_status(
            ticket_ref=ticket_ref,
            new_status_str=new_status,
            assigned_engineer=assigned_engineer,
            assigned_team=assigned_team
        )
        return jsonify(result), status_code

    # Engineer/Team update without status change
    ticket = TicketService.get_ticket(ticket_ref)
    if not ticket:
        return jsonify({
            "error": {
                "code": 404,
                "name": "Not Found",
                "description": f"Repair ticket '{ticket_ref}' not found."
            }
        }), 404

    if assigned_engineer:
        ticket.assigned_engineer = assigned_engineer
    if assigned_team:
        ticket.assigned_team = assigned_team
    
    from app.database import db
    db.session.commit()

    return jsonify({
        "status": "success",
        "message": "Ticket assignment updated successfully.",
        "ticket": ticket.to_dict()
    }), 200


@tickets_bp.route("/<ticket_ref>/verify", methods=["POST"])
def verify_ticket(ticket_ref: str):
    """
    POST /api/v1/tickets/<ticket_ref>/verify
    Queries live telemetry to automatically verify whether power has been restored to affected poles.
    Transitions ticket from RESOLVED -> VERIFIED upon clean verification.
    """
    result, status_code = TicketService.auto_verify_ticket(ticket_ref)
    return jsonify(result), status_code
