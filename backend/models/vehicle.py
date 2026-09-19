"""ClearWay AI — Vehicle and TrafficSnapshot models"""
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict
from pydantic import BaseModel, Field
import uuid


class VehicleType(str, Enum):
    CAR = "car"
    MOTORCYCLE = "motorcycle"
    BUS = "bus"
    TRUCK = "truck"
    EMERGENCY = "emergency"
    PEDESTRIAN = "pedestrian"
    AUTO_RICKSHAW = "auto_rickshaw"


class Vehicle(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: VehicleType = VehicleType.CAR
    intersection_id: str
    lane: str  # "north", "south", "east", "west"
    speed_kmh: float = 0.0
    is_queued: bool = False
    detected_at: datetime = Field(default_factory=datetime.utcnow)
    bounding_box: Optional[Dict[str, float]] = None  # {x, y, w, h}
    confidence: float = 1.0
    data_source: str = "SIMULATED"


class VehicleComposition(BaseModel):
    cars: int = 0
    motorcycles: int = 0
    buses: int = 0
    trucks: int = 0
    emergency: int = 0
    auto_rickshaws: int = 0
    pedestrians: int = 0

    @property
    def total(self) -> int:
        return self.cars + self.motorcycles + self.buses + self.trucks + self.emergency + self.auto_rickshaws

    @property
    def heavy_vehicle_ratio(self) -> float:
        t = self.total
        return (self.buses + self.trucks) / t if t > 0 else 0.0


class TrafficSnapshot(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    intersection_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    vehicle_count: int
    queue_length: int
    average_speed_kmh: float
    congestion_score: float  # 0.0–1.0
    waiting_time_seconds: float
    throughput_vph: float
    lane_occupancy: Dict[str, float] = Field(default_factory=dict)  # lane -> occupancy %
    vehicle_composition: VehicleComposition = Field(default_factory=VehicleComposition)
    data_source: str = "DEMO"

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}
