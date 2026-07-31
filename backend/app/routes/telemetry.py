from datetime import datetime, timezone, timedelta
from flask import Blueprint, request, jsonify
from sqlalchemy import or_, desc, asc, func

from app.database import db
from app.models import Device, Pole, Telemetry, TelemetryEvent
from app.services import TelemetryIngestionService

telemetry_bp = Blueprint("telemetry", __name__)


@telemetry_bp.route("", methods=["POST"])
def ingest_telemetry_single():
    """
    POST /api/v1/telemetry
    Ingests a single IoT pole telemetry event.
    """
    payload = request.get_json(silent=True)
    if not payload:
        return jsonify({
            "error": {
                "code": 400,
                "name": "Bad Request",
                "description": "Invalid or missing JSON payload."
            }
        }), 400

    result, status_code = TelemetryIngestionService.ingest_single(payload)
    return jsonify(result), status_code


@telemetry_bp.route("/bulk", methods=["POST"])
def ingest_telemetry_bulk():
    """
    POST /api/v1/telemetry/bulk
    Batch ingests an array of IoT pole telemetry events.
    """
    payloads = request.get_json(silent=True)
    if not isinstance(payloads, list):
        return jsonify({
            "error": {
                "code": 400,
                "name": "Bad Request",
                "description": "Bulk request payload must be a JSON array of telemetry objects."
            }
        }), 400

    result, status_code = TelemetryIngestionService.ingest_bulk(payloads)
    return jsonify(result), status_code


@telemetry_bp.route("/statistics", methods=["GET"])
def get_telemetry_statistics():
    """
    GET /api/v1/telemetry/statistics
    Returns overall telemetry event metrics, event type breakdowns, out-of-order counts, and online device status.
    """
    total_telemetry = Telemetry.query.count()

    now = datetime.now(timezone.utc)
    today_start = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)
    today_count = Telemetry.query.filter(Telemetry.event_timestamp >= today_start).count()

    heartbeats = Telemetry.query.filter(Telemetry.event == TelemetryEvent.HEARTBEAT).count()
    power_lost = Telemetry.query.filter(Telemetry.event == TelemetryEvent.POWER_LOST).count()
    power_restored = Telemetry.query.filter(Telemetry.event == TelemetryEvent.POWER_RESTORED).count()
    boot = Telemetry.query.filter(Telemetry.event == TelemetryEvent.BOOT).count()

    out_of_order_messages = Telemetry.query.filter(Telemetry.out_of_order.is_(True)).count()

    # Online Devices Definition: communicates within last 15 minutes
    fifteen_mins_ago = now - timedelta(minutes=15)
    currently_online_devices = Device.query.filter(
        Device.last_seen.isnot(None),
        Device.last_seen >= fifteen_mins_ago
    ).count()

    total_devices = Device.query.count()
    offline_devices = max(0, total_devices - currently_online_devices)

    return jsonify({
        "total_telemetry": total_telemetry,
        "today_count": today_count,
        "heartbeats": heartbeats,
        "power_lost": power_lost,
        "power_restored": power_restored,
        "boot": boot,
        "out_of_order_messages": out_of_order_messages,
        "currently_online_devices": currently_online_devices,
        "offline_devices": offline_devices,
        "total_devices": total_devices,
    }), 200


@telemetry_bp.route("", methods=["GET"])
def list_telemetry():
    """
    GET /api/v1/telemetry
    Returns a paginated list of telemetry event stream records with filtering support.
    """
    page = request.args.get("page", 1, type=int)
    page_size = min(request.args.get("page_size", 20, type=int), 100)
    device_id = request.args.get("device_id", "").strip()
    pole_id = request.args.get("pole_id", "").strip()
    event_str = request.args.get("event", "").strip()
    out_of_order_param = request.args.get("out_of_order", "").strip().lower()
    sort_by = request.args.get("sort_by", "event_timestamp").strip()
    order = request.args.get("order", "desc").strip().lower()

    query = Telemetry.query.join(Device, Telemetry.device_id == Device.id).join(Pole, Telemetry.pole_id == Pole.id)

    if device_id:
        query = query.filter(Device.device_id.ilike(f"%{device_id}%"))

    if pole_id:
        query = query.filter(
            or_(
                Pole.pole_code.ilike(f"%{pole_id}%"),
                db.cast(Pole.id, db.String) == pole_id
            )
        )

    if event_str:
        telemetry_enum = TelemetryEvent.from_string(event_str)
        query = query.filter(Telemetry.event == telemetry_enum)

    if out_of_order_param in ("true", "1"):
        query = query.filter(Telemetry.out_of_order.is_(True))
    elif out_of_order_param in ("false", "0"):
        query = query.filter(Telemetry.out_of_order.is_(False))

    # Sorting
    sort_column = getattr(Telemetry, sort_by, Telemetry.event_timestamp)
    if order == "asc":
        query = query.order_by(asc(sort_column))
    else:
        query = query.order_by(desc(sort_column))

    total_records = query.count()
    total_pages = (total_records + page_size - 1) // page_size if total_records > 0 else 1

    records = query.offset((page - 1) * page_size).limit(page_size).all()

    telemetry_data = []
    for t in records:
        telemetry_data.append({
            "id": str(t.id),
            "device_id": t.device.device_id,
            "pole_code": t.pole.pole_code,
            "event": t.event.value,
            "energized": t.energized,
            "sequence_number": t.sequence_number,
            "out_of_order": t.out_of_order,
            "battery_mv": t.battery_mv,
            "rssi": t.rssi,
            "firmware_version": t.firmware_version,
            "event_timestamp": t.event_timestamp.isoformat() if t.event_timestamp else None,
            "received_timestamp": t.received_timestamp.isoformat() if t.received_timestamp else None,
        })

    return jsonify({
        "telemetry": telemetry_data,
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total_records": total_records,
            "total_pages": total_pages,
        }
    }), 200
