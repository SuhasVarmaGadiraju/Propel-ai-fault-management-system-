from typing import Optional, List, TYPE_CHECKING
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Integer, Boolean, Enum, ForeignKey, DateTime, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel
from app.models.enums import DeviceStatus

if TYPE_CHECKING:
    from app.models.pole import Pole
    from app.models.telemetry import Telemetry


class Device(BaseModel):
    """
    Represents a physical IoT telemetry sensor device attached to a Pole.
    Separated from Pole to support device replacement, maintenance, and lifecycle tracking.
    """
    __tablename__ = "devices"

    device_id: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)

    pole_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("poles.id", ondelete="SET NULL"),
        unique=True,
        index=True,
        nullable=True
    )

    firmware_version: Mapped[str] = mapped_column(String(20), default="1.0.0", nullable=False)
    battery_mv: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    last_rssi: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    installed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=True
    )
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    status: Mapped[DeviceStatus] = mapped_column(
        Enum(DeviceStatus),
        default=DeviceStatus.ACTIVE,
        nullable=False
    )

    # Relationships
    pole: Mapped[Optional["Pole"]] = relationship("Pole", back_populates="device")
    telemetry: Mapped[List["Telemetry"]] = relationship(
        "Telemetry",
        back_populates="device",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Device {self.device_id} (Pole: {self.pole_id or 'Unassigned'}) - Active: {self.active}>"
