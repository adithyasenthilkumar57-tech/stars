"""
ClearWay AI — Application Configuration
Reads from .env file via pydantic-settings.
All secrets stay server-side — never exposed to frontend.
"""

import json
import os
from enum import Enum
from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class DataMode(str, Enum):
    DEMO = "DEMO"
    SIMULATION = "SIMULATION"
    LIVE = "LIVE"


class Environment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── External API Keys ──────────────────────────────────────────────────
    GEMINI_API_KEY: str = ""
    FEATHERLESS_API_KEY: str = ""     # Featherless AI (OpenAI-compatible)
    FEATHERLESS_MODEL: str = "Qwen/Qwen2.5-7B-Instruct"
    FIREBASE_SERVICE_ACCOUNT_JSON: str = "{}"

    # Firebase web config (returned to frontend for Auth SDK only)
    FIREBASE_WEB_API_KEY: str = ""
    FIREBASE_AUTH_DOMAIN: str = ""
    FIREBASE_PROJECT_ID: str = ""
    FIREBASE_STORAGE_BUCKET: str = ""
    FIREBASE_MESSAGING_SENDER_ID: str = ""
    FIREBASE_APP_ID: str = ""

    # ── Application ────────────────────────────────────────────────────────
    DATA_MODE: DataMode = DataMode.DEMO
    ENVIRONMENT: Environment = Environment.DEVELOPMENT
    BACKEND_URL: str = "http://localhost:8000"
    FRONTEND_URL: str = "http://localhost:3000"
    SECRET_KEY: str = "clearway-dev-secret-change-in-production"

    # ── Infrastructure ─────────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── Feature Flags ──────────────────────────────────────────────────────
    ENABLE_QUANTUM: bool = True
    ENABLE_AUDIO_DETECTION: bool = True
    ENABLE_VISION: bool = True
    ENABLE_GEMINI: bool = True

    # ── Quantum ────────────────────────────────────────────────────────────
    QAOA_LAYERS: int = 2

    # ── Audio / Siren ──────────────────────────────────────────────────────
    SIREN_CONFIDENCE_THRESHOLD: float = 0.75

    # ── Simulation ─────────────────────────────────────────────────────────
    SIM_TICK_INTERVAL: float = 1.0
    DEMO_INTERSECTION_COUNT: int = 6

    # ── Derived properties ─────────────────────────────────────────────────
    @property
    def featherless_available(self) -> bool:
        return bool(self.FEATHERLESS_API_KEY and self.FEATHERLESS_API_KEY.startswith("rc_"))

    @property
    def gemini_available(self) -> bool:
        return bool(self.GEMINI_API_KEY and self.GEMINI_API_KEY != "YOUR_GEMINI_API_KEY_HERE")

    @property
    def ai_available(self) -> bool:
        return self.featherless_available or self.gemini_available

    @property
    def firebase_available(self) -> bool:
        try:
            sa = json.loads(self.FIREBASE_SERVICE_ACCOUNT_JSON)
            return bool(sa.get("project_id"))
        except Exception:
            return False

    @property
    def firebase_service_account(self) -> dict:
        try:
            return json.loads(self.FIREBASE_SERVICE_ACCOUNT_JSON)
        except Exception:
            return {}

    @property
    def firebase_web_config(self) -> dict:
        return {
            "apiKey": self.FIREBASE_WEB_API_KEY,
            "authDomain": self.FIREBASE_AUTH_DOMAIN,
            "projectId": self.FIREBASE_PROJECT_ID,
            "storageBucket": self.FIREBASE_STORAGE_BUCKET,
            "messagingSenderId": self.FIREBASE_MESSAGING_SENDER_ID,
            "appId": self.FIREBASE_APP_ID,
        }

    @property
    def system_status(self) -> dict:
        return {
            "featherless_available": self.featherless_available,
            "gemini_available": self.gemini_available,
            "ai_available": self.ai_available,
            "firebase": "available" if self.firebase_available else "not_configured",
            "data_mode": self.DATA_MODE.value,
            "environment": self.ENVIRONMENT.value,
            "quantum": "enabled" if self.ENABLE_QUANTUM else "disabled",
            "audio_detection": "enabled" if self.ENABLE_AUDIO_DETECTION else "disabled",
            "vision": "enabled" if self.ENABLE_VISION else "disabled",
        }


@lru_cache
def get_settings() -> Settings:
    return Settings()
