import enum


class FeederStatus(str, enum.Enum):
    """Feeder operational status enum."""
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    MAINTENANCE = "MAINTENANCE"
    FAULTED = "FAULTED"


class TransformerStatus(str, enum.Enum):
    """Distribution transformer operational status enum."""
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    MAINTENANCE = "MAINTENANCE"
    FAULTED = "FAULTED"


class PoleStatus(str, enum.Enum):
    """Pole operational status enum."""
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    MAINTENANCE = "MAINTENANCE"
    FAULTED = "FAULTED"


class DeviceStatus(str, enum.Enum):
    """IoT device operational status enum."""
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    DISCONNECTED = "DISCONNECTED"
    DECOMMISSIONED = "DECOMMISSIONED"


class PoleType(str, enum.Enum):
    """Pole physical/structural classification enum."""
    TENSION = "TENSION"
    SUSPENSION = "SUSPENSION"
    JUNCTION = "JUNCTION"
    TERMINAL = "TERMINAL"
    TRANSFORMER_POLE = "TRANSFORMER_POLE"


class TelemetryEvent(str, enum.Enum):
    """Telemetry data event type enum matching assignment specification."""
    HEARTBEAT = "heartbeat"
    POWER_LOST = "power_lost"
    POWER_RESTORED = "power_restored"
    BOOT = "boot"
    FAULT_DETECTED = "fault_detected"
    LOW_BATTERY = "low_battery"

    @classmethod
    def from_string(cls, val: str) -> "TelemetryEvent":
        """Normalize event string (e.g., 'power_lost', 'POWER_LOST', 'heartbeat')."""
        normalized = val.strip().lower()
        for item in cls:
            if item.value == normalized or item.name.lower() == normalized:
                return item
        return cls.HEARTBEAT


class TicketStatus(str, enum.Enum):
    """Repair ticket lifecycle state enum."""
    NEW = "NEW"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    ASSIGNED = "ASSIGNED"
    RESOLVED = "RESOLVED"
    VERIFIED = "VERIFIED"
    CLOSED = "CLOSED"


class TicketPriority(str, enum.Enum):
    """Repair ticket priority level enum."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
