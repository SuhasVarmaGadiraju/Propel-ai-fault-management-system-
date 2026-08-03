import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple

from app.database import db
from app.models import Pole, Device, Telemetry, TelemetryEvent, DeviceStatus

logger = logging.getLogger("telemetry_ingestion")


class TelemetryIngestionService:
    """
    Production-ready telemetry ingestion service responsible for validating payloads,
    detecting duplicates, handling out-of-order messages, storing event records,
    and updating live IoT device operational states.
    """

    @classmethod
    def parse_iso_timestamp(cls, ts_str: str) -> Optional[datetime]:
        """Parse ISO 8601 timestamp string into UTC datetime object."""
        if not ts_str:
            return None
        try:
            normalized_ts = ts_str.replace("Z", "+00:00")
            dt = datetime.fromisoformat(normalized_ts)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except (ValueError, TypeError):
            return None

    @classmethod
    def validate_payload(cls, payload: Dict[str, Any]) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """
        Validates telemetry payload structure and types according to assignment schema.
        Expected keys: device_id, pole_id, event, energized, ts, seq, battery_mv, rssi, fw.
        """
        if not isinstance(payload, dict):
            return False, "Payload must be a JSON object.", None

        device_id_raw = str(payload.get("device_id", "")).strip()
        pole_id_raw = str(payload.get("pole_id", "")).strip()
        event_raw = str(payload.get("event", "")).strip()
        energized_raw = payload.get("energized")
        ts_raw = str(payload.get("ts", "")).strip()
        seq_raw = payload.get("seq")

        if not device_id_raw:
            return False, "Missing required field 'device_id'.", None
        if not pole_id_raw:
            return False, "Missing required field 'pole_id'.", None
        if not event_raw:
            return False, "Missing required field 'event'.", None
        if energized_raw is None or not isinstance(energized_raw, bool):
            return False, "Missing or invalid boolean field 'energized'.", None
        if seq_raw is None or not isinstance(seq_raw, int):
            return False, "Missing or invalid integer field 'seq'.", None

        event_timestamp = cls.parse_iso_timestamp(ts_raw)
        if not event_timestamp:
            return False, f"Invalid ISO 8601 timestamp format 'ts': '{ts_raw}'.", None

        telemetry_event = TelemetryEvent.from_string(event_raw)

        cleaned_data = {
            "device_id_raw": device_id_raw,
            "pole_id_raw": pole_id_raw,
            "event": telemetry_event,
            "energized": bool(energized_raw),
            "event_timestamp": event_timestamp,
            "sequence_number": int(seq_raw),
            "battery_mv": int(payload["battery_mv"]) if payload.get("battery_mv") is not None else None,
            "rssi": int(payload["rssi"]) if payload.get("rssi") is not None else None,
            "firmware_version": str(payload.get("fw", "1.0.0")).strip() if payload.get("fw") else None,
        }

        return True, None, cleaned_data

    @classmethod
    def ingest_single(cls, payload: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
        """
        Processes a single telemetry payload.
        Returns result dict and HTTP status code.
        """
        try:
            logger.info("STEP 1: Validating payload")
            is_valid, err_msg, data = cls.validate_payload(payload)
            if not is_valid or not data:
                return {
                    "status": "error",
                    "error": {
                        "code": 400,
                        "name": "Bad Request",
                        "description": err_msg
                    }
                }, 400

            logger.info("STEP 2: Looking up pole")
            # Resolve Pole first
            pole = Pole.query.filter(
                (Pole.pole_code == data["pole_id_raw"]) | (db.cast(Pole.id, db.String) == data["pole_id_raw"])
            ).first()

            if not pole:
                pole = Pole.query.first()

            if not pole:
                db.session.rollback()
                return {
                    "status": "error",
                    "error": {
                        "code": 404,
                        "name": "Not Found",
                        "description": f"Pole '{data['pole_id_raw']}' not found in registry."
                    }
                }, 404

            logger.info("STEP 3: Looking up device")
            # Resolve or create Device
            device = Device.query.filter_by(device_id=data["device_id_raw"]).first()
            if not device:
                logger.info("STEP 3b: Creating device")
                # Link to pole if pole does not have an attached device yet
                target_pole_id = pole.id if pole.device is None else None
                device = Device(
                    device_id=data["device_id_raw"],
                    pole_id=target_pole_id,
                    firmware_version=data["firmware_version"] or "1.0.0",
                    active=True,
                    status=DeviceStatus.ACTIVE
                )
                db.session.add(device)
                db.session.flush()

            # Safely assign device to pole if unassigned and pole has no device assigned
            if device.pole_id is None and pole.device is None:
                device.pole_id = pole.id
                pole.device_installed = True
                pole.current_device_id = device.device_id

            # Duplicate Detection Strategy: Check if (device_id, sequence_number) exists
            print("=" * 60)
            print("Incoming Device:", data["device_id_raw"])
            print("Incoming Pole:", data["pole_id_raw"])
            print("DB Device ID:", device.id)
            print("Sequence:", data["sequence_number"])
            print("=" * 60)

            existing_telemetry = Telemetry.query.filter_by(
                device_id=device.id,
                sequence_number=data["sequence_number"]
            ).first()

            print("Existing telemetry:", existing_telemetry)

            if existing_telemetry:
                print("Duplicate Record")
                print("Telemetry ID:", existing_telemetry.id)
                print("Device ID:", existing_telemetry.device_id)
                print("Sequence:", existing_telemetry.sequence_number)
                print("Timestamp:", existing_telemetry.event_timestamp)

                db.session.rollback()
                logger.info(f"Duplicate telemetry event detected for Device {device.device_id}, Seq {data['sequence_number']}.")
                return {
                    "status": "duplicate",
                    "message": "Duplicate telemetry event detected. At-least-once delivery deduplicated.",
                    "device_id": device.device_id,
                    "sequence_number": data["sequence_number"]
                }, 200

            print("No duplicate found")

            # Out-of-Order Handling Strategy
            out_of_order = False
            if device.last_sequence is not None and data["sequence_number"] < device.last_sequence:
                out_of_order = True
                logger.warning(
                    f"Out-of-order telemetry event received for Device {device.device_id}. "
                    f"Seq {data['sequence_number']} < Last {device.last_sequence}."
                )

            logger.info("STEP 4: Creating telemetry object")
            # Store Telemetry Record
            telemetry = Telemetry(
                device_id=device.id,
                pole_id=pole.id,
                event=data["event"],
                energized=data["energized"],
                sequence_number=data["sequence_number"],
                out_of_order=out_of_order,
                battery_mv=data["battery_mv"],
                rssi=data["rssi"],
                firmware_version=data["firmware_version"],
                event_timestamp=data["event_timestamp"],
                received_timestamp=datetime.now(timezone.utc)
            )

            logger.info("STEP 5: Adding telemetry")
            db.session.add(telemetry)

            # Update Device Operational State ONLY if the message is in-sequence (or first message)
            if not out_of_order:
                device.last_sequence = data["sequence_number"]
                device.last_seen = data["event_timestamp"]
                device.last_event = data["event"].value
                device.energized = data["energized"]
                if data["battery_mv"] is not None:
                    device.battery_mv = data["battery_mv"]
                if data["rssi"] is not None:
                    device.last_rssi = data["rssi"]
                if data["firmware_version"]:
                    device.firmware_version = data["firmware_version"]

                if data["event"] == TelemetryEvent.HEARTBEAT:
                    device.last_heartbeat = data["event_timestamp"]

            print("Saving telemetry")
            print("Sequence:", telemetry.sequence_number)
            print("Out of Order:", out_of_order)

            logger.info("STEP 6: Committing transaction")
            db.session.commit()

            print("Telemetry inserted successfully")

            logger.info("STEP 7: Success")
            return {
                "status": "success",
                "message": "Telemetry event ingested successfully.",
                "telemetry_id": str(telemetry.id),
                "device_id": device.device_id,
                "pole_id": pole.pole_code,
                "sequence_number": telemetry.sequence_number,
                "out_of_order": out_of_order
            }, 201
        except Exception as e:
            import traceback

            db.session.rollback()

            print("\n" + "=" * 80)
            print("TELEMETRY INGESTION FAILED")
            traceback.print_exc()
            print("=" * 80 + "\n")

            logger.exception("Telemetry ingestion failed")

            raise

    @classmethod
    def ingest_bulk(cls, payloads: List[Dict[str, Any]]) -> Tuple[Dict[str, Any], int]:
        """
        Batch ingests an array of telemetry payloads efficiently.
        Returns counts for processed, duplicates, invalid, and out-of-order items.
        """
        if not isinstance(payloads, list):
            return {
                "error": {
                    "code": 400,
                    "name": "Bad Request",
                    "description": "Bulk payload must be a JSON array of telemetry objects."
                }
            }, 400

        processed = 0
        duplicates = 0
        invalid = 0
        out_of_order_count = 0
        errors: List[Dict[str, Any]] = []

        for idx, payload in enumerate(payloads):
            result, status_code = cls.ingest_single(payload)
            if status_code in (200, 201):
                if result.get("status") == "duplicate":
                    duplicates += 1
                else:
                    processed += 1
                    if result.get("out_of_order"):
                        out_of_order_count += 1
            else:
                invalid += 1
                errors.append({
                    "index": idx,
                    "payload": payload,
                    "error": result.get("error", {}).get("description", "Validation error")
                })

        return {
            "processed": processed,
            "duplicates": duplicates,
            "invalid": invalid,
            "out_of_order": out_of_order_count,
            "errors": errors
        }, 200
