from typing import Optional, List, TYPE_CHECKING
import uuid
from sqlalchemy import String, Float, Integer, Boolean, Enum, ForeignKey, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel
from app.models.enums import PoleStatus, PoleType

if TYPE_CHECKING:
    from app.models.feeder import Feeder
    from app.models.transformer import Transformer
    from app.models.device import Device
    from app.models.telemetry import Telemetry


class Pole(BaseModel):
    """
    Represents a physical electricity pole along a radial distribution line.
    
    IMPORTANT TOPOLOGY NOTE:
    parent_pole_id and seq_on_line MUST allow NULL values because approximately
    60% of transformers in real-world distribution networks have unknown topology.
    """
    __tablename__ = "poles"

    pole_code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)

    transformer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("transformers.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    feeder_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("feeders.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )

    # Self-referencing Parent Pole relationship (NULLABLE for unknown topology)
    parent_pole_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("poles.id", ondelete="SET NULL"),
        index=True,
        nullable=True
    )
    seq_on_line: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)

    ward: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    pincode: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)

    pole_type: Mapped[PoleType] = mapped_column(
        Enum(PoleType),
        default=PoleType.SUSPENSION,
        nullable=False
    )
    device_installed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    current_device_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    status: Mapped[PoleStatus] = mapped_column(
        Enum(PoleStatus),
        default=PoleStatus.ACTIVE,
        nullable=False
    )

    # Relationships
    feeder: Mapped["Feeder"] = relationship("Feeder", back_populates="poles")
    transformer: Mapped["Transformer"] = relationship("Transformer", back_populates="poles")

    parent_pole: Mapped[Optional["Pole"]] = relationship(
        "Pole",
        remote_side="Pole.id",
        back_populates="children_poles"
    )
    children_poles: Mapped[List["Pole"]] = relationship(
        "Pole",
        back_populates="parent_pole"
    )

    device: Mapped[Optional["Device"]] = relationship(
        "Device",
        back_populates="pole",
        uselist=False
    )
    telemetry: Mapped[List["Telemetry"]] = relationship(
        "Telemetry",
        back_populates="pole",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Pole {self.pole_code} (Parent: {self.parent_pole_id or 'None'}) - DeviceInstalled: {self.device_installed}>"
