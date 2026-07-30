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
    """Telemetry data event type enum."""
    HEARTBEAT = "HEARTBEAT"
    POWER_OUTAGE = "POWER_OUTAGE"
    POWER_RESTORED = "POWER_RESTORED"
    FAULT_DETECTED = "FAULT_DETECTED"
    LOW_BATTERY = "LOW_BATTERY"
