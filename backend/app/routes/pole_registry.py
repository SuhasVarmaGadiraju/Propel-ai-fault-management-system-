from flask import Blueprint, request, jsonify
from sqlalchemy import or_, desc, asc

from app.database import db
from app.models import Feeder, Transformer, Pole, Device
from app.services import PoleRegistryImportService

pole_registry_bp = Blueprint("pole_registry", __name__)


@pole_registry_bp.route("/import", methods=["POST"])
def import_pole_registry():
    """
    POST /api/v1/pole-registry/import
    Upload and import official electricity department CSV pole registry file.
    """
    if "file" not in request.files and not request.data:
        return jsonify({
            "error": {
                "code": 400,
                "name": "Bad Request",
                "description": "No file uploaded. Please attach a CSV file under form-data key 'file'."
            }
        }), 400

    if "file" in request.files:
        uploaded_file = request.files["file"]
        if not uploaded_file.filename or not uploaded_file.filename.endswith(".csv"):
            return jsonify({
                "error": {
                    "code": 400,
                    "name": "Bad Request",
                    "description": "Only .csv files are supported."
                }
            }), 400
        csv_text = uploaded_file.read().decode("utf-8", errors="replace")
    else:
        csv_text = request.data.decode("utf-8", errors="replace")

    summary = PoleRegistryImportService.import_csv(csv_text)
    return jsonify(summary), 200


@pole_registry_bp.route("/statistics", methods=["GET"])
def get_pole_registry_statistics():
    """
    GET /api/v1/pole-registry/statistics
    Returns operational counts for poles, transformers, feeders, topology status, and device installations.
    """
    total_poles = Pole.query.count()
    total_transformers = Transformer.query.count()
    total_feeders = Feeder.query.count()
    total_devices = Device.query.count()

    unknown_topology_count = Pole.query.filter(
        Pole.parent_pole_id.is_(None),
        Pole.seq_on_line.is_(None)
    ).count()

    poles_without_devices = Pole.query.filter(
        Pole.device_installed.is_(False)
    ).count()

    return jsonify({
        "total_poles": total_poles,
        "total_transformers": total_transformers,
        "total_feeders": total_feeders,
        "total_devices": total_devices,
        "unknown_topology_count": unknown_topology_count,
        "poles_without_devices": poles_without_devices,
    }), 200


@pole_registry_bp.route("", methods=["GET"])
def list_poles():
    """
    GET /api/v1/pole-registry
    Query paginated pole list with search filtering by pole_id, feeder, transformer, ward, pincode, and device status.
    """
    page = request.args.get("page", 1, type=int)
    page_size = min(request.args.get("page_size", 20, type=int), 100)
    search = request.args.get("search", "").strip()
    feeder_code = request.args.get("feeder_code", "").strip()
    transformer_code = request.args.get("transformer_code", "").strip()
    ward = request.args.get("ward", "").strip()
    pincode = request.args.get("pincode", "").strip()
    device_installed_param = request.args.get("device_installed", "").strip().lower()
    sort_by = request.args.get("sort_by", "created_at").strip()
    order = request.args.get("order", "desc").strip().lower()

    query = Pole.query.join(Feeder, Pole.feeder_id == Feeder.id).join(Transformer, Pole.transformer_id == Transformer.id)

    if search:
        query = query.filter(
            or_(
                Pole.pole_code.ilike(f"%{search}%"),
                Feeder.feeder_code.ilike(f"%{search}%"),
                Transformer.transformer_code.ilike(f"%{search}%"),
                Pole.ward.ilike(f"%{search}%"),
                Pole.pincode.ilike(f"%{search}%"),
            )
        )

    if feeder_code:
        query = query.filter(Feeder.feeder_code.ilike(f"%{feeder_code}%"))

    if transformer_code:
        query = query.filter(Transformer.transformer_code.ilike(f"%{transformer_code}%"))

    if ward:
        query = query.filter(Pole.ward.ilike(f"%{ward}%"))

    if pincode:
        query = query.filter(Pole.pincode.ilike(f"%{pincode}%"))

    if device_installed_param in ("true", "1"):
        query = query.filter(Pole.device_installed.is_(True))
    elif device_installed_param in ("false", "0"):
        query = query.filter(Pole.device_installed.is_(False))

    # Sorting
    sort_column = getattr(Pole, sort_by, Pole.created_at)
    if order == "asc":
        query = query.order_by(asc(sort_column))
    else:
        query = query.order_by(desc(sort_column))

    total_records = query.count()
    total_pages = (total_records + page_size - 1) // page_size if total_records > 0 else 1

    poles = query.offset((page - 1) * page_size).limit(page_size).all()

    poles_data = []
    for p in poles:
        poles_data.append({
            "id": str(p.id),
            "pole_code": p.pole_code,
            "feeder_code": p.feeder.feeder_code,
            "feeder_name": p.feeder.name,
            "transformer_code": p.transformer.transformer_code,
            "parent_pole_id": str(p.parent_pole_id) if p.parent_pole_id else None,
            "parent_pole_code": p.parent_pole.pole_code if p.parent_pole else None,
            "seq_on_line": p.seq_on_line,
            "latitude": p.latitude,
            "longitude": p.longitude,
            "ward": p.ward,
            "pincode": p.pincode,
            "pole_type": p.pole_type.value,
            "device_installed": p.device_installed,
            "current_device_id": p.current_device_id,
            "status": p.status.value,
            "topology_known": p.parent_pole_id is not None or p.seq_on_line is not None,
            "created_at": p.created_at.isoformat() if p.created_at else None,
        })

    return jsonify({
        "poles": poles_data,
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total_records": total_records,
            "total_pages": total_pages,
        }
    }), 200


@pole_registry_bp.route("/<pole_ref>", methods=["GET"])
def get_pole_detail(pole_ref: str):
    """
    GET /api/v1/pole-registry/<pole_ref>
    Returns detailed pole metrics including parent/children topology graph and attached IoT device.
    """
    pole = Pole.query.filter(
        or_(Pole.pole_code == pole_ref, db.cast(Pole.id, db.String) == pole_ref)
    ).first()

    if not pole:
        return jsonify({
            "error": {
                "code": 404,
                "name": "Not Found",
                "description": f"Pole with code or ID '{pole_ref}' was not found."
            }
        }), 404

    children_data = [
        {
            "id": str(child.id),
            "pole_code": child.pole_code,
            "seq_on_line": child.seq_on_line,
            "pole_type": child.pole_type.value,
            "device_installed": child.device_installed,
            "status": child.status.value,
        }
        for child in pole.children_poles
    ]

    device_data = None
    if pole.device:
        device_data = {
            "id": str(pole.device.id),
            "device_id": pole.device.device_id,
            "firmware_version": pole.device.firmware_version,
            "battery_mv": pole.device.battery_mv,
            "last_rssi": pole.device.last_rssi,
            "installed_at": pole.device.installed_at.isoformat() if pole.device.installed_at else None,
            "active": pole.device.active,
            "status": pole.device.status.value,
        }

    return jsonify({
        "id": str(pole.id),
        "pole_code": pole.pole_code,
        "feeder": {
            "id": str(pole.feeder.id),
            "feeder_code": pole.feeder.feeder_code,
            "name": pole.feeder.name,
            "status": pole.feeder.status.value,
        },
        "transformer": {
            "id": str(pole.transformer.id),
            "transformer_code": pole.transformer.transformer_code,
            "capacity_kva": pole.transformer.capacity_kva,
            "households_served": pole.transformer.households_served,
            "status": pole.transformer.status.value,
        },
        "parent_pole": {
            "id": str(pole.parent_pole.id),
            "pole_code": pole.parent_pole.pole_code,
            "seq_on_line": pole.parent_pole.seq_on_line,
        } if pole.parent_pole else None,
        "children_poles": children_data,
        "seq_on_line": pole.seq_on_line,
        "latitude": pole.latitude,
        "longitude": pole.longitude,
        "ward": pole.ward,
        "pincode": pole.pincode,
        "pole_type": pole.pole_type.value,
        "device_installed": pole.device_installed,
        "device": device_data,
        "status": pole.status.value,
        "topology_known": pole.parent_pole_id is not None or pole.seq_on_line is not None,
        "created_at": pole.created_at.isoformat() if pole.created_at else None,
        "updated_at": pole.updated_at.isoformat() if pole.updated_at else None,
    }), 200
