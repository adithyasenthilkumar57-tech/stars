"""ClearWay AI — User and Role models"""
from datetime import datetime
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr
import uuid


class UserRole(str, Enum):
    SUPER_ADMIN = "super_admin"
    TRAFFIC_AUTHORITY = "traffic_authority"
    OPERATOR = "operator"
    TRAFFIC_POLICE = "traffic_police"
    EMERGENCY_COORDINATOR = "emergency_coordinator"
    ANALYST = "analyst"
    VIEWER = "viewer"


class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    display_name: str
    role: UserRole = UserRole.VIEWER
    organization_id: str
    city_ids: List[str] = Field(default_factory=list)
    zone_ids: List[str] = Field(default_factory=list)
    assigned_junction_id: Optional[str] = None  # For traffic police field units
    is_active: bool = True
    last_login: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    @property
    def can_view_alerts(self) -> bool:
        return self.role in [
            UserRole.SUPER_ADMIN, UserRole.TRAFFIC_AUTHORITY,
            UserRole.OPERATOR, UserRole.TRAFFIC_POLICE,
            UserRole.EMERGENCY_COORDINATOR, UserRole.ANALYST,
        ]

    @property
    def can_control_signals(self) -> bool:
        return self.role in [
            UserRole.SUPER_ADMIN, UserRole.TRAFFIC_AUTHORITY, UserRole.OPERATOR,
        ]

    @property
    def can_activate_emergency(self) -> bool:
        return self.role in [
            UserRole.SUPER_ADMIN, UserRole.TRAFFIC_AUTHORITY,
            UserRole.EMERGENCY_COORDINATOR,
        ]

    @property
    def can_acknowledge_siren(self) -> bool:
        return self.role in [
            UserRole.SUPER_ADMIN, UserRole.TRAFFIC_AUTHORITY,
            UserRole.OPERATOR, UserRole.TRAFFIC_POLICE,
        ]


class TokenData(BaseModel):
    user_id: str
    email: str
    role: UserRole
    organization_id: str


class LoginRequest(BaseModel):
    email: str
    password: str
    organization_id: Optional[str] = None


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: User
    system_status: dict
