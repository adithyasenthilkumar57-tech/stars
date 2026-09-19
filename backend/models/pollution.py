"""ClearWay AI — Pollution models"""
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict
from pydantic import BaseModel, Field
import uuid


class PollutantType(str, Enum):
    CO2 = "co2"
    CO = "co"
    NOX = "nox"
    PM25 = "pm25"
    PM10 = "pm10"
    FUEL = "fuel_liters"


EMISSION_FACTORS = {
    "car":       {"co2": 120.0, "co": 1.2, "nox": 0.06, "pm25": 0.002, "pm10": 0.004, "fuel_liters": 0.05},
    "motorcycle":{"co2": 70.0,  "co": 1.8, "nox": 0.04, "pm25": 0.001, "pm10": 0.002, "fuel_liters": 0.03},
    "bus":       {"co2": 550.0, "co": 3.5, "nox": 0.50, "pm25": 0.020, "pm10": 0.040, "fuel_liters": 0.25},
    "truck":     {"co2": 750.0, "co": 4.0, "nox": 0.80, "pm25": 0.030, "pm10": 0.060, "fuel_liters": 0.35},
    "auto_rickshaw": {"co2": 90.0, "co": 2.0, "nox": 0.10, "pm25": 0.005, "pm10": 0.010, "fuel_liters": 0.04},
    "cars":      {"co2": 120.0, "co": 1.2, "nox": 0.06, "pm25": 0.002, "pm10": 0.004, "fuel_liters": 0.05},
    "motorcycles":{"co2": 70.0,  "co": 1.8, "nox": 0.04, "pm25": 0.001, "pm10": 0.002, "fuel_liters": 0.03},
    "buses":     {"co2": 550.0, "co": 3.5, "nox": 0.50, "pm25": 0.020, "pm10": 0.040, "fuel_liters": 0.25},
    "trucks":    {"co2": 750.0, "co": 4.0, "nox": 0.80, "pm25": 0.030, "pm10": 0.060, "fuel_liters": 0.35},
    "auto_rickshaws": {"co2": 90.0, "co": 2.0, "nox": 0.10, "pm25": 0.005, "pm10": 0.010, "fuel_liters": 0.04},
}

IDLE_FACTOR = 1.8


class PollutionEstimate(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    intersection_id: str
    junction_label: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    co2_kg_per_hour: float
    co_g_per_hour: float
    nox_g_per_hour: float
    pm25_g_per_hour: float
    pm10_g_per_hour: float
    fuel_liters_per_hour: float
    vehicle_count: int
    queue_length: int
    idle_fraction: float
    dominant_vehicle_type: str
    aqi_estimate: int
    aqi_category: str
    ai_insight: Optional[str] = None
    data_source: str = "ESTIMATED"

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class PollutionTrend(BaseModel):
    intersection_id: str
    junction_label: str
    history: List[Dict] = Field(default_factory=list)
    trend_direction: str = "stable"
    peak_hour: Optional[int] = None
    data_source: str = "ESTIMATED"
