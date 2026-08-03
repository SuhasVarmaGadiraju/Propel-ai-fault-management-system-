import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

from app.services.network_graph_service import (
    NetworkGraphService,
    FeederNode,
    TransformerNode,
    PoleNode,
)

logger = logging.getLogger("fault_localization_service")


class FaultLocalizationService:
    """
    Advanced deterministic fault localization engine supporting:
    - Span, Transformer, Feeder, and UNKNOWN_SPAN fault detection
    - Gap traversal across uninstrumented poles (possible_fault_range)
    - 0-100% confidence scoring with explicit deduction reasons
    - Step-by-step narrative explanation engine (reasoning)
    """

    _latest_incidents: List[Dict[str, Any]] = []
    _latest_anomalies: List[Dict[str, Any]] = []
    _analyzed_at: Optional[datetime] = None

    @classmethod
    def calculate_confidence(
        cls,
        fault_type: str,
        topology_known: bool,
        affected_nodes: List[PoleNode],
        has_uninstrumented_gaps: bool = False
    ) -> tuple[int, str]:
        """
        Calculates confidence score (0-100%) and returns (score, reason_string).
        Base score: 100%. Deductions applied deterministically.
        """
        score = 100
        deductions = []

        if not topology_known or fault_type == "UNKNOWN_SPAN":
            score -= 25
            deductions.append("Unknown line topology (-25%)")

        if has_uninstrumented_gaps:
            score -= 15
            deductions.append("Gaps in IoT device instrumentation (-15%)")

        # Check for stale or out-of-order telemetry in affected nodes
        stale_count = 0
        out_of_order_count = 0
        for node in affected_nodes:
            if node.out_of_order:
                out_of_order_count += 1

        if out_of_order_count > 0:
            score -= 10
            deductions.append(f"Sequence lag on {out_of_order_count} telemetry sensor(s) (-10%)")

        # Clamp score between 10% and 100%
        score = max(10, min(100, score))

        reason_str = "High certainty (Known topology, active sensors)"
        if deductions:
            reason_str = "Deductions: " + ", ".join(deductions)

        return score, reason_str

    @classmethod
    def analyze_network(cls) -> Dict[str, Any]:
        """
        Executes deterministic fault localization across all feeders, transformers, and poles.
        Returns active fault incidents, sensor anomalies, and summary counters.
        """
        graph_service = NetworkGraphService.get_instance()
        if not graph_service.is_built():
            graph_service.build_graph()

        incidents: List[Dict[str, Any]] = []
        anomalies: List[Dict[str, Any]] = []
        incident_counter = 1

        now_iso = datetime.now(timezone.utc).isoformat()

        # Iterate over all unique feeders in network
        unique_feeders = list({f.id: f for f in graph_service._feeders.values()}.values())

        for feeder in unique_feeders:
            all_feeder_poles = [
                p for tr in feeder.transformers for p in tr.poles
            ]
            installed_feeder_poles = [
                p for p in all_feeder_poles if p.device_id is not None
            ]

            # 1. Feeder Fault Detection
            if installed_feeder_poles and all(not p.energized for p in installed_feeder_poles):
                confidence, conf_reason = cls.calculate_confidence(
                    "FEEDER_FAULT", topology_known=True, affected_nodes=all_feeder_poles
                )
                reasoning = [
                    f"Feeder {feeder.code} main 11kV trunk monitored across {len(feeder.transformers)} transformers.",
                    f"100% of installed IoT pole devices ({len(installed_feeder_poles)} sensors) report DE-ENERGIZED.",
                    f"Feeder-level circuit breaker trip diagnosed on Feeder {feeder.code}.",
                    f"Confidence score {confidence}% ({conf_reason})."
                ]

                incident = {
                    "incident_id": f"INC-FDR-{incident_counter:04d}",
                    "fault_type": "FEEDER_FAULT",
                    "feeder_id": feeder.id,
                    "feeder_code": feeder.code,
                    "transformer_id": None,
                    "transformer_code": None,
                    "upstream_pole": None,
                    "downstream_pole": None,
                    "possible_fault_range": [p.code for p in all_feeder_poles[:5]],
                    "affected_poles": [p.code for p in all_feeder_poles],
                    "affected_poles_count": len(all_feeder_poles),
                    "estimated_households": len(all_feeder_poles) * 4,
                    "topology_known": True,
                    "confidence": confidence,
                    "confidence_reason": conf_reason,
                    "reasoning": reasoning,
                    "reason": f"All transformers and poles under 11kV Feeder {feeder.code} are completely de-energized.",
                    "detected_at": now_iso
                }
                incidents.append(incident)
                incident_counter += 1
                continue  # Feeder trip covers all downstream poles

            # 2. Transformer (DT), Unknown Span, & Span Fault Detection
            for tr in feeder.transformers:
                installed_tr_poles = [p for p in tr.poles if p.device_id is not None]

                # Transformer Fault Detection
                if installed_tr_poles and all(not p.energized for p in installed_tr_poles):
                    topology_known = all(p.topology_known for p in tr.poles)
                    confidence, conf_reason = cls.calculate_confidence(
                        "TRANSFORMER_FAULT", topology_known=topology_known, affected_nodes=tr.poles
                    )
                    reasoning = [
                        f"Distribution Transformer {tr.code} monitored across {len(tr.poles)} total poles.",
                        f"100% of installed pole sensors under transformer {tr.code} report DE-ENERGIZED.",
                        f"Other transformers on Feeder {feeder.code} remain energized.",
                        f"Transformer outage localized to DTR station {tr.code}.",
                        f"Confidence score {confidence}% ({conf_reason})."
                    ]

                    incident = {
                        "incident_id": f"INC-TRF-{incident_counter:04d}",
                        "fault_type": "TRANSFORMER_FAULT",
                        "feeder_id": feeder.id,
                        "feeder_code": feeder.code,
                        "transformer_id": tr.id,
                        "transformer_code": tr.code,
                        "upstream_pole": None,
                        "downstream_pole": None,
                        "possible_fault_range": [p.code for p in tr.poles[:5]],
                        "affected_poles": [p.code for p in tr.poles],
                        "affected_poles_count": len(tr.poles),
                        "estimated_households": len(tr.poles) * 4,
                        "topology_known": topology_known,
                        "confidence": confidence,
                        "confidence_reason": conf_reason,
                        "reasoning": reasoning,
                        "reason": f"Distribution Transformer {tr.code} is completely de-energized across all downstream poles.",
                        "detected_at": now_iso
                    }
                    incidents.append(incident)
                    incident_counter += 1
                    continue  # Transformer trip covers all poles under this DT

                # Check Unknown Topology Fallback (UNKNOWN_SPAN)
                unknown_poles = [p for p in tr.poles if not p.topology_known]
                dark_unknown_poles = [p for p in unknown_poles if p.device_id and not p.energized]
                if dark_unknown_poles and len(dark_unknown_poles) < len(installed_tr_poles):
                    confidence, conf_reason = cls.calculate_confidence(
                        "UNKNOWN_SPAN", topology_known=False, affected_nodes=dark_unknown_poles
                    )
                    dark_codes = [p.code for p in dark_unknown_poles]
                    area_name = dark_unknown_poles[0].ward or dark_unknown_poles[0].pin_code or tr.code
                    reasoning = [
                        f"Dark telemetry detected on {len(dark_unknown_poles)} pole(s) under Transformer {tr.code}.",
                        f"Topology is unlinked (parent_pole_id = NULL) for area {area_name}.",
                        f"Exact upstream/downstream span boundary cannot be isolated due to missing parent links.",
                        f"Fallback localized to UNKNOWN_SPAN in area {area_name}.",
                        f"Confidence score {confidence}% ({conf_reason})."
                    ]

                    incident = {
                        "incident_id": f"INC-UNK-{incident_counter:04d}",
                        "fault_type": "UNKNOWN_SPAN",
                        "feeder_id": feeder.id,
                        "feeder_code": feeder.code,
                        "transformer_id": tr.id,
                        "transformer_code": tr.code,
                        "upstream_pole": None,
                        "downstream_pole": None,
                        "estimated_area": area_name,
                        "possible_poles": dark_codes,
                        "possible_fault_range": dark_codes,
                        "affected_poles": dark_codes,
                        "affected_poles_count": len(dark_codes),
                        "estimated_households": len(dark_codes) * 4,
                        "topology_known": False,
                        "confidence": confidence,
                        "confidence_reason": conf_reason,
                        "reasoning": reasoning,
                        "reason": f"Unknown topology line fault detected in area {area_name} under Transformer {tr.code}.",
                        "detected_at": now_iso
                    }
                    incidents.append(incident)
                    incident_counter += 1
                    continue

                # Check Root Span Fault Detection (De-energized root pole with known topology)
                for root_pole in tr.root_poles:
                    if not root_pole.energized and root_pole.topology_known:
                        descendants = graph_service.get_descendants(root_pole)
                        # Ensure not a sensor anomaly (i.e. not dark root pole with ALL energized children)
                        children_energized = any(c.energized for c in root_pole.children) if root_pole.children else False
                        if not children_energized:
                            dark_descendants = [d for d in descendants if not d.energized]
                            affected_nodes = [root_pole] + dark_descendants
                            affected_codes = [n.code for n in affected_nodes]

                            confidence, conf_reason = cls.calculate_confidence(
                                "ROOT_SPAN_FAULT",
                                topology_known=True,
                                affected_nodes=affected_nodes
                            )

                            reasoning = [
                                f"Root Pole {root_pole.code} has no upstream parent pole in network tree topology.",
                                f"Standard SPAN_FAULT detection requires an energized upstream parent, which cannot apply to root poles.",
                                f"Root Pole {root_pole.code} is DE-ENERGIZED, but other transformers/feeders remain active.",
                                f"Evaluated Feeder {feeder.code} and Transformer {tr.code} outage rules (did not match complete station outages).",
                                f"Fault localized to transformer output / root span at Pole {root_pole.code}.",
                                f"Confidence score {confidence}% ({conf_reason})."
                            ]

                            incident = {
                                "incident_id": f"INC-RSPN-{incident_counter:04d}",
                                "fault_type": "ROOT_SPAN_FAULT",
                                "feeder_id": feeder.id,
                                "feeder_code": feeder.code,
                                "transformer_id": tr.id,
                                "transformer_code": tr.code,
                                "upstream_pole": None,
                                "downstream_pole": root_pole.code,
                                "possible_fault_range": [tr.code, root_pole.code],
                                "affected_poles": affected_codes,
                                "affected_poles_count": len(affected_codes),
                                "estimated_households": len(affected_codes) * 4,
                                "topology_known": True,
                                "confidence": confidence,
                                "confidence_reason": conf_reason,
                                "reasoning": reasoning,
                                "reason": f"Root span fault localized between Transformer {tr.code} output and Root Pole {root_pole.code}.",
                                "detected_at": now_iso
                            }
                            incidents.append(incident)
                            incident_counter += 1

                # Span Fault & Sensor Anomaly Detection (Tree Traversal)
                visited_poles = set()
                for root_pole in tr.root_poles:
                    cls._analyze_pole_subtree(
                        pole=root_pole,
                        feeder=feeder,
                        transformer=tr,
                        graph_service=graph_service,
                        incidents=incidents,
                        anomalies=anomalies,
                        counter=incident_counter,
                        now_iso=now_iso,
                        visited=visited_poles
                    )
                    incident_counter = len(incidents) + 1

        cls._latest_incidents = incidents
        cls._latest_anomalies = anomalies
        cls._analyzed_at = datetime.now(timezone.utc)

        span_faults = sum(1 for i in incidents if i["fault_type"] in ("SPAN_FAULT", "UNKNOWN_SPAN", "ROOT_SPAN_FAULT"))
        transformer_faults = sum(1 for i in incidents if i["fault_type"] == "TRANSFORMER_FAULT")
        feeder_faults = sum(1 for i in incidents if i["fault_type"] == "FEEDER_FAULT")
        total_affected_poles = sum(i["affected_poles_count"] for i in incidents)

        return {
            "summary": {
                "total_incidents": len(incidents),
                "span_faults": span_faults,
                "transformer_faults": transformer_faults,
                "feeder_faults": feeder_faults,
                "sensor_anomalies": len(anomalies),
                "total_affected_poles": total_affected_poles,
                "total_estimated_households": total_affected_poles * 4,
                "analyzed_at": now_iso
            },
            "incidents": incidents,
            "sensor_anomalies": anomalies
        }

    @classmethod
    def _analyze_pole_subtree(
        cls,
        pole: PoleNode,
        feeder: FeederNode,
        transformer: TransformerNode,
        graph_service: NetworkGraphService,
        incidents: List[Dict[str, Any]],
        anomalies: List[Dict[str, Any]],
        counter: int,
        now_iso: str,
        visited: set
    ) -> None:
        """Recursive tree traversal to detect live/dark span boundaries, gap ranges, and sensor glitches."""
        if pole.id in visited:
            return
        visited.add(pole.id)

        # Check Sensor Anomaly: Pole is dark BUT has energized downstream children
        if not pole.energized:
            children_energized = any(child.energized for child in pole.children)
            if children_energized:
                anomalies.append({
                    "pole_code": pole.code,
                    "device_id": pole.device_id,
                    "transformer_code": transformer.code,
                    "feeder_code": feeder.code,
                    "reason": f"Pole {pole.code} reports dark (unpowered), but downstream child poles report energized. Telemetry sensor failure."
                })
                # Continue analyzing children since power is physically flowing
                for child in pole.children:
                    cls._analyze_pole_subtree(
                        child, feeder, transformer, graph_service, incidents, anomalies, counter, now_iso, visited
                    )
                return

        # Upstream pole is ENERGIZED -> check downstream children for dark boundary
        if pole.energized:
            for child in pole.children:
                if not child.energized:
                    # Check if child is a sensor anomaly (has energized descendants)
                    descendants = graph_service.get_descendants(child)
                    if any(d.energized for d in descendants):
                        # Sensor anomaly on child
                        anomalies.append({
                            "pole_code": child.code,
                            "device_id": child.device_id,
                            "transformer_code": transformer.code,
                            "feeder_code": feeder.code,
                            "reason": f"Pole {child.code} reports dark, but downstream descendants report energized. Telemetry sensor failure."
                        })
                        cls._analyze_pole_subtree(
                            child, feeder, transformer, graph_service, incidents, anomalies, counter, now_iso, visited
                        )
                    else:
                        # Genuine Span Fault between pole (upstream) and child (downstream)
                        affected_nodes = [child] + descendants
                        affected_codes = [n.code for n in affected_nodes]

                        # Check for uninstrumented gap poles between upstream pole and downstream child
                        uninstrumented_gaps = [n for n in affected_nodes if n.device_id is None]
                        has_gaps = len(uninstrumented_gaps) > 0

                        fault_range = [pole.code] + [g.code for g in uninstrumented_gaps] + [child.code]

                        topology_known = pole.topology_known and child.topology_known
                        confidence, conf_reason = cls.calculate_confidence(
                            "SPAN_FAULT",
                            topology_known=topology_known,
                            affected_nodes=affected_nodes,
                            has_uninstrumented_gaps=has_gaps
                        )

                        reasoning = [
                            f"Upstream Pole {pole.code} is ENERGIZED (power active).",
                            f"Downstream Pole {child.code} is DARK (power lost).",
                        ]
                        if has_gaps:
                            reasoning.append(f"Uninstrumented pole gaps ({len(uninstrumented_gaps)}) present in line segment.")
                        reasoning.append(f"All downstream descendant poles ({len(descendants)} poles) are dark.")
                        reasoning.append(f"Fault localized to span line segment {pole.code} → {child.code}.")
                        reasoning.append(f"Confidence score {confidence}% ({conf_reason}).")

                        inc_id = f"INC-SPAN-{len(incidents) + 1:04d}"
                        incident = {
                            "incident_id": inc_id,
                            "fault_type": "SPAN_FAULT",
                            "feeder_id": feeder.id,
                            "feeder_code": feeder.code,
                            "transformer_id": transformer.id,
                            "transformer_code": transformer.code,
                            "upstream_pole": pole.code,
                            "downstream_pole": child.code,
                            "possible_fault_range": fault_range,
                            "affected_poles": affected_codes,
                            "affected_poles_count": len(affected_codes),
                            "estimated_households": len(affected_codes) * 4,
                            "topology_known": topology_known,
                            "confidence": confidence,
                            "confidence_reason": conf_reason,
                            "reasoning": reasoning,
                            "reason": f"Line break on span between upstream Pole {pole.code} (energized) and downstream Pole {child.code} (dark).",
                            "detected_at": now_iso
                        }
                        incidents.append(incident)
                else:
                    # Child is energized -> recurse down child subtree
                    cls._analyze_pole_subtree(
                        child, feeder, transformer, graph_service, incidents, anomalies, counter, now_iso, visited
                    )

    @classmethod
    def get_latest_results(cls) -> Dict[str, Any]:
        """Returns cached latest fault localization results or triggers fresh analysis."""
        if cls._analyzed_at is None:
            return cls.analyze_network()

        span_faults = sum(1 for i in cls._latest_incidents if i["fault_type"] in ("SPAN_FAULT", "UNKNOWN_SPAN", "ROOT_SPAN_FAULT"))
        transformer_faults = sum(1 for i in cls._latest_incidents if i["fault_type"] == "TRANSFORMER_FAULT")
        feeder_faults = sum(1 for i in cls._latest_incidents if i["fault_type"] == "FEEDER_FAULT")
        total_affected_poles = sum(i["affected_poles_count"] for i in cls._latest_incidents)

        return {
            "summary": {
                "total_incidents": len(cls._latest_incidents),
                "span_faults": span_faults,
                "transformer_faults": transformer_faults,
                "feeder_faults": feeder_faults,
                "sensor_anomalies": len(cls._latest_anomalies),
                "total_affected_poles": total_affected_poles,
                "total_estimated_households": total_affected_poles * 4,
                "analyzed_at": cls._analyzed_at.isoformat()
            },
            "incidents": cls._latest_incidents,
            "sensor_anomalies": cls._latest_anomalies
        }
