"""ClearWay AI — Siren Detection and Police Alert models"""
from datetime import datetime
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field
import uuid


class SirenStatus(str, Enum):
    MONITORING = "monitoring"
    DETECTED = "detected"
    ALERT_DISPATCHED = "alert_dispatched"
    OFFICER_ACKNOWLEDGED = "officer_acknowledged"
    CLEARANCE_IN_PROGRESS = "clearance_in_progress"
    PATH_CLEAR = "path_clear"
    COMPLETE = "complete"
    FALSE_POSITIVE = "false_positive"


class ApproachDirection(str, Enum):
    NORTH = "north"
    SOUTH = "south"
    EAST = "east"
    WEST = "west"
    UNKNOWN = "unknown"


class SirenDetectionEvent(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    junction_id: str
    junction_label: str
    detected_at: datetime = Field(default_factory=datetime.utcnow)
    confidence: float  # 0.0–1.0
    mfcc_features: Optional[List[float]] = None  # 40 MFCC coefficients
    approach_direction: ApproachDirection = ApproachDirection.UNKNOWN
    direction_estimate_method: str = "SIMULATED_TRIANGULATION"
    direction_confidence: float = 0.0
    status: SirenStatus = SirenStatus.DETECTED
    is_active: bool = True

    # Labeled as: SIMULATED | REAL_MICROPHONE
    data_source: str = "SIMULATED"

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class PoliceAlertDispatch(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    siren_event_id: str
    junction_id: str
    junction_label: str
    officer_id: Optional[str] = None
    voice_message_text: str
    voice_audio_url: Optional[str] = None  # Firebase Storage URL of TTS audio
    repeat_count: int = 5
    dispatched_at: datetime = Field(default_factory=datetime.utcnow)
    acknowledged_at: Optional[datetime] = None
    clearance_started_at: Optional[datetime] = None
    path_cleared_at: Optional[datetime] = None
    officer_status: SirenStatus = SirenStatus.ALERT_DISPATCHED
    approach_direction: ApproachDirection = ApproachDirection.UNKNOWN
    # Clearly labeled as prototype
    dispatch_method: str = "SIMULATED_RADIO_DISPATCH"

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class SirenAcknowledgeRequest(BaseModel):
    siren_event_id: str
    officer_status: SirenStatus
    officer_id: Optional[str] = None
    note: Optional[str] = None


class SirenEventRequest(BaseModel):
    junction_id: str
    junction_label: str
    confidence: float
    approach_direction: ApproachDirection = ApproachDirection.UNKNOWN
    data_source: str = "SIMULATED"


class JunctionMicrophoneStatus(BaseModel):
    junction_id: str
    junction_label: str
    microphone_online: bool
    monitoring_active: bool
    last_detection_at: Optional[datetime] = None
    current_confidence: float = 0.0
    active_event: Optional[SirenDetectionEvent] = None
    active_dispatch: Optional[PoliceAlertDispatch] = None
    status: SirenStatus = SirenStatus.MONITORING
    data_source: str = "SIMULATED"
