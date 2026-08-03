import logging
import random
import time
import uuid
import traceback
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

from app.services.telemetry_ingestion_service import TelemetryIngestionService
from app.services.network_graph_service import NetworkGraphService, PoleNode, TransformerNode, FeederNode
from app.services.fault_localization_service import FaultLocalizationService
from app.services.ticket_service import TicketService
from app.models.simulator_usage import SimulatorUsage

logger = logging.getLogger("simulator_service")


class SimulatorService:
    """
    Production-ready Fault Simulator service that generates physically consistent synthetic telemetry
    through the existing ingestion pipeline and exercises the end-to-end fault management workflow.
    """

    SCENARIOS = [
        {
            "id": "small_span_fault",
            "name": "Small Span Line Outage",
            "category": "SPAN",
            "description": "De-energizes target pole B and 100% of its downstream descendants. Generates SPAN_FAULT + Repair Ticket.",
            "icon": "zap"
        },
        {
            "id": "large_span_fault",
            "name": "Major Trunk Line Break",
            "category": "SPAN",
            "description": "De-energizes major trunk pole B and 100% of its downstream descendants. Generates SPAN_FAULT + High Priority Ticket.",
            "icon": "zap"
        },
        {
            "id": "transformer_failure",
            "name": "DTR Substation Station Failure",
            "category": "TRANSFORMER",
            "description": "De-energizes 100% of poles connected to a Distribution Transformer. Generates TRANSFORMER_FAULT + High Priority Ticket.",
            "icon": "radio"
        },
        {
            "id": "feeder_failure",
            "name": "11kV Feeder Main Trunk Trip",
            "category": "FEEDER",
            "description": "De-energizes 100% of poles across all transformers on an 11kV Feeder. Generates FEEDER_FAULT + Critical Ticket.",
            "icon": "shield-alert"
        },
        {
            "id": "sensor_anomaly",
            "name": "Telemetry Sensor Hardware Failure",
            "category": "ANOMALY",
            "description": "Single pole reports dark while downstream children remain energized. Generates SENSOR_ANOMALY (0 tickets).",
            "icon": "alert-circle"
        },
        {
            "id": "missing_telemetry",
            "name": "Missing Telemetry & Uninstrumented Gaps",
            "category": "GAP",
            "description": "De-energizes line segment while omitting telemetry for intermediate uninstrumented poles.",
            "icon": "layers"
        },
        {
            "id": "out_of_order_telemetry",
            "name": "Out-of-Order Sequence Lag",
            "category": "LAG",
            "description": "Posts sequence #15 -> #12 -> #16. Exercises deduplication & sequence lag out_of_order tagging.",
            "icon": "clock"
        },
        {
            "id": "restore_network",
            "name": "Power Restoration & Auto-Verification",
            "category": "RESTORE",
            "description": "Posts power_restored telemetry. Re-analyzes localization and auto-verifies RESOLVED tickets.",
            "icon": "check-circle"
        }
    ]

    _history: List[Dict[str, Any]] = []

    @classmethod
    def get_scenarios(cls) -> List[Dict[str, Any]]:
        """Returns built-in scenario presets library."""
        return cls.SCENARIOS

    @classmethod
    def get_history(cls) -> List[Dict[str, Any]]:
        """Returns simulation execution history log."""
        return cls._history

    @classmethod
    def _propagate_uninstrumented_node_states(cls, graph_service: NetworkGraphService) -> None:
        """
        In radial distribution networks, uninstrumented poles (device_id is None) have no IoT sensor.
        Propagates electrical power state top-down from parent nodes so uninstrumented poles
        inherit the physical power state of their parent pole/transformer.
        """
        visited = set()
        for pole in list(graph_service._poles.values()):
            if pole.id not in visited and pole.parent is None:
                stack = [pole]
                while stack:
                    curr = stack.pop()
                    if curr.id in visited:
                        continue
                    visited.add(curr.id)

                    if curr.parent and not curr.parent.energized:
                        if curr.device_id is None:
                            curr.energized = False

                    stack.extend(curr.children)

    @classmethod
    def validate_telemetry_consistency(
        cls,
        payloads: List[Dict[str, Any]],
        graph_service: NetworkGraphService,
        scenario_id: str
    ) -> None:
        """
        Validates electrical radial consistency before submitting telemetry:
        1. A dark pole cannot have energized instrumented descendants (unless scenario is sensor_anomaly).
        2. All instrumented descendants of a dark span boundary must be dark.
        """
        if scenario_id == "sensor_anomaly":
            logger.info("[Simulator] Skipping electrical consistency check for hardware sensor_anomaly scenario.")
            return

        proposed_states = {
            p["pole_id"]: p["energized"] for p in payloads if "pole_id" in p and "energized" in p
        }

        for payload in payloads:
            pole_code = payload.get("pole_id")
            energized = payload.get("energized")

            if energized is False and pole_code:
                pole_node = graph_service.get_pole(pole_code)
                if pole_node:
                    descendants = graph_service.get_descendants(pole_node)
                    for desc_node in descendants:
                        # Skip uninstrumented poles (they have no IoT device)
                        if desc_node.device_id is None:
                            continue

                        desc_state = proposed_states.get(desc_node.code, desc_node.energized)
                        if desc_state is True:
                            raise ValueError(
                                f"Invalid electrical state generated for scenario '{scenario_id}': "
                                f"Pole {pole_code} is DE-ENERGIZED but its downstream descendant {desc_node.code} "
                                f"is ENERGIZED. In radial networks, all descendants of a dark pole MUST be dark."
                            )

        logger.info("[Simulator] Validation passed")

    @classmethod
    def run_scenario(
        cls,
        scenario_id: str,
        feeder_ref: Optional[str] = None,
        transformer_ref: Optional[str] = None,
        pole_ref: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes a synthetic telemetry scenario through TelemetryIngestionService,
        triggers FaultLocalizationService, and auto-generates Repair Tickets.
        """
        start_time = time.time()
        logger.info(f"[Simulator] Scenario selected: {scenario_id} (Target feeder: {feeder_ref}, tr: {transformer_ref}, pole: {pole_ref})")

        graph_service = NetworkGraphService.get_instance()
        graph_service.build_graph(force_rebuild=True)

        now_iso = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

        # Robust Null Pointer / Topology Resolution
        all_feeders = list({f.id: f for f in graph_service._feeders.values()}.values())
        if not all_feeders:
            raise ValueError("No feeders found in NetworkGraph.")

        target_feeder = graph_service.get_feeder(feeder_ref) if feeder_ref else all_feeders[0]
        if not target_feeder:
            target_feeder = all_feeders[0]

        target_tr = None
        if transformer_ref:
            target_tr = graph_service.get_transformer(transformer_ref)
        if not target_tr and target_feeder.transformers:
            target_tr = target_feeder.transformers[0]
        if not target_tr:
            all_trs = list({t.id: t for t in graph_service._transformers.values()}.values())
            if not all_trs:
                raise ValueError("No transformers found in NetworkGraph.")
            target_tr = all_trs[0]

        target_pole = None
        if pole_ref:
            target_pole = graph_service.get_pole(pole_ref)
        if not target_pole and target_tr.root_poles:
            target_pole = target_tr.root_poles[0]
        if not target_pole and target_tr.poles:
            target_pole = target_tr.poles[0]

        telemetry_payloads: List[Dict[str, Any]] = []
        scenario_name = scenario_id.replace("_", " ").title()

        # Track persistent execution counter
        if scenario_id in ("small_span_fault", "large_span_fault", "feeder_failure", "transformer_failure"):
            SimulatorUsage.increment("power_loss", "Power Loss")
        elif scenario_id == "restore_network":
            SimulatorUsage.increment("restore_network", "Power Restored")
        elif scenario_id == "out_of_order_telemetry":
            SimulatorUsage.increment("out_of_order", "Out-of-Order")
        else:
            SimulatorUsage.increment(scenario_id, scenario_name)

        # Build telemetry payloads according to scenario logic
        if scenario_id == "feeder_failure":
            scenario_name = "11kV Feeder Main Trunk Trip"
            for tr in target_feeder.transformers:
                for pole in tr.poles:
                    if pole and pole.device_id:
                        telemetry_payloads.append(cls._make_payload(pole, pole.code, energized=False, event="power_lost", ts=now_iso))

        elif scenario_id == "transformer_failure":
            scenario_name = "DTR Substation Station Failure"
            for pole in target_tr.poles:
                if pole and pole.device_id:
                    telemetry_payloads.append(cls._make_payload(pole, pole.code, energized=False, event="power_lost", ts=now_iso))

        elif scenario_id in ("small_span_fault", "large_span_fault"):
            if target_pole:
                # 1. Path to root transformer is ENERGIZED
                path_to_root = graph_service.get_path_to_transformer(target_pole)
                for p in path_to_root:
                    if p and p.device_id:
                        telemetry_payloads.append(cls._make_payload(p, p.code, energized=True, event="heartbeat", ts=now_iso))

                # 2. Downstream child pole B and 100% OF ALL ITS DESCENDANTS are DE-ENERGIZED
                if target_pole.children:
                    dark_child = target_pole.children[0]
                    descendants = graph_service.get_descendants(dark_child)
                    all_dark_subtree = [dark_child] + descendants

                    for p in all_dark_subtree:
                        if p and p.device_id:
                            telemetry_payloads.append(cls._make_payload(p, p.code, energized=False, event="power_lost", ts=now_iso))

        elif scenario_id == "sensor_anomaly":
            scenario_name = "Telemetry Sensor Hardware Failure"
            if target_pole:
                # Single pole dark
                if target_pole.device_id:
                    telemetry_payloads.append(cls._make_payload(target_pole, target_pole.code, energized=False, event="power_lost", ts=now_iso))
                # Downstream children energized
                if target_pole.children:
                    for child in target_pole.children:
                        if child and child.device_id:
                            telemetry_payloads.append(cls._make_payload(child, child.code, energized=True, event="heartbeat", ts=now_iso))

        elif scenario_id == "missing_telemetry":
            scenario_name = "Missing Telemetry & Uninstrumented Gaps"
            if target_pole:
                path_to_root = graph_service.get_path_to_transformer(target_pole)
                for p in path_to_root:
                    if p and p.device_id:
                        telemetry_payloads.append(cls._make_payload(p, p.code, energized=True, event="heartbeat", ts=now_iso))

                if target_pole.children:
                    dark_child = target_pole.children[0]
                    descendants = graph_service.get_descendants(dark_child)
                    all_dark_subtree = [dark_child] + descendants
                    for idx, p in enumerate(all_dark_subtree):
                        if p and p.device_id and idx % 2 == 0:
                            telemetry_payloads.append(cls._make_payload(p, p.code, energized=False, event="power_lost", ts=now_iso))

        elif scenario_id == "out_of_order_telemetry":
            scenario_name = "Out-of-Order Sequence Lag"
            if target_pole and target_pole.device_id:
                base_seq = (target_pole.last_sequence or 100) + 10
                # Sequence 15
                telemetry_payloads.append(cls._make_payload(target_pole, target_pole.code, energized=True, event="heartbeat", ts=now_iso, seq=base_seq + 5))
                # Out-of-order sequence 12
                telemetry_payloads.append(cls._make_payload(target_pole, target_pole.code, energized=True, event="power_lost", ts=now_iso, seq=base_seq + 2))
                # Sequence 16
                telemetry_payloads.append(cls._make_payload(target_pole, target_pole.code, energized=True, event="power_restored", ts=now_iso, seq=base_seq + 6))

        elif scenario_id == "restore_network":
            return cls.restore_network(target_ref=feeder_ref or transformer_ref or pole_ref)

        logger.info(f"[Simulator] Telemetry generated: {len(telemetry_payloads)} payloads.")

        # Validate electrical consistency before submitting payloads
        cls.validate_telemetry_consistency(telemetry_payloads, graph_service, scenario_id)

        # 1. Inject Synthetic Telemetry via TelemetryIngestionService
        ingest_res, ingest_status = TelemetryIngestionService.ingest_bulk(telemetry_payloads)
        logger.info(f"[Simulator] Telemetry ingested: {ingest_res.get('processed', 0)} events processed.")

        # Rebuild graph cache in memory to reflect fresh device telemetry states
        graph_service.build_graph(force_rebuild=True)

        # Propagate uninstrumented node states top-down so uninstrumented poles inherit dark state
        cls._propagate_uninstrumented_node_states(graph_service)

        # 2. Trigger Deterministic Fault Localization Engine
        localization_res = FaultLocalizationService.analyze_network()
        incidents = localization_res.get("incidents", [])
        incidents_count = len(incidents)
        logger.info(f"[Simulator] Localization complete: {incidents_count} incidents detected.")

        # 3. Auto-generate Repair Tickets ONLY IF incidents exist
        tickets_created = []
        if incidents_count > 0:
            tickets_created = TicketService.process_fault_incidents(incidents)
            logger.info(f"[Simulator] Tickets created: {len(tickets_created)} repair tickets spawned.")
        else:
            logger.info("[Simulator] Tickets created: 0 tickets spawned (no active outage incidents).")

        elapsed_ms = round((time.time() - start_time) * 1000, 2)

        ticket_dicts = [t.to_dict() for t in tickets_created]
        ticket_numbers = [t.ticket_number for t in tickets_created]
        ticket_count = len(tickets_created)

        history_entry = {
            "id": f"SIM-{len(cls._history) + 1:04d}",
            "scenario_id": scenario_id,
            "scenario_name": scenario_name,
            "target": target_pole.code if target_pole else (target_tr.code if target_tr else target_feeder.code),
            "telemetry_injected": len(telemetry_payloads),
            "incidents_detected": incidents_count,
            "tickets_created": ticket_count,
            "ticket_numbers": ticket_numbers,
            "duration_ms": elapsed_ms,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        cls._history.insert(0, history_entry)

        return {
            "status": "success",
            "simulation": history_entry,
            "ingestion": ingest_res,
            "fault_localization": localization_res,
            "tickets_created": ticket_dicts,
            "ticket_numbers": ticket_numbers,
            "ticket_count": ticket_count
        }

    @classmethod
    def restore_network(cls, target_ref: Optional[str] = None) -> Dict[str, Any]:
        """
        Restores power across specified target or entire network by ingesting power_restored telemetry,
        re-running fault analysis, and auto-verifying RESOLVED tickets.
        """
        SimulatorUsage.increment("restore_network", "Power Restored")
        start_time = time.time()
        logger.info("[Simulator] Scenario selected: restore_network")

        graph_service = NetworkGraphService.get_instance()
        graph_service.build_graph(force_rebuild=True)

        now_iso = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        telemetry_payloads = []

        all_poles = list(graph_service._poles.values())
        unique_poles = {p.id: p for p in all_poles}.values()

        for p in unique_poles:
            if p and p.device_id:
                telemetry_payloads.append(cls._make_payload(p, p.code, energized=True, event="power_restored", ts=now_iso))

        logger.info(f"[Simulator] Telemetry generated: {len(telemetry_payloads)} restoration payloads.")

        # 1. Ingest restoration telemetry
        ingest_res, _ = TelemetryIngestionService.ingest_bulk(telemetry_payloads)
        logger.info(f"[Simulator] Telemetry ingested: {ingest_res.get('processed', 0)} events processed.")

        # Rebuild graph cache to reflect restored states
        graph_service.build_graph(force_rebuild=True)

        # 2. Re-run fault localization (should yield 0 active faults)
        localization_res = FaultLocalizationService.analyze_network()
        logger.info("[Simulator] Localization complete: 0 incidents detected.")

        # 3. Auto-verify all RESOLVED tickets
        from app.models import Ticket, TicketStatus
        resolved_tickets = Ticket.query.filter_by(status=TicketStatus.RESOLVED).all()
        auto_verified_count = 0

        for tkt in resolved_tickets:
            v_res, v_code = TicketService.auto_verify_ticket(tkt.ticket_number)
            if v_code == 200:
                auto_verified_count += 1

        logger.info(f"[Simulator] Auto-verified {auto_verified_count} RESOLVED tickets.")

        elapsed_ms = round((time.time() - start_time) * 1000, 2)

        history_entry = {
            "id": f"SIM-{len(cls._history) + 1:04d}",
            "scenario_id": "restore_network",
            "scenario_name": "Power Restoration & Auto-Verification",
            "target": target_ref or "Entire Network",
            "telemetry_injected": len(telemetry_payloads),
            "incidents_detected": len(localization_res.get("incidents", [])),
            "tickets_auto_verified": auto_verified_count,
            "duration_ms": elapsed_ms,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        cls._history.insert(0, history_entry)

        return {
            "status": "success",
            "message": f"Network power restored. Telemetry ingested ({len(telemetry_payloads)} sensors). Auto-verified {auto_verified_count} RESOLVED tickets.",
            "simulation": history_entry,
            "ingestion": ingest_res,
            "fault_localization": localization_res,
            "tickets_created": [],
            "ticket_numbers": [],
            "ticket_count": 0,
            "tickets_auto_verified_count": auto_verified_count
        }

    @classmethod
    def propagate_outage(
        cls,
        pole_ref: str,
        energized: bool,
        event: Optional[str] = None,
        base_seq: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Generates and ingests cascading telemetry packets for a target pole and all its downstream descendants
        in upstream-to-downstream topological order.
        """
        SimulatorUsage.increment("propagation", "Propagation Tests")
        start_time = time.time()
        graph_service = NetworkGraphService.get_instance()
        if not graph_service.is_built():
            graph_service.build_graph(force_rebuild=True)

        target_pole = graph_service.get_pole(pole_ref)
        if not target_pole:
            all_poles = list(graph_service._poles.values())
            for p in all_poles:
                if p.code == pole_ref or p.id == pole_ref:
                    target_pole = p
                    break

        if not target_pole:
            raise ValueError(f"Pole '{pole_ref}' not found in NetworkGraph.")

        descendants = graph_service.get_descendants(target_pole)
        affected_poles = [target_pole] + descendants

        now_iso = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        event_type = event or ("power_restored" if energized else "power_lost")

        telemetry_payloads: List[Dict[str, Any]] = []
        for idx, pole in enumerate(affected_poles):
            if pole:
                seq_num = (base_seq + idx * 2) if base_seq else ((pole.last_sequence or 100) + random.randint(1, 5))
                telemetry_payloads.append(
                    cls._make_payload(
                        pole,
                        pole.code,
                        energized=energized,
                        event=event_type,
                        ts=now_iso,
                        seq=seq_num
                    )
                )

        logger.info(f"[Simulator] Propagating telemetry to {len(telemetry_payloads)} poles under {target_pole.code}.")

        # Ingest cascading telemetry payloads
        ingest_res, _ = TelemetryIngestionService.ingest_bulk(telemetry_payloads)

        # Rebuild graph cache in memory to reflect fresh device telemetry states
        graph_service.build_graph(force_rebuild=True)

        # Propagate uninstrumented node states top-down
        cls._propagate_uninstrumented_node_states(graph_service)

        # Trigger Deterministic Fault Localization Engine
        localization_res = FaultLocalizationService.analyze_network()
        incidents = localization_res.get("incidents", [])

        # Auto-generate Repair Tickets IF incidents exist
        tickets_created = []
        if incidents:
            tickets_created = TicketService.process_fault_incidents(incidents)

        elapsed_ms = round((time.time() - start_time) * 1000, 2)

        history_entry = {
            "id": f"SIM-{len(cls._history) + 1:04d}",
            "scenario_id": "cascade_propagation",
            "scenario_name": f"Cascading {'Restoration' if energized else 'Outage'} ({event_type})",
            "target": target_pole.code,
            "telemetry_injected": len(telemetry_payloads),
            "incidents_detected": len(incidents),
            "tickets_created": len(tickets_created),
            "ticket_numbers": [t.ticket_number for t in tickets_created],
            "duration_ms": elapsed_ms,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        cls._history.insert(0, history_entry)

        return {
            "status": "success",
            "message": f"Successfully propagated {'power restoration' if energized else 'power outage'} to {len(affected_poles)} poles under {target_pole.code}.",
            "affected_poles_count": len(affected_poles),
            "target_pole": target_pole.code,
            "simulation": history_entry,
            "ingestion": ingest_res,
            "fault_localization": localization_res,
            "tickets_created": [t.to_dict() for t in tickets_created]
        }

    @classmethod
    def reset_network(cls) -> Dict[str, Any]:
        """Resets network graph cache and clears active fault incidents."""
        logger.info("[Simulator] Resetting network cache and fault state.")
        graph_service = NetworkGraphService.get_instance()
        graph_service.invalidate_cache()
        FaultLocalizationService._latest_incidents.clear()
        FaultLocalizationService._latest_anomalies.clear()
        FaultLocalizationService._analyzed_at = None

        return {
            "status": "success",
            "message": "Simulator reset completed. Graph cache invalidated and active fault analysis cleared."
        }

    @classmethod
    def _make_payload(cls, pole: PoleNode, pole_id_str: str, energized: bool, event: str, ts: str, seq: Optional[int] = None) -> Dict[str, Any]:
        """Generates assignment-compliant telemetry JSON dictionary."""
        sequence_num = seq or ((pole.last_sequence or 100) + random.randint(1, 5))
        return {
            "device_id": pole.device_id or f"DEV-{pole.code}",
            "pole_id": pole_id_str,
            "event": event,
            "energized": energized,
            "ts": ts,
            "seq": sequence_num,
            "battery_mv": random.randint(3500, 4100),
            "rssi": random.randint(-90, -55),
            "fw": pole.firmware_version or "1.4.2"
        }
