"""
ClearWay AI — FastAPI Application Entry Point
Quantum-Enhanced Adaptive Urban Traffic Optimization

Backend-first: all frontend data comes through these endpoints.
Never exposes Firebase credentials or API keys to clients.
"""
import asyncio
import logging
import random
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from config import get_settings
from firebase_admin_init import init_firebase
from websocket_manager import ws_manager

# Routers
from routers.traffic import router as traffic_router
from routers.intersections import router as intersections_router
from routers.cameras import router as cameras_router
from routers.microphones import router as microphones_router
from routers.optimization import router as optimization_router
from routers.emergency import router as emergency_router
from routers.siren import router as siren_router
from routers.all_routers import (
    pollution_router, predictions_router, simulation_router,
    events_router, ai_chat_router, reports_router, auth_router,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger("clearway")

settings = get_settings()

# ── Background Tasks ──────────────────────────────────────────────────────

async def traffic_tick_loop():
    """Push live traffic updates to all WebSocket clients every 5 seconds."""
    from data.demo_seed import demo_store
    from services.alert_service import alert_service

    demo_store.initialize()
    while True:
        try:
            if ws_manager.active_connections:
                intersections = demo_store.get_intersections()
                for inter in intersections:
                    delta = random.uniform(-0.02, 0.03)
                    inter.congestion_score = max(0.0, min(1.0, inter.congestion_score + delta))
                    inter.vehicle_count = max(0, inter.vehicle_count + random.randint(-1, 2))
                    inter.queue_length = max(0, inter.queue_length + random.randint(-1, 1))
                    inter.last_updated = datetime.utcnow()

                # Auto-generate traffic alerts
                alert_service.check_and_create_traffic_alerts(intersections)
                alert_service.auto_resolve_expired()

                await ws_manager.broadcast_traffic_update(intersections)
        except Exception as e:
            logger.error(f"Traffic tick error: {e}")

        await asyncio.sleep(5)


async def emergency_tick_loop():
    """Advance emergency corridor every 8 seconds when active."""
    from services.emergency_service import emergency_service
    from models.emergency import CorridorStatus

    while True:
        try:
            if emergency_service.is_active:
                status = emergency_service.advance_corridor()
                await ws_manager.broadcast_emergency_update(status.model_dump())
        except Exception as e:
            logger.error(f"Emergency tick error: {e}")
        await asyncio.sleep(8)


# ── App Lifecycle ─────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    logger.info("╔══════════════════════════════════════════╗")
    logger.info("║  ClearWay AI — Starting Up               ║")
    logger.info("║  Quantum-Enhanced Traffic Optimization   ║")
    logger.info("╚══════════════════════════════════════════╝")

    # Init Firebase (or log not-configured)
    firebase_ok = init_firebase(settings)
    logger.info(f"Firebase: {'✓ Connected' if firebase_ok else '✗ Not configured (DEMO mode)'}")
    logger.info(f"Gemini AI: {'✓ Available' if settings.gemini_available else '✗ Not configured (fallback mode)'}")
    logger.info(f"Data mode: {settings.DATA_MODE.value}")

    # Seed demo data
    from data.demo_seed import demo_store
    demo_store.initialize()
    logger.info(f"Demo data: ✓ {len(demo_store.get_intersections())} intersections seeded")

    # Create audio_alerts directory
    Path("audio_alerts").mkdir(exist_ok=True)

    # Start background tasks
    tick_task = asyncio.create_task(traffic_tick_loop())
    em_task = asyncio.create_task(emergency_tick_loop())
    logger.info("Background tasks started ✓")
    logger.info("ClearWay AI ready — http://localhost:8000")
    logger.info("API docs — http://localhost:8000/docs")

    yield

    # Shutdown
    tick_task.cancel()
    em_task.cancel()
    logger.info("ClearWay AI stopped.")


# ── FastAPI App ───────────────────────────────────────────────────────────

app = FastAPI(
    title="ClearWay AI",
    description=(
        "Quantum-Enhanced Adaptive Urban Traffic Optimization. "
        "All quantum results use QUANTUM SIMULATOR (Qiskit Aer) — never real hardware. "
        "All emissions are ESTIMATED. All audio alerts are SIMULATED RADIO DISPATCH."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:3000", "http://localhost:3001", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files (TTS audio)
Path("audio_alerts").mkdir(exist_ok=True)
app.mount("/audio", StaticFiles(directory="audio_alerts"), name="audio")

# ── Routers ──────────────────────────────────────────────────────────────

app.include_router(traffic_router)
app.include_router(intersections_router)
app.include_router(cameras_router)
app.include_router(microphones_router)
app.include_router(optimization_router)
app.include_router(emergency_router)
app.include_router(siren_router)
app.include_router(pollution_router)
app.include_router(predictions_router)
app.include_router(simulation_router)
app.include_router(events_router)
app.include_router(ai_chat_router)
app.include_router(reports_router)
app.include_router(auth_router)

# ── WebSocket ─────────────────────────────────────────────────────────────

@app.websocket("/ws/traffic")
async def websocket_traffic(websocket: WebSocket):
    """Real-time traffic state stream."""
    await ws_manager.connect(websocket)
    try:
        # Send initial state on connect
        from data.demo_seed import demo_store
        demo_store.initialize()
        await ws_manager.broadcast_traffic_update(demo_store.get_intersections())
        await ws_manager.broadcast_system_status(settings.system_status)

        while True:
            # Keep connection alive; data pushed by background tasks
            try:
                msg = await asyncio.wait_for(websocket.receive_text(), timeout=30)
                if msg == "ping":
                    await websocket.send_text('{"type":"pong"}')
            except asyncio.TimeoutError:
                await websocket.send_text('{"type":"heartbeat"}')
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)


# ── Root ─────────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {
        "product": "ClearWay AI",
        "tagline": "Quantum-Enhanced Adaptive Urban Traffic Optimization",
        "version": "1.0.0",
        "status": settings.system_status,
        "docs": "/docs",
        "labels": {
            "quantum": "QUANTUM SIMULATOR — Qiskit Aer, not real quantum hardware",
            "emissions": "ESTIMATED EMISSIONS — not measured sensor data",
            "audio": "SIMULATED RADIO DISPATCH — not real police radio",
            "camera": "SIMULATED CAMERA DATA — when real camera not connected",
        }
    }


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "system": settings.system_status,
    }
