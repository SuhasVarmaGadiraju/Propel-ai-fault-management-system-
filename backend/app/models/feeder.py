from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel
from app.models.enums import FeederStatus

if TYPE_CHECKING:
    from app.models.transformer import Transformer
    from app.models.pole import Pole


class Feeder(BaseModel):
    """
    Represents an 11kV radial power distribution feeder line.
    """
    __tablename__ = "feeders"

    feeder_code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[FeederStatus] = mapped_column(
        Enum(FeederStatus),
        default=FeederStatus.ACTIVE,
        nullable=False
    )
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Relationships
    transformers: Mapped[List["Transformer"]] = relationship(
        "Transformer",
        back_populates="feeder",
        cascade="all, delete-orphan"
    )
    poles: Mapped[List["Pole"]] = relationship(
        "Pole",
        back_populates="feeder",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Feeder {self.feeder_code} ({self.name}) - {self.status.value}>"
