"""ClearWay AI — Intersection, Road, Signal models"""
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict
from pydantic import BaseModel, Field
import uuid


class CongestionLevel(str, Enum):
    LOW = "low"
    MODERATE = "moderate"
    HEAVY = "heavy"
    SEVERE = "severe"


class SignalPhase(str, Enum):
    NORTH_SOUTH_GREEN = "ns_green"
    EAST_WEST_GREEN = "ew_green"
    ALL_RED = "all_red"
    PEDESTRIAN = "pedestrian"
    EMERGENCY_OVERRIDE = "emergency_override"


class Signal(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    intersection_id: str
    current_phase: SignalPhase = SignalPhase.NORTH_SOUTH_GREEN
    phase_remaining_seconds: int = 30
    ns_green_duration: int = 45   # seconds
    ew_green_duration: int = 35
    all_red_duration: int = 5
    pedestrian_duration: int = 20
    is_emergency_override: bool = False
    ai_recommended_ns: Optional[int] = None
    ai_recommended_ew: Optional[int] = None
    last_updated: datetime = Field(default_factory=datetime.utcnow)


class Camera(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    intersection_id: str
    label: str
    direction: str  # "north", "south", "east", "west"
    is_online: bool = True
    last_frame_at: Optional[datetime] = None
    stream_url: Optional[str] = None
    detection_active: bool = True


class Microphone(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    intersection_id: str
    label: str
    direction: str
    is_online: bool = True
    detection_active: bool = True
    last_detection_at: Optional[datetime] = None
    ambient_db: float = 65.0  # estimated ambient dB level


class Intersection(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    zone_id: str
    city_id: str
    organization_id: str
    name: str
    label: str  # e.g., "J1", "J4"
    latitude: float
    longitude: float
    road_capacity: int = 800  # vehicles/hour
    lane_count: int = 4
    has_pedestrian_crossing: bool = True

    # Live state (updated by simulation/vision)
    vehicle_count: int = 0
    queue_length: int = 0
    average_speed_kmh: float = 40.0
    congestion_level: CongestionLevel = CongestionLevel.LOW
    congestion_score: float = 0.0  # 0.0 – 1.0
    density: float = 0.0  # vehicles/km²
    waiting_time_seconds: float = 0.0
    throughput_vph: float = 0.0  # vehicles per hour

    # Devices
    signal: Optional[Signal] = None
    cameras: List[Camera] = Field(default_factory=list)
    microphones: List[Microphone] = Field(default_factory=list)

    # Connections
    connected_intersection_ids: List[str] = Field(default_factory=list)

    # AI insight
    ai_insight: Optional[str] = None
    recommendation_strength: Optional[str] = None  # High/Medium/Low

    # Metadata
    is_active: bool = True
    data_source: str = "DEMO"
    last_updated: datetime = Field(default_factory=datetime.utcnow)


class Road(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    from_intersection_id: str
    to_intersection_id: str
    name: str
    distance_meters: float
    speed_limit_kmh: int = 60
    lane_count: int = 2
    is_bidirectional: bool = True
    current_congestion: CongestionLevel = CongestionLevel.LOW
    is_blocked: bool = False
    block_reason: Optional[str] = None
