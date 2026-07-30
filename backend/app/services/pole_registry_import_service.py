import csv
import io
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from app.database import db
from app.models import (
    Feeder,
    Transformer,
    Pole, PoleStatus, PoleType,
    Device, DeviceStatus
)

logger = logging.getLogger("pole_registry_import")


class PoleRegistryImportService:
    """
    Service responsible for reading, validating, and importing/updating
    electricity pole registry data from CSV files.
    """

    REQUIRED_HEADERS = {"pole_id", "lat", "lon", "feeder_id", "dt_id"}

    @classmethod
    def import_csv(cls, csv_content: str) -> Dict[str, Any]:
        """
        Parses CSV string content, validates schema and relationships,
        and performs an UPSERT (insert or update) for all valid records.
        """
        reader = csv.DictReader(io.StringIO(csv_content))
        if not reader.fieldnames:
            return {
                "total_rows": 0,
                "imported_count": 0,
                "updated_count": 0,
                "skipped_count": 0,
                "errors": [{"row": 0, "pole_id": "N/A", "error": "CSV file is empty or missing headers."}]
            }

        # Normalize header fieldnames (strip whitespace & lowercase)
        fieldnames = [f.strip().lower() for f in reader.fieldnames]
        missing_headers = cls.REQUIRED_HEADERS - set(fieldnames)
        if missing_headers:
            return {
                "total_rows": 0,
                "imported_count": 0,
                "updated_count": 0,
                "skipped_count": 0,
                "errors": [{
                    "row": 0,
                    "pole_id": "N/A",
                    "error": f"Missing required CSV columns: {', '.join(sorted(missing_headers))}"
                }]
            }

        # Cache existing feeders and transformers for fast validation
        feeders_by_code = {f.feeder_code: f for f in Feeder.query.all()}
        feeders_by_id = {str(f.id): f for f in feeders_by_code.values()}

        trfs_by_code = {t.transformer_code: t for t in Transformer.query.all()}
        trfs_by_id = {str(t.id): t for t in trfs_by_code.values()}

        # Cache existing poles by pole_code and id
        poles_by_code = {p.pole_code: p for p in Pole.query.all()}
        poles_by_id = {str(p.id): p for p in poles_by_code.values()}

        total_rows = 0
        imported_count = 0
        updated_count = 0
        skipped_count = 0
        errors: List[Dict[str, Any]] = []

        seen_csv_pole_ids = set()

        for idx, raw_row in enumerate(reader, start=2):  # Row 1 is header
            # Normalize keys
            row = {k.strip().lower(): (v.strip() if v else "") for k, v in raw_row.items() if k}
            
            # Skip blank rows
            if not any(row.values()):
                continue

            total_rows += 1
            pole_code = row.get("pole_id", "")
            if not pole_code:
                skipped_count += 1
                errors.append({"row": idx, "pole_id": "N/A", "error": "pole_id is required."})
                continue

            # Duplicate check within the same CSV upload
            if pole_code in seen_csv_pole_ids:
                skipped_count += 1
                errors.append({"row": idx, "pole_id": pole_code, "error": f"Duplicate pole_id '{pole_code}' in CSV."})
                continue
            seen_csv_pole_ids.add(pole_code)

            # Validate GPS coordinates
            try:
                lat = float(row.get("lat", ""))
                lon = float(row.get("lon", ""))
                if not (-90.0 <= lat <= 90.0) or not (-180.0 <= lon <= 180.0):
                    raise ValueError("Out of valid latitude (-90..90) or longitude (-180..180) range.")
            except ValueError as e:
                skipped_count += 1
                errors.append({"row": idx, "pole_id": pole_code, "error": f"Invalid GPS coordinates: {str(e)}"})
                continue

            # Validate Feeder reference
            feeder_ref = row.get("feeder_id", "")
            feeder = feeders_by_code.get(feeder_ref) or feeders_by_id.get(feeder_ref)
            if not feeder:
                skipped_count += 1
                errors.append({"row": idx, "pole_id": pole_code, "error": f"Feeder '{feeder_ref}' not found in database."})
                continue

            # Validate Transformer reference
            trf_ref = row.get("dt_id", "")
            transformer = trfs_by_code.get(trf_ref) or trfs_by_id.get(trf_ref)
            if not transformer:
                skipped_count += 1
                errors.append({"row": idx, "pole_id": pole_code, "error": f"Transformer/DT '{trf_ref}' not found in database."})
                continue

            # Parse optional parent pole reference
            parent_pole_ref = row.get("parent_pole_id", "")
            parent_pole = None
            if parent_pole_ref:
                parent_pole = poles_by_code.get(parent_pole_ref) or poles_by_id.get(parent_pole_ref)
                if not parent_pole and parent_pole_ref != pole_code:
                    # Parent pole might be in current CSV if defined earlier
                    pass

            # Parse optional sequence number
            seq_raw = row.get("seq_on_line", "")
            seq_on_line = None
            if seq_raw:
                try:
                    seq_on_line = int(seq_raw)
                except ValueError:
                    pass

            # Parse optional pole_type
            pole_type_raw = row.get("pole_type", "").upper()
            try:
                pole_type = PoleType[pole_type_raw] if pole_type_raw in PoleType.__members__ else PoleType.SUSPENSION
            except KeyError:
                pole_type = PoleType.SUSPENSION

            ward = row.get("ward", "") or None
            pincode = row.get("pincode", "") or None
            device_id_raw = row.get("device_id", "")
            device_installed = bool(device_id_raw)

            # Check if pole already exists in database (UPSERT logic)
            existing_pole = poles_by_code.get(pole_code) or poles_by_id.get(pole_code)

            if existing_pole:
                # Update existing pole attributes
                existing_pole.transformer_id = transformer.id
                existing_pole.feeder_id = feeder.id
                existing_pole.parent_pole_id = parent_pole.id if parent_pole else None
                existing_pole.seq_on_line = seq_on_line
                existing_pole.latitude = lat
                existing_pole.longitude = lon
                existing_pole.ward = ward
                existing_pole.pincode = pincode
                existing_pole.pole_type = pole_type
                existing_pole.device_installed = device_installed
                existing_pole.current_device_id = device_id_raw or None
                updated_count += 1
                target_pole = existing_pole
            else:
                # Insert new pole
                new_pole = Pole(
                    pole_code=pole_code,
                    transformer_id=transformer.id,
                    feeder_id=feeder.id,
                    parent_pole_id=parent_pole.id if parent_pole else None,
                    seq_on_line=seq_on_line,
                    latitude=lat,
                    longitude=lon,
                    ward=ward,
                    pincode=pincode,
                    pole_type=pole_type,
                    device_installed=device_installed,
                    current_device_id=device_id_raw or None,
                    status=PoleStatus.ACTIVE
                )
                db.session.add(new_pole)
                db.session.flush()
                poles_by_code[pole_code] = new_pole
                poles_by_id[str(new_pole.id)] = new_pole
                imported_count += 1
                target_pole = new_pole

            # Handle physical Device linking if device_id is present
            if device_id_raw:
                existing_device = Device.query.filter_by(device_id=device_id_raw).first()
                if existing_device:
                    existing_device.pole_id = target_pole.id
                    existing_device.active = True
                    existing_device.status = DeviceStatus.ACTIVE
                else:
                    new_device = Device(
                        device_id=device_id_raw,
                        pole_id=target_pole.id,
                        firmware_version="1.0.0",
                        active=True,
                        status=DeviceStatus.ACTIVE
                    )
                    db.session.add(new_device)

        db.session.commit()

        logger.info(
            f"Pole Registry Import complete: Total={total_rows}, "
            f"Imported={imported_count}, Updated={updated_count}, Skipped={skipped_count}"
        )

        return {
            "total_rows": total_rows,
            "imported_count": imported_count,
            "updated_count": updated_count,
            "skipped_count": skipped_count,
            "errors": errors
        }
