"""
ClearWay AI — Emergency Service
NetworkX routing + Green Corridor state machine.
Lifecycle: INACTIVE → DETECTED → CORRIDOR_ACTIVE → PASSING → COMPLETE → REOPTIMIZING
"""
import logging
import random
from datetime import datetime
from typing import Optional, List, Dict, Any

import networkx as nx

from models.emergency import (
    EmergencyVehicle, EmergencyRoute, CorridorStatus,
    EmergencyActivateRequest, EmergencyStatusResponse
)
from models.intersection import SignalPhase

logger = logging.getLogger(__name__)


class EmergencyService:
    """
    Manages emergency green corridor lifecycle.
    Uses NetworkX for shortest-path calculation.
    All data labeled SIMULATED.
    """

    def __init__(self):
        self.graph = nx.DiGraph()
        self._active_vehicle: Optional[EmergencyVehicle] = None
        self._active_route: Optional[EmergencyRoute] = None
        self._corridor_status: CorridorStatus = CorridorStatus.INACTIVE
        self._signal_overrides: Dict[str, dict] = {}

    def build_graph(self, intersections: list, roads: list):
        """Build NetworkX graph from intersection and road data."""
        self.graph.clear()
        for inter in intersections:
            self.graph.add_node(inter.id, label=inter.label,
                                lat=inter.latitude, lon=inter.longitude)
        for road in roads:
            weight = road.distance_meters / max(road.speed_limit_kmh / 3.6, 1)
            if road.is_blocked:
                weight *= 100  # Heavily penalize blocked roads
            self.graph.add_edge(road.from_intersection_id, road.to_intersection_id, weight=weight)
            if road.is_bidirectional:
                self.graph.add_edge(road.to_intersection_id, road.from_intersection_id, weight=weight)

    def activate_corridor(
        self,
        request: EmergencyActivateRequest,
        intersections: list,
        roads: list,
    ) -> EmergencyStatusResponse:
        """
        Activate emergency green corridor.
        Calculates optimal route and returns corridor status.
        """
        self.build_graph(intersections, roads)

        # Find origin intersection
        origin = next((i for i in intersections if i.id == request.origin_intersection_id), None)
        if origin is None:
            origin = intersections[0]

        # Destination: use last intersection as "hospital" proxy
        dest = intersections[-1]

        # Calculate shortest path
        try:
            path_ids = nx.shortest_path(
                self.graph, source=origin.id, target=dest.id, weight='weight'
            )
        except nx.NetworkXNoPath:
            path_ids = [i.id for i in intersections]

        # Calculate distances and times
        total_dist = sum(
            self.graph[path_ids[i]][path_ids[i + 1]].get('weight', 100) * 50
            for i in range(len(path_ids) - 1)
        )
        # Classical: based on normal traffic conditions
        classical_time = total_dist / (20 / 3.6)  # 20 km/h with red lights
        # Optimized: green corridor removes stops
        optimized_time = total_dist / (50 / 3.6)  # 50 km/h unimpeded
        improvement_pct = (classical_time - optimized_time) / classical_time * 100

        # Signal overrides for corridor junctions
        overrides = {}
        for jid in path_ids:
            overrides[jid] = {
                "phase": SignalPhase.EMERGENCY_OVERRIDE.value,
                "ns_green_seconds": 999,  # Hold green
                "reason": "Emergency green corridor active",
            }

        # Create emergency vehicle
        self._active_vehicle = EmergencyVehicle(
            origin_intersection_id=origin.id,
            destination_name=request.destination_name,
            detected_via=request.detected_via,
            current_intersection_id=path_ids[0] if path_ids else origin.id,
            status=CorridorStatus.CORRIDOR_ACTIVE,
        )

        # Create route
        self._active_route = EmergencyRoute(
            emergency_vehicle_id=self._active_vehicle.id,
            route_intersection_ids=path_ids,
            total_distance_meters=total_dist,
            estimated_travel_time_classical=round(classical_time, 1),
            estimated_travel_time_optimized=round(optimized_time, 1),
            improvement_pct=round(improvement_pct, 1),
            current_junction_index=0,
            eta_seconds=round(optimized_time, 1),
            corridor_status=CorridorStatus.CORRIDOR_ACTIVE,
            activated_at=datetime.utcnow(),
            signal_overrides=overrides,
            data_source="SIMULATED",
        )

        self._corridor_status = CorridorStatus.CORRIDOR_ACTIVE
        self._signal_overrides = overrides

        return self._build_status_response()

    def advance_corridor(self) -> EmergencyStatusResponse:
        """Advance ambulance one junction along the corridor."""
        if self._active_route is None or self._corridor_status != CorridorStatus.CORRIDOR_ACTIVE:
            return self._build_status_response()

        route = self._active_route
        route.current_junction_index = min(
            route.current_junction_index + 1,
            len(route.route_intersection_ids) - 1,
        )
        route.junctions_cleared.append(
            route.route_intersection_ids[route.current_junction_index - 1]
        )

        # Update ETA
        remaining_junctions = len(route.route_intersection_ids) - route.current_junction_index
        route.eta_seconds = route.estimated_travel_time_optimized * (
            remaining_junctions / max(len(route.route_intersection_ids), 1)
        )

        # Update ambulance location
        if self._active_vehicle:
            cur_idx = route.current_junction_index
            if cur_idx < len(route.route_intersection_ids):
                self._active_vehicle.current_intersection_id = route.route_intersection_ids[cur_idx]

        # Check if reached destination
        if route.current_junction_index >= len(route.route_intersection_ids) - 1:
            self._corridor_status = CorridorStatus.COMPLETE
            route.corridor_status = CorridorStatus.COMPLETE
            route.completed_at = datetime.utcnow()
            self._signal_overrides = {}

        return self._build_status_response()

    def complete_corridor(self) -> EmergencyStatusResponse:
        """Mark corridor complete and begin re-optimization."""
        if self._active_route:
            self._active_route.corridor_status = CorridorStatus.COMPLETE
            self._active_route.completed_at = datetime.utcnow()
        self._corridor_status = CorridorStatus.REOPTIMIZING
        self._signal_overrides = {}
        return self._build_status_response()

    def reset(self):
        """Reset corridor to inactive state."""
        self._active_vehicle = None
        self._active_route = None
        self._corridor_status = CorridorStatus.INACTIVE
        self._signal_overrides = {}

    def get_status(self) -> EmergencyStatusResponse:
        return self._build_status_response()

    def get_signal_overrides(self) -> Dict[str, dict]:
        return self._signal_overrides.copy()

    def _build_status_response(self) -> EmergencyStatusResponse:
        progress = 0.0
        if self._active_route and len(self._active_route.route_intersection_ids) > 1:
            progress = (
                self._active_route.current_junction_index
                / (len(self._active_route.route_intersection_ids) - 1)
                * 100
            )
        return EmergencyStatusResponse(
            active=self._corridor_status not in [CorridorStatus.INACTIVE, CorridorStatus.REOPTIMIZING],
            corridor_status=self._corridor_status,
            emergency_vehicle=self._active_vehicle,
            route=self._active_route,
            progress_pct=round(progress, 1),
        )

    @property
    def is_active(self) -> bool:
        return self._corridor_status == CorridorStatus.CORRIDOR_ACTIVE


# Singleton
emergency_service = EmergencyService()
