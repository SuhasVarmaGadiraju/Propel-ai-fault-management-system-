from datetime import datetime, timezone
from app.database import db
from app.models.base import BaseModel


class SimulatorUsage(BaseModel):
    """
    Persistent model tracking execution counts of simulation scenarios and telemetry testing actions.
    """
    __tablename__ = "simulator_usage"

    scenario_key = db.Column(db.String(64), unique=True, nullable=False, index=True)
    label = db.Column(db.String(128), nullable=False)
    execution_count = db.Column(db.Integer, default=0, nullable=False)
    last_executed_at = db.Column(db.DateTime(timezone=True), nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "scenario_key": self.scenario_key,
            "label": self.label,
            "execution_count": self.execution_count,
            "last_executed_at": self.last_executed_at.isoformat() if self.last_executed_at else None
        }

    @classmethod
    def increment(cls, scenario_key: str, label: str = None) -> "SimulatorUsage":
        """
        Atomically increments execution count for a target scenario.
        """
        try:
            record = cls.query.filter_by(scenario_key=scenario_key).first()
            if not record:
                default_label = label or scenario_key.replace("_", " ").title()
                record = cls(
                    scenario_key=scenario_key,
                    label=default_label,
                    execution_count=1,
                    last_executed_at=datetime.now(timezone.utc)
                )
                db.session.add(record)
            else:
                record.execution_count += 1
                record.last_executed_at = datetime.now(timezone.utc)
                if label and record.label != label:
                    record.label = label
            db.session.commit()
            return record
        except Exception:
            db.session.rollback()
            record = cls.query.filter_by(scenario_key=scenario_key).first()
            if record:
                record.execution_count += 1
                record.last_executed_at = datetime.now(timezone.utc)
                db.session.commit()
                return record
            return None
