"""ClearWay AI — Simulation scenario and event models"""
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
import uuid


class EventType(str, Enum):
    HEAVY_TRAFFIC = "heavy_traffic"
    ACCIDENT = "accident"
    ROAD_CLOSURE = "road_closure"
    EMERGENCY_VEHICLE = "emergency_vehicle"
    SUDDEN_CONGESTION = "sudden_congestion"
    PEDESTRIAN_SURGE = "pedestrian_surge"
    SIREN_DETECTION = "siren_detection"


class TrafficVolume(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    PEAK = "peak"


class TrafficEvent(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: EventType
    intersection_id: Optional[str] = None
    road_id: Optional[str] = None
    description: str = ""
    severity: float = 0.5  # 0.0–1.0
    duration_minutes: int = 15
    triggered_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True
    ai_response: Optional[str] = None


class SimulationScenario(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    num_intersections: int = 6
    traffic_volume: TrafficVolume = TrafficVolume.MEDIUM
    emergency_vehicle: bool = False
    siren_detection: bool = False
    accident: bool = False
    road_closure: bool = False
    pedestrian_surge: bool = False
    vehicle_composition: Dict[str, float] = Field(
        default_factory=lambda: {
            "cars": 0.60, "motorcycles": 0.20, "buses": 0.08,
            "trucks": 0.07, "auto_rickshaws": 0.05
        }
    )
    optimization_method: str = "hybrid_quantum"
    pollution_estimation: bool = True
    duration_minutes: int = 30
    created_at: datetime = Field(default_factory=datetime.utcnow)


class IntersectionSimState(BaseModel):
    intersection_id: str
    label: str
    vehicle_count: int
    queue_length: int
    waiting_time: float
    congestion_score: float
    throughput_vph: float
    current_phase: str
    phase_remaining: int
    ns_green: int
    ew_green: int


class SimulationResult(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    scenario_id: str
    scenario_name: str
    duration_simulated_minutes: int
    tick_count: int

    # Aggregate metrics
    total_vehicles_processed: int
    avg_waiting_time_seconds: float
    avg_queue_length: float
    peak_congestion_junction: str
    total_throughput_vehicles: int
    optimization_cost_classical: float
    optimization_cost_quantum: float
    improvement_pct: float

    # Emergency metrics (if applicable)
    emergency_travel_time_classical: Optional[float] = None
    emergency_travel_time_optimized: Optional[float] = None
    emergency_improvement_pct: Optional[float] = None

    # Siren timeline (if applicable)
    siren_timeline: Optional[List[Dict[str, Any]]] = None

    # Per-junction final states
    intersection_states: List[IntersectionSimState] = Field(default_factory=list)

    # Pollution estimates
    total_co2_kg: float = 0.0
    total_nox_g: float = 0.0
    total_pm25_g: float = 0.0

    # Charts data (time-series)
    timeline: List[Dict[str, Any]] = Field(default_factory=list)

    completed_at: datetime = Field(default_factory=datetime.utcnow)
    data_source: str = "SIMULATION"

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class SimulationRunRequest(BaseModel):
    scenario: SimulationScenario
