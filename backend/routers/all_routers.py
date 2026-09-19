"""ClearWay AI — Remaining routers (pollution, predictions, simulation, events, ai_chat, reports, auth)"""
import random
from datetime import datetime
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional

# ── Pollution ──────────────────────────────────────────────────────────────
pollution_router = APIRouter(prefix="/pollution", tags=["pollution"])

@pollution_router.get("/estimates")
async def get_pollution_estimates(intersection_id: Optional[str] = None):
    from data.demo_seed import demo_store
    from services.pollution_service import pollution_service
    demo_store.initialize()
    intersections = demo_store.get_intersections()
    if intersection_id:
        intersections = [i for i in intersections if i.id == intersection_id]
    estimates = pollution_service.estimate_all(intersections)
    total_co2 = sum(e.co2_kg_per_hour for e in estimates)
    return {
        "estimates": [e.model_dump() for e in estimates],
        "network_totals": {
            "co2_kg_per_hour": round(total_co2, 2),
            "nox_g_per_hour": round(sum(e.nox_g_per_hour for e in estimates), 2),
            "pm25_g_per_hour": round(sum(e.pm25_g_per_hour for e in estimates), 4),
            "fuel_liters_per_hour": round(sum(e.fuel_liters_per_hour for e in estimates), 2),
            "avg_aqi": int(sum(e.aqi_estimate for e in estimates) / max(len(estimates), 1)),
        },
        "data_source": "ESTIMATED",
        "label": "ESTIMATED EMISSIONS — Not measured sensor data",
    }


@pollution_router.get("/trend/{intersection_id}")
async def get_pollution_trend(intersection_id: str, hours: int = 24):
    from data.demo_seed import demo_store
    from services.pollution_service import pollution_service
    demo_store.initialize()
    inter = demo_store.get_intersection(intersection_id)
    if not inter:
        return {"error": "Intersection not found"}
    trend = pollution_service.historical_trend(inter, hours)
    return {"trend": trend, "data_source": "ESTIMATED HISTORICAL"}


# ── Predictions ─────────────────────────────────────────────────────────────
predictions_router = APIRouter(prefix="/predictions", tags=["predictions"])

@predictions_router.get("")
async def get_predictions():
    from data.demo_seed import demo_store
    from services.prediction_service import prediction_service
    demo_store.initialize()
    intersections = demo_store.get_intersections()
    return prediction_service.predict_all(intersections)


# ── Simulation ─────────────────────────────────────────────────────────────
simulation_router = APIRouter(prefix="/simulation", tags=["simulation"])

@simulation_router.post("/run")
async def run_simulation(body: dict):
    from models.simulation import SimulationScenario, TrafficVolume
    from services.simulation_service import simulation_service
    scenario_data = body.get("scenario", {})
    scenario = SimulationScenario(
        id=scenario_data.get("id", "sim-" + str(random.randint(1000, 9999))),
        name=scenario_data.get("name", "Demo Simulation"),
        num_intersections=scenario_data.get("num_intersections", 6),
        traffic_volume=TrafficVolume(scenario_data.get("traffic_volume", "medium")),
        emergency_vehicle=scenario_data.get("emergency_vehicle", False),
        siren_detection=scenario_data.get("siren_detection", False),
        accident=scenario_data.get("accident", False),
        road_closure=scenario_data.get("road_closure", False),
        pedestrian_surge=scenario_data.get("pedestrian_surge", False),
        duration_minutes=min(scenario_data.get("duration_minutes", 15), 60),
    )
    result = simulation_service.run(scenario)
    return result.model_dump()


# ── Events ─────────────────────────────────────────────────────────────────
events_router = APIRouter(prefix="/events", tags=["events"])

@events_router.post("")
async def trigger_event(body: dict):
    from models.simulation import EventType
    from services.alert_service import alert_service
    from models.alert import AlertType
    from data.demo_seed import demo_store
    demo_store.initialize()

    event_type = body.get("type", "heavy_traffic")
    junction_id = body.get("intersection_id")
    inter = demo_store.get_intersection(junction_id) if junction_id else None

    # Affect the intersection state
    if inter:
        if event_type == "accident":
            inter.congestion_score = min(1.0, inter.congestion_score + 0.4)
            inter.queue_length = min(inter.queue_length + 30, 80)
            inter.vehicle_count = min(inter.vehicle_count + 20, 200)
            alert_service.create_alert(
                AlertType.ACCIDENT, f"Accident — {inter.label}",
                f"Accident reported at {inter.name}. Traffic severely impacted.",
                intersection=inter, data_source="DEMO",
            )
        elif event_type == "heavy_traffic":
            inter.congestion_score = min(1.0, inter.congestion_score + 0.25)
            inter.queue_length = min(inter.queue_length + 15, 60)
        elif event_type == "road_closure":
            inter.congestion_score = 0.95
            alert_service.create_alert(
                AlertType.ROAD_CLOSURE, f"Road Closure — {inter.label}",
                f"Road closure at {inter.name}. Alternate routes recommended.",
                intersection=inter, data_source="DEMO",
            )
        elif event_type == "pedestrian_surge":
            inter.queue_length = min(inter.queue_length + 20, 60)
        elif event_type == "emergency_vehicle":
            from services.emergency_service import emergency_service
            from models.emergency import EmergencyActivateRequest
            req = EmergencyActivateRequest(
                origin_intersection_id=inter.id,
                destination_name="City Hospital",
                detected_via="CAMERA",
            )
            intersections = demo_store.get_intersections()
            roads = demo_store.roads
            emergency_service.activate_corridor(req, intersections, roads)

        demo_store.update_intersection(inter)

    return {
        "event_type": event_type,
        "affected_junction": inter.label if inter else "all",
        "timestamp": datetime.utcnow().isoformat(),
        "ai_response": {
            "steps": [
                "Recalculating traffic flow",
                "Identifying alternate routes",
                "Adjusting nearby signal timings",
                "Updating congestion predictions",
                "Recalculating pollution estimates",
                "Generating operator alert",
            ],
            "data_source": "SIMULATED",
        }
    }


# ── AI Chat ────────────────────────────────────────────────────────────────
ai_chat_router = APIRouter(prefix="/ai", tags=["ai"])

class ChatRequest(BaseModel):
    message: str
    context: Optional[dict] = None


@ai_chat_router.post("/chat")
async def ai_chat(request: ChatRequest):
    from data.demo_seed import demo_store
    from services.ai_assistant_service import create_ai_assistant
    from services.alert_service import alert_service
    from services.emergency_service import emergency_service
    from services.audio_alert_service import audio_alert_service
    from services.pollution_service import pollution_service
    from config import get_settings

    settings = get_settings()
    assistant = create_ai_assistant(settings)

    demo_store.initialize()
    intersections = demo_store.get_intersections()
    pollution = pollution_service.estimate_all(intersections)
    emergency = emergency_service.get_status()

    backend_state = {
        "data_mode": settings.DATA_MODE.value,
        "intersections": [i.model_dump() for i in intersections],
        "alerts": [a.model_dump() for a in alert_service.get_all(active_only=True)],
        "emergency": emergency.model_dump(),
        "siren_events": [e.model_dump() for e in audio_alert_service.get_active_events().values()],
        "pollution": [p.model_dump() for p in pollution],
        "latest_optimization": request.context.get("latest_optimization") if request.context else None,
    }

    response = await assistant.chat(request.message, backend_state)
    return response


# ── Reports ─────────────────────────────────────────────────────────────────
reports_router = APIRouter(prefix="/reports", tags=["reports"])

@reports_router.get("")
async def get_reports():
    return {"reports": [], "message": "No saved reports yet. Use /reports/generate to create one."}


@reports_router.post("/generate")
async def generate_report(body: dict):
    from fastapi.responses import Response
    from services.report_service import report_service
    from data.demo_seed import demo_store
    from services.alert_service import alert_service

    demo_store.initialize()
    intersections = demo_store.get_intersections()
    alerts = alert_service.get_all()
    fmt = body.get("format", "pdf")

    if fmt == "csv":
        content = report_service.generate_csv(intersections, alerts)
        return Response(
            content=content,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=clearway_report.csv"},
        )
    else:
        content = report_service.generate_pdf_bytes(intersections, alerts)
        return Response(
            content=content,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=clearway_report.pdf"},
        )


# ── Auth ────────────────────────────────────────────────────────────────────
auth_router = APIRouter(prefix="/auth", tags=["auth"])

@auth_router.post("/login")
async def login(body: dict):
    from services.auth_service import auth_service
    from models.user import LoginRequest
    request = LoginRequest(email=body.get("email", ""), password=body.get("password", ""))
    result = auth_service.login_demo(request)
    if not result:
        from fastapi import HTTPException
        raise HTTPException(401, "Invalid credentials. Check demo users in /auth/demo-users")
    return result.model_dump()


@auth_router.get("/demo-users")
async def get_demo_users():
    from services.auth_service import auth_service
    return {"demo_users": auth_service.get_demo_users_info()}


@auth_router.get("/config")
async def get_firebase_config():
    from config import get_settings
    settings = get_settings()
    return {"firebase_config": settings.firebase_web_config, "system_status": settings.system_status}
