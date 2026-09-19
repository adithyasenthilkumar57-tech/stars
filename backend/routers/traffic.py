"""ClearWay AI — Traffic router"""
import random
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from data.demo_seed import demo_store
from services.pollution_service import pollution_service

router = APIRouter(prefix="/traffic", tags=["traffic"])


@router.get("/live")
async def get_live_traffic():
    """Get current traffic state for all intersections."""
    demo_store.initialize()
    intersections = demo_store.get_intersections()
    # Live-tick small random changes to simulate movement
    for inter in intersections:
        delta = random.uniform(-0.03, 0.04)
        inter.congestion_score = max(0.0, min(1.0, inter.congestion_score + delta))
        inter.vehicle_count = max(0, inter.vehicle_count + random.randint(-2, 3))
        inter.queue_length = max(0, inter.queue_length + random.randint(-1, 2))
        inter.last_updated = datetime.utcnow()
    return {
        "data_mode": "DEMO",
        "timestamp": datetime.utcnow().isoformat(),
        "intersections": [i.model_dump() for i in intersections],
        "network_summary": {
            "active_intersections": len(intersections),
            "total_vehicles": sum(i.vehicle_count for i in intersections),
            "avg_congestion": round(sum(i.congestion_score for i in intersections) / max(len(intersections), 1), 3),
            "avg_waiting_seconds": round(sum(i.waiting_time_seconds for i in intersections) / max(len(intersections), 1), 1),
        }
    }


@router.get("/history")
async def get_traffic_history(hours: int = 24, intersection_id: str = None):
    """Get historical traffic snapshots (simulated)."""
    demo_store.initialize()
    intersections = demo_store.get_intersections()
    if intersection_id:
        intersections = [i for i in intersections if i.id == intersection_id]

    history = []
    now = datetime.utcnow()
    for h in range(hours, -1, -1):
        ts = now - timedelta(hours=h)
        hour = ts.hour
        factor = 0.85 if (8 <= hour <= 10 or 17 <= hour <= 19) else 0.4
        history.append({
            "timestamp": ts.isoformat(),
            "hour": hour,
            "avg_congestion": round(factor + random.gauss(0, 0.05), 3),
            "total_vehicles": int(sum(i.road_capacity for i in intersections) * factor / 60 + random.gauss(0, 5)),
            "avg_waiting_seconds": round(factor * 120 + random.gauss(0, 10), 1),
            "avg_queue": round(factor * 25 + random.gauss(0, 3), 1),
            "data_label": "SIMULATED HISTORICAL",
        })
    return {"history": history, "data_label": "SIMULATED HISTORICAL"}
