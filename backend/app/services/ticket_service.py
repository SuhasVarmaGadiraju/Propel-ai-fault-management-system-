import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Any
from sqlalchemy import or_, desc, asc

from app.database import db
from app.models import Ticket, TicketStatus, TicketPriority, Feeder, Transformer, Pole
from app.services.network_graph_service import NetworkGraphService

logger = logging.getLogger("ticket_service")


class TicketService:
    """
    Service managing the lifecycle, state machine transitions, auto-creation,
    priority calculation, and auto-verification of Repair Tickets.
    """

    VALID_TRANSITIONS = {
        TicketStatus.NEW: {TicketStatus.ACKNOWLEDGED, TicketStatus.ASSIGNED},
        TicketStatus.ACKNOWLEDGED: {TicketStatus.ASSIGNED},
        TicketStatus.ASSIGNED: {TicketStatus.RESOLVED},
        TicketStatus.RESOLVED: {TicketStatus.VERIFIED},
        TicketStatus.VERIFIED: {TicketStatus.CLOSED},
        TicketStatus.CLOSED: set(),
    }

    @classmethod
    def calculate_priority(cls, fault_type: str, households: int, confidence: int) -> TicketPriority:
        """
        Calculates ticket priority deterministically based on fault type, households, and confidence.
        """
        if fault_type == "FEEDER_FAULT" or households > 200:
            return TicketPriority.CRITICAL
        if fault_type == "TRANSFORMER_FAULT" or households > 50:
            return TicketPriority.HIGH
        if households > 10:
            return TicketPriority.MEDIUM
        return TicketPriority.LOW

    @classmethod
    def process_fault_incidents(cls, incidents: List[Dict[str, Any]]) -> List[Ticket]:
        """
        Consumes localized fault incidents and automatically creates repair tickets.
        If an active non-closed ticket already exists for an incident/location, returns that active ticket.
        Prevents duplicate ticket creation.
        """
        result_tickets: List[Ticket] = []

        for inc in incidents:
            incident_id = inc.get("incident_id")
            downstream = inc.get("downstream_pole")
            tr_code = inc.get("transformer_code")
            feeder_code = inc.get("feeder_code")
            fault_type = inc.get("fault_type")

            # Check 1: Existing active ticket for exact incident_id
            active_ticket = None
            if incident_id:
                active_ticket = Ticket.query.filter(
                    Ticket.incident_id == incident_id,
                    Ticket.status != TicketStatus.CLOSED
                ).first()

            # Check 2: Existing active ticket for same downstream pole (Span Fault)
            if not active_ticket and downstream:
                active_ticket = Ticket.query.filter(
                    Ticket.downstream_pole == downstream,
                    Ticket.status != TicketStatus.CLOSED
                ).first()

            # Check 3: Existing active ticket for same transformer (Transformer Fault)
            if not active_ticket and fault_type == "TRANSFORMER_FAULT" and tr_code:
                active_ticket = Ticket.query.filter(
                    Ticket.transformer_code == tr_code,
                    Ticket.fault_type == "TRANSFORMER_FAULT",
                    Ticket.status != TicketStatus.CLOSED
                ).first()

            # Check 4: Existing active ticket for same feeder (Feeder Fault)
            if not active_ticket and fault_type == "FEEDER_FAULT" and feeder_code:
                active_ticket = Ticket.query.filter(
                    Ticket.feeder_code == feeder_code,
                    Ticket.fault_type == "FEEDER_FAULT",
                    Ticket.status != TicketStatus.CLOSED
                ).first()

            if active_ticket:
                result_tickets.append(active_ticket)
                continue

            # Create NEW Ticket if no active non-closed ticket exists!
            count = Ticket.query.count() + len(result_tickets) + 1
            ticket_num = f"TKT-2026-{count:04d}"

            priority = cls.calculate_priority(
                fault_type=inc.get("fault_type", "SPAN_FAULT"),
                households=inc.get("estimated_households", 0),
                confidence=inc.get("confidence", 100)
            )

            feeder_obj = Feeder.query.filter_by(feeder_code=feeder_code).first() if feeder_code else None
            tr_obj = Transformer.query.filter_by(transformer_code=tr_code).first() if tr_code else None

            reason_summary = inc.get("reason", "")
            if inc.get("reasoning") and isinstance(inc["reasoning"], list):
                reason_summary = "\n".join(inc["reasoning"])

            ticket = Ticket(
                ticket_number=ticket_num,
                incident_id=incident_id or f"INC-{ticket_num}",
                fault_type=inc.get("fault_type", "SPAN_FAULT"),
                feeder_id=feeder_obj.id if feeder_obj else None,
                feeder_code=feeder_code,
                transformer_id=tr_obj.id if tr_obj else None,
                transformer_code=tr_code,
                upstream_pole=inc.get("upstream_pole"),
                downstream_pole=downstream,
                priority=priority,
                status=TicketStatus.NEW,
                estimated_households=inc.get("estimated_households", 0),
                confidence=inc.get("confidence", 100),
                reasoning_summary=reason_summary,
                created_at=datetime.now(timezone.utc)
            )

            db.session.add(ticket)
            result_tickets.append(ticket)

        if result_tickets:
            db.session.commit()
            logger.info(f"Processed {len(result_tickets)} repair tickets from fault analysis.")

        return result_tickets

    @classmethod
    def get_ticket(cls, ticket_ref: str) -> Optional[Ticket]:
        """Resolves Ticket by UUID or ticket_number."""
        return Ticket.query.filter(
            or_(
                Ticket.ticket_number == ticket_ref,
                db.cast(Ticket.id, db.String) == ticket_ref
            )
        ).first()

    @classmethod
    def transition_status(
        cls,
        ticket_ref: str,
        new_status_str: str,
        assigned_engineer: Optional[str] = None,
        assigned_team: Optional[str] = None
    ) -> Tuple[Dict[str, Any], int]:
        """
        Validates state machine transition and updates audit timestamps.
        """
        ticket = cls.get_ticket(ticket_ref)
        if not ticket:
            return {
                "error": {
                    "code": 404,
                    "name": "Not Found",
                    "description": f"Repair ticket '{ticket_ref}' not found."
                }
            }, 404

        try:
            target_status = TicketStatus(new_status_str.upper())
        except ValueError:
            return {
                "error": {
                    "code": 400,
                    "name": "Bad Request",
                    "description": f"Invalid ticket status '{new_status_str}'."
                }
            }, 400

        current_status = ticket.status
        if target_status not in cls.VALID_TRANSITIONS.get(current_status, set()):
            return {
                "error": {
                    "code": 400,
                    "name": "Bad Request",
                    "description": f"Invalid state transition from {current_status.value} to {target_status.value}."
                }
            }, 400

        # Execute Transition & Timestamp
        now = datetime.now(timezone.utc)
        ticket.status = target_status

        if target_status == TicketStatus.ACKNOWLEDGED:
            ticket.acknowledged_at = now
        elif target_status == TicketStatus.ASSIGNED:
            ticket.assigned_at = now
            if not ticket.acknowledged_at:
                ticket.acknowledged_at = now
        elif target_status == TicketStatus.RESOLVED:
            ticket.resolved_at = now
        elif target_status == TicketStatus.VERIFIED:
            ticket.verified_at = now
        elif target_status == TicketStatus.CLOSED:
            ticket.closed_at = now

        if assigned_engineer:
            ticket.assigned_engineer = assigned_engineer
        if assigned_team:
            ticket.assigned_team = assigned_team

        db.session.commit()

        return {
            "status": "success",
            "message": f"Ticket {ticket.ticket_number} status updated to {target_status.value}.",
            "ticket": ticket.to_dict()
        }, 200

    @classmethod
    def auto_verify_ticket(cls, ticket_ref: str) -> Tuple[Dict[str, Any], int]:
        """
        Queries live telemetry for ticket's affected poles.
        If all affected poles report energized=True, transitions RESOLVED -> VERIFIED.
        """
        ticket = cls.get_ticket(ticket_ref)
        if not ticket:
            return {
                "error": {
                    "code": 404,
                    "name": "Not Found",
                    "description": f"Repair ticket '{ticket_ref}' not found."
                }
            }, 404

        if ticket.status != TicketStatus.RESOLVED:
            return {
                "error": {
                    "code": 400,
                    "name": "Bad Request",
                    "description": f"Auto-verification requires ticket to be in RESOLVED state. Current state: {ticket.status.value}."
                }
            }, 400

        graph_service = NetworkGraphService.get_instance()
        graph_service.build_graph(force_rebuild=True)

        target_pole_code = ticket.downstream_pole or ticket.upstream_pole
        if target_pole_code:
            pole = graph_service.get_pole(target_pole_code)
            if pole:
                descendants = graph_service.get_descendants(pole)
                affected_nodes = [pole] + descendants
                dark_nodes = [p for p in affected_nodes if p.device_id and not p.energized]
                if dark_nodes:
                    dark_codes = [p.code for p in dark_nodes]
                    return {
                        "verified": False,
                        "message": f"Auto-verification failed: Telemetry reports {len(dark_nodes)} pole(s) still de-energized ({', '.join(dark_codes[:3])}).",
                        "ticket": ticket.to_dict()
                    }, 400

        # Auto-verification successful!
        ticket.status = TicketStatus.VERIFIED
        ticket.verified_at = datetime.now(timezone.utc)
        db.session.commit()

        return {
            "verified": True,
            "message": f"Auto-verification successful: Power restored across all affected poles. Ticket status updated to VERIFIED.",
            "ticket": ticket.to_dict()
        }, 200

    @classmethod
    def list_tickets(
        cls,
        page: int = 1,
        page_size: int = 20,
        search: str = "",
        status_filter: str = "",
        priority_filter: str = "",
        engineer_filter: str = "",
        transformer_filter: str = ""
    ) -> Dict[str, Any]:
        """Returns paginated repair tickets list matching filters."""
        query = Ticket.query

        if search:
            query = query.filter(
                or_(
                    Ticket.ticket_number.ilike(f"%{search}%"),
                    Ticket.incident_id.ilike(f"%{search}%"),
                    Ticket.feeder_code.ilike(f"%{search}%"),
                    Ticket.transformer_code.ilike(f"%{search}%"),
                    Ticket.downstream_pole.ilike(f"%{search}%")
                )
            )

        if status_filter:
            try:
                st = TicketStatus(status_filter.upper())
                query = query.filter(Ticket.status == st)
            except ValueError:
                pass

        if priority_filter:
            try:
                pr = TicketPriority(priority_filter.upper())
                query = query.filter(Ticket.priority == pr)
            except ValueError:
                pass

        if engineer_filter:
            query = query.filter(Ticket.assigned_engineer.ilike(f"%{engineer_filter}%"))

        if transformer_filter:
            query = query.filter(Ticket.transformer_code.ilike(f"%{transformer_filter}%"))

        query = query.order_by(desc(Ticket.created_at))

        total_records = query.count()
        total_pages = (total_records + page_size - 1) // page_size if total_records > 0 else 1
        records = query.offset((page - 1) * page_size).limit(page_size).all()

        return {
            "tickets": [t.to_dict() for t in records],
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_records": total_records,
                "total_pages": total_pages
            }
        }

    @classmethod
    def get_ticket_statistics(cls) -> Dict[str, Any]:
        """Returns overall repair ticket status counts and critical metric breakdown."""
        total_tickets = Ticket.query.count()
        new_count = Ticket.query.filter(Ticket.status == TicketStatus.NEW).count()
        acknowledged_count = Ticket.query.filter(Ticket.status == TicketStatus.ACKNOWLEDGED).count()
        assigned_count = Ticket.query.filter(Ticket.status == TicketStatus.ASSIGNED).count()
        resolved_count = Ticket.query.filter(Ticket.status == TicketStatus.RESOLVED).count()
        verified_count = Ticket.query.filter(Ticket.status == TicketStatus.VERIFIED).count()
        closed_count = Ticket.query.filter(Ticket.status == TicketStatus.CLOSED).count()

        critical_count = Ticket.query.filter(Ticket.priority == TicketPriority.CRITICAL).count()

        return {
            "total_tickets": total_tickets,
            "new_count": new_count,
            "acknowledged_count": acknowledged_count,
            "assigned_count": assigned_count,
            "resolved_count": resolved_count,
            "verified_count": verified_count,
            "closed_count": closed_count,
            "critical_count": critical_count
        }
