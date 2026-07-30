from typing import Optional, List, TYPE_CHECKING
import uuid
from sqlalchemy import String, Float, Integer, Enum, ForeignKey, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel
from app.models.enums import TransformerStatus

if TYPE_CHECKING:
    from app.models.feeder import Feeder
    from app.models.pole import Pole


class Transformer(BaseModel):
    """
    Represents a Distribution Transformer (DTR) connected to an 11kV Feeder.
    """
    __tablename__ = "transformers"

    transformer_code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    feeder_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("feeders.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    capacity_kva: Mapped[float] = mapped_column(Float, nullable=False, default=100.0)
    households_served: Mapped[int] = mapped_column(Integer, nullable=False, default=25)
    status: Mapped[TransformerStatus] = mapped_column(
        Enum(TransformerStatus),
        default=TransformerStatus.ACTIVE,
        nullable=False
    )

    # Relationships
    feeder: Mapped["Feeder"] = relationship("Feeder", back_populates="transformers")
    poles: Mapped[List["Pole"]] = relationship(
        "Pole",
        back_populates="transformer",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Transformer {self.transformer_code} ({self.capacity_kva} kVA) - {self.status.value}>"
