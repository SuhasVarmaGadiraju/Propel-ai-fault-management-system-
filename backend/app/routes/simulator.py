import logging
import traceback
import uuid
from flask import Blueprint, request, jsonify
from app.services import SimulatorService

logger = logging.getLogger("simulator_routes")
simulator_bp = Blueprint("simulator", __name__)


@simulator_bp.route("/scenarios", methods=["GET"])
def get_scenarios():
    """
    GET /api/v1/simulator/scenarios
    Returns list of available built-in fault simulation scenarios.
    """
    scenarios = SimulatorService.get_scenarios()
    return jsonify(scenarios), 200


@simulator_bp.route("/history", methods=["GET"])
def get_history():
    """
    GET /api/v1/simulator/history
    Returns simulation execution history audit trail.
    """
    history = SimulatorService.get_history()
    return jsonify(history), 200


@simulator_bp.route("/run", methods=["POST"])
def run_simulation():
    """
    POST /api/v1/simulator/run
    Executes a synthetic outage scenario, posts telemetry via ingestion pipeline,
    runs deterministic fault localization, and auto-generates repair tickets.
    """
    payload = request.get_json(silent=True) or {}
    scenario_id = payload.get("scenario_id", "small_span_fault")
    feeder_ref = payload.get("feeder_id") or payload.get("feeder_code")
    transformer_ref = payload.get("transformer_id") or payload.get("transformer_code")
    pole_ref = payload.get("pole_id") or payload.get("pole_code")

    try:
        result = SimulatorService.run_scenario(
            scenario_id=scenario_id,
            feeder_ref=feeder_ref,
            transformer_ref=transformer_ref,
            pole_ref=pole_ref
        )
        return jsonify(result), 200

    except ValueError as val_err:
        # Electrical consistency validation error -> HTTP 400 Bad Request
        logger.warning(f"[Simulator] Validation failed: {val_err}")
        return jsonify({
            "status": "error",
            "message": str(val_err),
            "error": "Electrical Consistency Validation Error"
        }), 400

    except Exception as exc:
        trace_id = str(uuid.uuid4())
        tb = traceback.extract_tb(exc.__traceback__)[-1]
        error_location = f"{tb.filename}:{tb.lineno} in {tb.name}()"

        logger.error(
            f"[Simulator] Unexpected exception during run_scenario execution:\n"
            f"  Trace ID: {trace_id}\n"
            f"  Exception: {exc.__class__.__name__}: {exc}\n"
            f"  Location: {error_location}\n"
            f"{traceback.format_exc()}"
        )

        return jsonify({
            "status": "error",
            "message": str(exc),
            "exception": exc.__class__.__name__,
            "location": error_location,
            "trace_id": trace_id
        }), 500


@simulator_bp.route("/restore", methods=["POST"])
def restore_power():
    """
    POST /api/v1/simulator/restore
    Ingests power_restored telemetry, re-analyzes network, and auto-verifies RESOLVED tickets.
    """
    payload = request.get_json(silent=True) or {}
    target_ref = payload.get("target_id") or payload.get("target_code")

    try:
        result = SimulatorService.restore_network(target_ref=target_ref)
        return jsonify(result), 200
    except Exception as exc:
        trace_id = str(uuid.uuid4())
        tb = traceback.extract_tb(exc.__traceback__)[-1]
        error_location = f"{tb.filename}:{tb.lineno} in {tb.name}()"

        logger.error(f"[Simulator] Unexpected exception during restore_power: {exc}\n{traceback.format_exc()}")
        return jsonify({
            "status": "error",
            "message": str(exc),
            "exception": exc.__class__.__name__,
            "location": error_location,
            "trace_id": trace_id
        }), 500


@simulator_bp.route("/propagate", methods=["POST"])
def propagate_outage():
    """
    POST /api/v1/simulator/propagate
    Generates and ingests cascading telemetry packets for a target pole and all its downstream descendants.
    """
    payload = request.get_json(silent=True) or {}
    pole_ref = payload.get("pole_id") or payload.get("pole_code") or payload.get("target_id")
    energized = payload.get("energized", False)
    event = payload.get("event")
    seq = payload.get("seq")

    if not pole_ref:
        return jsonify({
            "status": "error",
            "message": "Missing required parameter 'pole_id' or 'pole_code'."
        }), 400

    try:
        result = SimulatorService.propagate_outage(
            pole_ref=pole_ref,
            energized=bool(energized),
            event=event,
            base_seq=int(seq) if seq is not None else None
        )
        return jsonify(result), 200
    except ValueError as val_err:
        return jsonify({
            "status": "error",
            "message": str(val_err)
        }), 400
    except Exception as exc:
        logger.error(f"[Simulator] Exception in propagate_outage: {exc}\n{traceback.format_exc()}")
        return jsonify({
            "status": "error",
            "message": str(exc)
        }), 500


@simulator_bp.route("/track", methods=["POST"])
def track_usage():
    """
    POST /api/v1/simulator/track
    Increments SimulatorUsage counter for custom simulator testing actions.
    """
    payload = request.get_json(silent=True) or {}
    action = payload.get("action") or payload.get("scenario_key")
    label = payload.get("label")

    if not action:
        return jsonify({
            "status": "error",
            "message": "Missing required field 'action' or 'scenario_key'."
        }), 400

    from app.models.simulator_usage import SimulatorUsage
    rec = SimulatorUsage.increment(action, label)
    return jsonify({
        "status": "success",
        "usage": rec.to_dict() if rec else None
    }), 200


@simulator_bp.route("/reset", methods=["POST"])
def reset_simulation():
    """
    POST /api/v1/simulator/reset
    Resets graph cache and clears active fault analysis state.
    """
    try:
        result = SimulatorService.reset_network()
        return jsonify(result), 200
    except Exception as exc:
        logger.error(f"[Simulator] Unexpected exception during reset_simulation: {exc}")
        return jsonify({
            "status": "error",
            "message": str(exc),
            "exception": exc.__class__.__name__
        }), 500
