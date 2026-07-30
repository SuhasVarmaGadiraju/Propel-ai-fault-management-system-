from typing import Optional, TYPE_CHECKING
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Integer, Boolean, Enum, ForeignKey, DateTime, UUID, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel
from app.models.enums import TelemetryEvent

if TYPE_CHECKING:
    from app.models.device import Device
    from app.models.pole import Pole


class Telemetry(BaseModel):
    """
    Represents raw time-series telemetry events transmitted from physical Devices on Poles.
    
    Indexes are explicitly created on (pole_id), (device_id), (event_timestamp), and (sequence_number)
    for high-speed querying during real-time fault detection processing.
    """
    __tablename__ = "telemetry"

    device_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("devices.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    pole_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("poles.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )

    event: Mapped[TelemetryEvent] = mapped_column(
        Enum(TelemetryEvent),
        default=TelemetryEvent.HEARTBEAT,
        nullable=False
    )
    energized: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    sequence_number: Mapped[int] = mapped_column(Integer, index=True, nullable=False)

    battery_mv: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    rssi: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    firmware_version: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    event_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        index=True,
        nullable=False
    )
    received_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Relationships
    device: Mapped["Device"] = relationship("Device", back_populates="telemetry")
    pole: Mapped["Pole"] = relationship("Pole", back_populates="telemetry")

    __table_args__ = (
        Index("idx_telemetry_pole_id", "pole_id"),
        Index("idx_telemetry_device_id", "device_id"),
        Index("idx_telemetry_event_timestamp", "event_timestamp"),
        Index("idx_telemetry_sequence_number", "sequence_number"),
    )

    def __repr__(self) -> str:
        return f"<Telemetry Pole:{self.pole_id} Event:{self.event.value} Seq:{self.sequence_number} Time:{self.event_timestamp}>"
