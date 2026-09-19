"""
ClearWay AI — Firebase Admin SDK Initialization
Singleton pattern — initialized once at startup.
Falls back gracefully if credentials are not configured.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

_firebase_app = None
_firestore_client = None
_storage_bucket = None
_firebase_initialized = False


def init_firebase(settings) -> bool:
    """
    Initialize Firebase Admin SDK.
    Returns True if successful, False if credentials not configured.
    """
    global _firebase_app, _firestore_client, _storage_bucket, _firebase_initialized

    if _firebase_initialized:
        return _firebase_app is not None

    if not settings.firebase_available:
        logger.warning(
            "Firebase credentials not configured. "
            "Running in DEMO mode without Firebase persistence. "
            "Set FIREBASE_SERVICE_ACCOUNT_JSON in .env to enable Firebase."
        )
        _firebase_initialized = True
        return False

    try:
        import firebase_admin
        from firebase_admin import credentials, firestore, storage

        sa = settings.firebase_service_account
        cred = credentials.Certificate(sa)
        _firebase_app = firebase_admin.initialize_app(
            cred,
            {"storageBucket": settings.FIREBASE_STORAGE_BUCKET},
        )
        _firestore_client = firestore.client()
        _storage_bucket = storage.bucket()
        _firebase_initialized = True
        logger.info(f"Firebase initialized for project: {sa.get('project_id')}")
        return True

    except Exception as e:
        logger.error(f"Firebase initialization failed: {e}")
        _firebase_initialized = True
        return False


def get_firestore():
    """Get Firestore client (None if Firebase not configured)."""
    return _firestore_client


def get_storage_bucket():
    """Get Storage bucket (None if Firebase not configured)."""
    return _storage_bucket


def is_firebase_available() -> bool:
    return _firestore_client is not None


def verify_id_token(token: str) -> Optional[dict]:
    """Verify Firebase ID token. Returns decoded claims or None."""
    if not is_firebase_available():
        return None
    try:
        from firebase_admin import auth
        return auth.verify_id_token(token)
    except Exception as e:
        logger.warning(f"Token verification failed: {e}")
        return None
