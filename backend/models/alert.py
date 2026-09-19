"""ClearWay AI — Alert models"""
from datetime import datetime
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field
import uuid


class AlertType(str, Enum):
    SEVERE_CONGESTION = "severe_congestion"
    QUEUE_GROWTH = "queue_growth"
    PREDICTED_CONGESTION = "predicted_congestion"
    EMERGENCY_VEHICLE = "emergency_vehicle"
    SIREN_DETECTED = "siren_detected"
    ACCIDENT = "accident"
    CAMERA_OFFLINE = "camera_offline"
    MICROPHONE_OFFLINE = "microphone_offline"
    GREEN_CORRIDOR_COMPLETE = "green_corridor_complete"
    HIGH_EMISSION = "high_emission"
    OPTIMIZATION_COMPLETE = "optimization_complete"
    ROAD_CLOSURE = "road_closure"


class AlertSeverity(str, Enum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


ALERT_SEVERITY_MAP = {
    AlertType.SEVERE_CONGESTION: AlertSeverity.CRITICAL,
    AlertType.QUEUE_GROWTH: AlertSeverity.MEDIUM,
    AlertType.PREDICTED_CONGESTION: AlertSeverity.LOW,
    AlertType.EMERGENCY_VEHICLE: AlertSeverity.CRITICAL,
    AlertType.SIREN_DETECTED: AlertSeverity.CRITICAL,
    AlertType.ACCIDENT: AlertSeverity.HIGH,
    AlertType.CAMERA_OFFLINE: AlertSeverity.MEDIUM,
    AlertType.MICROPHONE_OFFLINE: AlertSeverity.MEDIUM,
    AlertType.GREEN_CORRIDOR_COMPLETE: AlertSeverity.INFO,
    AlertType.HIGH_EMISSION: AlertSeverity.MEDIUM,
    AlertType.OPTIMIZATION_COMPLETE: AlertSeverity.INFO,
    AlertType.ROAD_CLOSURE: AlertSeverity.HIGH,
}


class Alert(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: AlertType
    severity: AlertSeverity
    title: str
    message: str
    intersection_id: Optional[str] = None
    junction_label: Optional[str] = None
    related_event_id: Optional[str] = None
    ai_explanation: Optional[str] = None
    recommended_action: Optional[str] = None
    is_active: bool = True
    acknowledged: bool = False
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    auto_resolve_at: Optional[datetime] = None
    data_source: str = "DEMO"

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}
