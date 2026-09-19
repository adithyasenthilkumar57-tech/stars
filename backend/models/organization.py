"""ClearWay AI — Organization, City, TrafficZone models"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
import uuid


class Organization(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    country: str
    state: str
    contact_email: str
    emblem_url: Optional[str] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Tamil Nadu Traffic Authority",
                "country": "India",
                "state": "Tamil Nadu",
                "contact_email": "traffic@tnta.gov.in",
            }
        }


class City(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: str
    name: str
    state: str
    country: str
    latitude: float
    longitude: float
    timezone: str = "Asia/Kolkata"
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)


class TrafficZone(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    city_id: str
    organization_id: str
    name: str
    description: Optional[str] = None
    boundary_geojson: Optional[dict] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
