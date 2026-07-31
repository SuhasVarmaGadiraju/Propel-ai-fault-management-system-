from typing import Optional
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Integer, Enum, ForeignKey, DateTime, Text, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel
from app.models.enums import TicketStatus, TicketPriority


class Ticket(BaseModel):
    """
    Represents an automated Maintenance Repair Ticket generated from confirmed fault localization incidents.
    Tracks work assignment, SLA priority, and strict state transitions.
    """
    __tablename__ = "tickets"

    ticket_number: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    incident_id: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    fault_type: Mapped[str] = mapped_column(String(50), nullable=False)

    feeder_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("feeders.id", ondelete="SET NULL"), nullable=True)
    feeder_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    transformer_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("transformers.id", ondelete="SET NULL"), nullable=True)
    transformer_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    upstream_pole: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    downstream_pole: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    priority: Mapped[TicketPriority] = mapped_column(Enum(TicketPriority), default=TicketPriority.MEDIUM, nullable=False, index=True)
    status: Mapped[TicketStatus] = mapped_column(Enum(TicketStatus), default=TicketStatus.NEW, nullable=False, index=True)

    assigned_engineer: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    assigned_team: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    estimated_households: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    confidence: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    reasoning_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Lifecycle Timestamps
    acknowledged_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    assigned_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    def to_dict(self) -> dict:
        """Convert Ticket instance to JSON-serializable dictionary."""
        return {
            "id": str(self.id),
            "ticket_number": self.ticket_number,
            "incident_id": self.incident_id,
            "fault_type": self.fault_type,
            "feeder_id": str(self.feeder_id) if self.feeder_id else None,
            "feeder_code": self.feeder_code,
            "transformer_id": str(self.transformer_id) if self.transformer_id else None,
            "transformer_code": self.transformer_code,
            "upstream_pole": self.upstream_pole,
            "downstream_pole": self.downstream_pole,
            "priority": self.priority.value if hasattr(self.priority, "value") else str(self.priority),
            "status": self.status.value if hasattr(self.status, "value") else str(self.status),
            "assigned_engineer": self.assigned_engineer,
            "assigned_team": self.assigned_team,
            "estimated_households": self.estimated_households,
            "confidence": self.confidence,
            "reasoning_summary": self.reasoning_summary,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "acknowledged_at": self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            "assigned_at": self.assigned_at.isoformat() if self.assigned_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "verified_at": self.verified_at.isoformat() if self.verified_at else None,
            "closed_at": self.closed_at.isoformat() if self.closed_at else None,
        }

    def __repr__(self) -> str:
        return f"<Ticket {self.ticket_number} ({self.status.value}) - Incident: {self.incident_id}>"
