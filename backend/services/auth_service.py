"""
ClearWay AI — Auth Service
JWT-based auth with demo user support when Firebase not configured.
"""
import logging
from datetime import datetime, timedelta
from typing import Optional
from jose import jwt, JWTError
from models.user import User, UserRole, LoginRequest, LoginResponse, TokenData
from data.demo_seed import DEMO_USERS

logger = logging.getLogger(__name__)

SECRET_KEY = "clearway-dev-secret-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24


class AuthService:
    def __init__(self, secret_key: str = SECRET_KEY):
        self.secret_key = secret_key
        self._demo_users = {u["email"]: u for u in DEMO_USERS}

    def create_access_token(self, user: User) -> str:
        expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
        payload = {
            "sub": user.id,
            "email": user.email,
            "role": user.role.value,
            "org": user.organization_id,
            "exp": expire,
        }
        return jwt.encode(payload, self.secret_key, algorithm=ALGORITHM)

    def decode_token(self, token: str) -> Optional[TokenData]:
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[ALGORITHM])
            return TokenData(
                user_id=payload["sub"],
                email=payload["email"],
                role=UserRole(payload["role"]),
                organization_id=payload.get("org", "org-tnta-001"),
            )
        except JWTError as e:
            logger.warning(f"Token decode failed: {e}")
            return None

    def login_demo(self, request: LoginRequest) -> Optional[LoginResponse]:
        """Authenticate against demo users (when Firebase not configured)."""
        demo = self._demo_users.get(request.email)
        if not demo:
            return None
        if demo.get("password") != request.password:
            return None

        user = User(
            id=demo["id"],
            email=demo["email"],
            display_name=demo["display_name"],
            role=UserRole(demo["role"]),
            organization_id="org-tnta-001",
            assigned_junction_id=demo.get("assigned_junction_id"),
        )
        token = self.create_access_token(user)
        return LoginResponse(
            access_token=token,
            user=user,
            system_status={"mode": "DEMO", "firebase": "not_configured"},
        )

    def get_demo_users_info(self) -> list:
        return [
            {"email": u["email"], "role": u["role"], "password": u["password"]}
            for u in DEMO_USERS
        ]


auth_service = AuthService()
