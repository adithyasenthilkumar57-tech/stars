"""ClearWay AI — Report models"""
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
import uuid


class ReportType(str, Enum):
    DAILY_TRAFFIC = "daily_traffic"
    EMERGENCY = "emergency"
    OPTIMIZATION = "optimization"
    POLLUTION = "pollution"


class Report(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: ReportType
    title: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    generated_by: str = "system"
    date_range_start: datetime
    date_range_end: datetime
    intersection_ids: Optional[List[str]] = None
    summary: Dict[str, Any] = Field(default_factory=dict)
    sections: List[Dict[str, Any]] = Field(default_factory=list)
    pdf_url: Optional[str] = None
    csv_url: Optional[str] = None
    data_source: str = "DEMO"

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class ReportGenerateRequest(BaseModel):
    type: ReportType
    date_range_start: Optional[datetime] = None
    date_range_end: Optional[datetime] = None
    intersection_ids: Optional[List[str]] = None
    include_ai_summary: bool = True
    format: str = "pdf"
