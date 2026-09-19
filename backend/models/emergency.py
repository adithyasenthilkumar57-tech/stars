"""ClearWay AI — Emergency Vehicle, Route, Corridor models"""
from datetime import datetime
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field
import uuid


class CorridorStatus(str, Enum):
    INACTIVE = "inactive"
    DETECTED = "detected"
    CORRIDOR_ACTIVE = "corridor_active"
    PASSING = "passing"
    COMPLETE = "complete"
    REOPTIMIZING = "reoptimizing"


class EmergencyVehicle(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    vehicle_id: str = "AMB-001"
    type: str = "ambulance"
    origin_intersection_id: str
    destination_name: str = "City Hospital"
    destination_lat: float = 0.0
    destination_lon: float = 0.0
    detected_via: str = "CAMERA"  # CAMERA | SIREN | MANUAL
    detected_at: datetime = Field(default_factory=datetime.utcnow)
    current_intersection_id: Optional[str] = None
    status: CorridorStatus = CorridorStatus.DETECTED


class EmergencyRoute(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    emergency_vehicle_id: str
    route_intersection_ids: List[str]  # ordered list of junction IDs
    total_distance_meters: float
    estimated_travel_time_classical: float  # seconds (classical signal plan)
    estimated_travel_time_optimized: float  # seconds (optimized corridor)
    improvement_pct: float
    current_junction_index: int = 0
    eta_seconds: float = 0.0
    corridor_status: CorridorStatus = CorridorStatus.DETECTED
    activated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    junctions_cleared: List[str] = Field(default_factory=list)
    signal_overrides: dict = Field(default_factory=dict)  # junction_id -> override_plan
    data_source: str = "SIMULATED"

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class EmergencyActivateRequest(BaseModel):
    origin_intersection_id: str
    destination_name: str = "City Hospital"
    vehicle_type: str = "ambulance"
    detected_via: str = "MANUAL"


class EmergencyStatusResponse(BaseModel):
    active: bool
    corridor_status: CorridorStatus
    emergency_vehicle: Optional[EmergencyVehicle] = None
    route: Optional[EmergencyRoute] = None
    progress_pct: float = 0.0
    ai_insight: Optional[str] = None
