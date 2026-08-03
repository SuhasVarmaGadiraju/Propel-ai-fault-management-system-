import logging
import threading
import traceback
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import joinedload

from app.database import db
from app.models import Feeder, Transformer, Pole, Device, Telemetry

logger = logging.getLogger("network_graph_service")


class PoleNode:
    """In-memory node representation of a physical distribution pole."""

    def __init__(
        self,
        pole_id: str,
        pole_code: str,
        transformer_id: Optional[str] = None,
        parent_pole_id: Optional[str] = None,
        seq_on_line: Optional[int] = None,
        ward: Optional[str] = None,
        pin_code: Optional[str] = None,
        latitude: float = 0.0,
        longitude: float = 0.0,
        device_id: Optional[str] = None,
        device_status: Optional[str] = None,
        firmware_version: Optional[str] = None,
        energized: bool = True,
        last_event: Optional[str] = None,
        last_sequence: Optional[int] = None,
        battery_mv: Optional[int] = None,
        last_rssi: Optional[int] = None,
        last_seen: Optional[str] = None,
        out_of_order: bool = False,
    ):
        self.id = str(pole_id)
        self.code = pole_code
        self.transformer_id = str(transformer_id) if transformer_id else None
        self.parent_pole_id = str(parent_pole_id) if parent_pole_id else None
        self.seq_on_line = seq_on_line
        self.ward = ward
        self.pin_code = pin_code
        self.latitude = latitude
        self.longitude = longitude

        # Topology Known logic: Known if parent link or sequence on line exists
        self.topology_known = bool(self.parent_pole_id is not None or self.seq_on_line == 1)

        # Device & Telemetry state
        self.device_id = device_id
        self.device_status = device_status
        self.firmware_version = firmware_version
        self.energized = energized
        self.last_event = last_event
        self.last_sequence = last_sequence
        self.battery_mv = battery_mv
        self.last_rssi = last_rssi
        self.last_seen = last_seen
        self.out_of_order = out_of_order

        # Bi-directional Graph Pointers
        self.parent: Optional["PoleNode"] = None
        self.children: List["PoleNode"] = []

    def to_dict(self, include_children: bool = False, depth: int = 1) -> Dict[str, Any]:
        """Convert PoleNode to JSON-serializable dictionary."""
        try:
            data = {
                "id": self.id,
                "code": self.code,
                "transformer_id": self.transformer_id,
                "parent_pole_id": self.parent_pole_id,
                "seq_on_line": self.seq_on_line,
                "ward": self.ward,
                "pin_code": self.pin_code,
                "latitude": self.latitude,
                "longitude": self.longitude,
                "topology_known": self.topology_known,
                "device": {
                    "device_id": self.device_id,
                    "status": self.device_status,
                    "firmware_version": self.firmware_version,
                } if self.device_id else None,
                "telemetry": {
                    "energized": self.energized,
                    "last_event": self.last_event,
                    "last_sequence": self.last_sequence,
                    "battery_mv": self.battery_mv,
                    "last_rssi": self.last_rssi,
                    "last_seen": self.last_seen,
                    "out_of_order": self.out_of_order,
                },
                "parent_code": self.parent.code if self.parent else None,
                "children_count": len(self.children),
            }

            if include_children and depth > 0:
                data["children"] = [child.to_dict(include_children=True, depth=depth - 1) for child in self.children]
            else:
                data["children_codes"] = [child.code for child in self.children]

            return data
        except Exception as e:
            tb = traceback.format_exc()
            logger.error(f"Error serializing PoleNode {getattr(self, 'code', 'unknown')}: {e}\n{tb}")
            print(f"\n========================================\nPOLE NODE TO_DICT FAILED: {e}\n{tb}========================================\n")
            raise


class TransformerNode:
    """In-memory node representation of a distribution transformer station."""

    def __init__(
        self,
        transformer_id: str,
        transformer_code: str,
        capacity_kva: float = 100.0,
        feeder_id: Optional[str] = None,
        latitude: float = 0.0,
        longitude: float = 0.0,
    ):
        self.id = str(transformer_id)
        self.code = transformer_code
        self.capacity_kva = capacity_kva
        self.feeder_id = str(feeder_id) if feeder_id else None
        self.latitude = latitude
        self.longitude = longitude

        self.parent_feeder: Optional["FeederNode"] = None
        self.poles: List[PoleNode] = []
        self.root_poles: List[PoleNode] = []

    def to_dict(self, include_poles: bool = True) -> Dict[str, Any]:
        """Convert TransformerNode to JSON-serializable dictionary."""
        try:
            return {
                "id": self.id,
                "code": self.code,
                "capacity_kva": self.capacity_kva,
                "feeder_id": self.feeder_id,
                "feeder_code": self.parent_feeder.code if self.parent_feeder else None,
                "latitude": self.latitude,
                "longitude": self.longitude,
                "total_poles": len(self.poles),
                "root_poles_count": len(self.root_poles),
                "root_poles": [pole.to_dict(include_children=True, depth=2) for pole in self.root_poles] if include_poles else []
            }
        except Exception as e:
            tb = traceback.format_exc()
            logger.error(f"Error serializing TransformerNode {getattr(self, 'code', 'unknown')}: {e}\n{tb}")
            print(f"\n========================================\nTRANSFORMER NODE TO_DICT FAILED: {e}\n{tb}========================================\n")
            raise


class FeederNode:
    """In-memory node representation of an 11kV Feeder main trunk."""

    def __init__(
        self,
        feeder_id: str,
        feeder_code: str,
        name: str,
        status: str = "ACTIVE"
    ):
        self.id = str(feeder_id)
        self.code = feeder_code
        self.name = name
        self.status = status
        self.transformers: List[TransformerNode] = []

    def to_dict(self, include_tree: bool = True) -> Dict[str, Any]:
        """Convert FeederNode to JSON-serializable dictionary."""
        try:
            return {
                "id": self.id,
                "code": self.code,
                "name": self.name,
                "status": self.status,
                "total_transformers": len(self.transformers),
                "total_poles": sum(len(tr.poles) for tr in self.transformers),
                "transformers": [tr.to_dict(include_poles=include_tree) for tr in self.transformers] if include_tree else []
            }
        except Exception as e:
            tb = traceback.format_exc()
            logger.error(f"Error serializing FeederNode {getattr(self, 'code', 'unknown')}: {e}\n{tb}")
            print(f"\n========================================\nFEEDER NODE TO_DICT FAILED: {e}\n{tb}========================================\n")
            raise


class NetworkGraphService:
    """
    Singleton thread-safe service responsible for constructing, caching,
    and querying the in-memory electrical distribution network graph.
    """

    _instance: Optional["NetworkGraphService"] = None
    _lock = threading.Lock()

    def __init__(self):
        self._feeders: Dict[str, FeederNode] = {}
        self._transformers: Dict[str, TransformerNode] = {}
        self._poles: Dict[str, PoleNode] = {}
        self._built_at: Optional[datetime] = None

    @classmethod
    def get_instance(cls) -> "NetworkGraphService":
        """Thread-safe Singleton accessor."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def is_built(self) -> bool:
        """Check if graph is cached in memory."""
        return len(self._poles) > 0 and self._built_at is not None

    def build_graph(self, force_rebuild: bool = False) -> "NetworkGraphService":
        """
        Loads entire distribution network from PostgreSQL using bulk joins,
        instantiates node objects, and links bi-directional graph references.
        """
        with self._lock:
            if self.is_built() and not force_rebuild:
                return self

            logger.info("Building in-memory distribution network graph...")
            start_time = datetime.now(timezone.utc)

            # Expire session cache to ensure fresh DB state
            try:
                db.session.expire_all()
            except Exception:
                pass

            # Reset internal dictionaries
            self._feeders.clear()
            self._transformers.clear()
            self._poles.clear()

            try:
                # 1. Fetch Feeders
                logger.info("Graph Build Step 1: Querying Feeders")
                feeders = Feeder.query.all()
                for f in feeders:
                    f_status_val = f.status.value if hasattr(f.status, "value") else str(f.status)
                    f_node = FeederNode(
                        feeder_id=str(f.id),
                        feeder_code=f.feeder_code,
                        name=f.name,
                        status=f_status_val
                    )
                    self._feeders[f_node.id] = f_node
                    self._feeders[f_node.code] = f_node
            except Exception as e:
                tb = traceback.format_exc()
                logger.error(f"Failed querying Feeders during build_graph: {e}\n{tb}")
                print(f"\n========================================\nBUILD GRAPH (FEEDERS) FAILED: {e}\n{tb}========================================\n")
                raise

            try:
                # 2. Fetch Transformers
                logger.info("Graph Build Step 2: Querying Transformers")
                transformers = Transformer.query.all()
                for t in transformers:
                    t_node = TransformerNode(
                        transformer_id=str(t.id),
                        transformer_code=t.transformer_code,
                        capacity_kva=t.capacity_kva,
                        feeder_id=str(t.feeder_id),
                        latitude=t.latitude,
                        longitude=t.longitude
                    )
                    self._transformers[t_node.id] = t_node
                    self._transformers[t_node.code] = t_node

                    # Link to Feeder
                    f_node = self._feeders.get(t_node.feeder_id)
                    if f_node:
                        t_node.parent_feeder = f_node
                        f_node.transformers.append(t_node)
            except Exception as e:
                tb = traceback.format_exc()
                logger.error(f"Failed querying Transformers during build_graph: {e}\n{tb}")
                print(f"\n========================================\nBUILD GRAPH (TRANSFORMERS) FAILED: {e}\n{tb}========================================\n")
                raise

            try:
                # 3. Fetch Poles with linked Devices and Telemetry
                logger.info("Graph Build Step 3: Querying Poles and Devices")
                poles = Pole.query.options(joinedload(Pole.device)).all()
                for p in poles:
                    dev = p.device
                    dev_status_val = None
                    if dev:
                        dev_status_val = dev.status.value if hasattr(dev.status, "value") else str(dev.status)

                    p_node = PoleNode(
                        pole_id=str(p.id),
                        pole_code=p.pole_code,
                        transformer_id=str(p.transformer_id) if p.transformer_id else None,
                        parent_pole_id=str(p.parent_pole_id) if p.parent_pole_id else None,
                        seq_on_line=p.seq_on_line,
                        ward=getattr(p, "ward", None),
                        pin_code=getattr(p, "pincode", getattr(p, "pin_code", None)),
                        latitude=p.latitude,
                        longitude=p.longitude,
                        device_id=dev.device_id if dev else None,
                        device_status=dev_status_val,
                        firmware_version=dev.firmware_version if dev else None,
                        energized=dev.energized if dev else True,
                        last_event=dev.last_event if dev else None,
                        last_sequence=dev.last_sequence if dev else None,
                        battery_mv=dev.battery_mv if dev else None,
                        last_rssi=dev.last_rssi if dev else None,
                        last_seen=dev.last_seen.isoformat() if dev and dev.last_seen else None,
                    )

                    self._poles[p_node.id] = p_node
                    self._poles[p_node.code] = p_node

                    # Attach to Transformer
                    if p_node.transformer_id:
                        t_node = self._transformers.get(p_node.transformer_id)
                        if t_node:
                            t_node.poles.append(p_node)
            except Exception as e:
                tb = traceback.format_exc()
                logger.error(f"Failed querying Poles during build_graph: {e}\n{tb}")
                print(f"\n========================================\nBUILD GRAPH (POLES) FAILED: {e}\n{tb}========================================\n")
                raise

            try:
                # 4. Construct Parent-Child Relationships & Branching Topology
                logger.info("Graph Build Step 4: Constructing Topology References")
                for p_node in list(self._poles.values()):
                    # Avoid processing duplicates (since indexed by both id and code)
                    if len(p_node.id) > 10 and self._poles.get(p_node.id) is not p_node:
                        continue

                    if p_node.parent_pole_id:
                        parent_node = self._poles.get(p_node.parent_pole_id)
                        if parent_node:
                            p_node.parent = parent_node
                            if p_node not in parent_node.children:
                                parent_node.children.append(p_node)
                    else:
                        # Pole has no parent -> root pole under transformer
                        if p_node.transformer_id:
                            t_node = self._transformers.get(p_node.transformer_id)
                            if t_node and p_node not in t_node.root_poles:
                                t_node.root_poles.append(p_node)

                self._built_at = datetime.now(timezone.utc)
                elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
                logger.info(f"Graph construction completed in {elapsed:.3f}s. Loaded {len(self._feeders)//2} Feeders, {len(self._transformers)//2} Transformers, {len(self._poles)//2} Poles.")
                return self
            except Exception as e:
                tb = traceback.format_exc()
                logger.error(f"Failed constructing topology references in build_graph: {e}\n{tb}")
                print(f"\n========================================\nBUILD GRAPH (TOPOLOGY) FAILED: {e}\n{tb}========================================\n")
                raise

    def invalidate_cache(self) -> None:
        """Invalidates graph cache forcing rebuild on next call."""
        with self._lock:
            self._feeders.clear()
            self._transformers.clear()
            self._poles.clear()
            self._built_at = None

    def refresh_graph(self) -> "NetworkGraphService":
        """Force rebuilds the in-memory graph."""
        return self.build_graph(force_rebuild=True)

    def update_pole_telemetry(
        self,
        pole_id_or_code: str,
        energized: bool,
        last_event: Optional[str],
        last_sequence: Optional[int],
        battery_mv: Optional[int],
        last_rssi: Optional[int],
        last_seen: Optional[str],
        out_of_order: bool = False,
    ) -> bool:
        """
        Incrementally mutates in-memory PoleNode telemetry fields in O(1) time
        without rebuilding or invalidating the graph cache.
        """
        if not self.is_built():
            return False

        pole_node = self._poles.get(str(pole_id_or_code))
        if not pole_node:
            return False

        pole_node.energized = energized
        pole_node.last_event = last_event
        pole_node.last_sequence = last_sequence
        pole_node.battery_mv = battery_mv
        pole_node.last_rssi = last_rssi
        pole_node.last_seen = last_seen
        pole_node.out_of_order = out_of_order
        return True

    # -------------------------------------------------------------------
    # Query & Traversal Helper Methods
    # -------------------------------------------------------------------

    def get_feeder(self, feeder_id_or_code: str) -> Optional[FeederNode]:
        """Returns FeederNode by UUID or feeder_code in O(1) time."""
        if not self.is_built():
            self.build_graph()
        return self._feeders.get(str(feeder_id_or_code))

    def get_transformer(self, transformer_id_or_code: str) -> Optional[TransformerNode]:
        """Returns TransformerNode by UUID or transformer_code in O(1) time."""
        if not self.is_built():
            self.build_graph()
        return self._transformers.get(str(transformer_id_or_code))

    def get_pole(self, pole_id_or_code: str) -> Optional[PoleNode]:
        """Returns PoleNode by UUID or pole_code in O(1) time."""
        if not self.is_built():
            self.build_graph()
        return self._poles.get(str(pole_id_or_code))

    def get_children(self, pole: PoleNode) -> List[PoleNode]:
        """Returns direct children of a pole in O(1) time."""
        return pole.children

    def get_parent(self, pole: PoleNode) -> Optional[PoleNode]:
        """Returns parent pole of a pole in O(1) time."""
        return pole.parent

    def get_descendants(self, pole: PoleNode) -> List[PoleNode]:
        """
        Recursively retrieves all downstream descendant poles under a target pole node.
        """
        descendants: List[PoleNode] = []
        stack = list(pole.children)
        while stack:
            curr = stack.pop()
            descendants.append(curr)
            stack.extend(curr.children)
        return descendants

    def get_path_to_transformer(self, pole: PoleNode) -> List[PoleNode]:
        """
        Traces parent pointers upwards from pole node to root pole/transformer.
        Returns ordered path from root pole down to target pole.
        """
        path: List[PoleNode] = []
        curr: Optional[PoleNode] = pole
        while curr:
            path.append(curr)
            curr = curr.parent
        path.reverse()
        return path

    def get_poles_under_transformer(self, transformer_id_or_code: str) -> List[PoleNode]:
        """Returns all poles connected to a specific transformer."""
        tr = self.get_transformer(transformer_id_or_code)
        return tr.poles if tr else []

    def get_transformers_under_feeder(self, feeder_id_or_code: str) -> List[TransformerNode]:
        """Returns all transformers connected to a specific feeder."""
        f = self.get_feeder(feeder_id_or_code)
        return f.transformers if f else []

    def get_graph_statistics(self) -> Dict[str, Any]:
        """
        Computes network structural metrics, depth, branching factor, and topology coverage.
        """
        try:
            if not self.is_built():
                self.build_graph()

            unique_poles = set()
            for p in self._poles.values():
                unique_poles.add(p.id)

            unique_transformers = set()
            for t in self._transformers.values():
                unique_transformers.add(t.id)

            unique_feeders = set()
            for f in self._feeders.values():
                unique_feeders.add(f.id)

            known_topology_count = 0
            unknown_topology_count = 0
            devices_count = 0
            branching_factors: List[int] = []
            max_depth = 0

            for p_id in unique_poles:
                p = self._poles[p_id]
                if p.topology_known:
                    known_topology_count += 1
                else:
                    unknown_topology_count += 1

                if p.device_id:
                    devices_count += 1

                if p.children:
                    branching_factors.append(len(p.children))

                # Depth calculation
                path = self.get_path_to_transformer(p)
                if len(path) > max_depth:
                    max_depth = len(path)

            avg_branch_factor = (
                sum(branching_factors) / len(branching_factors) if branching_factors else 0.0
            )

            return {
                "total_feeders": len(unique_feeders),
                "total_transformers": len(unique_transformers),
                "total_poles": len(unique_poles),
                "total_devices": devices_count,
                "known_topology_count": known_topology_count,
                "unknown_topology_count": unknown_topology_count,
                "known_topology_percent": round((known_topology_count / len(unique_poles) * 100), 1) if unique_poles else 0.0,
                "max_tree_depth": max_depth,
                "avg_branching_factor": round(avg_branch_factor, 2),
                "built_at": self._built_at.isoformat() if self._built_at else None,
            }
        except Exception as e:
            tb = traceback.format_exc()
            logger.error(f"Error computing get_graph_statistics: {e}\n{tb}")
            print(f"\n========================================\nGET GRAPH STATISTICS FAILED: {e}\n{tb}========================================\n")
            raise
