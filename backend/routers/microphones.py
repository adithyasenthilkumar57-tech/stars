"""ClearWay AI — Microphones router"""
from fastapi import APIRouter
from data.demo_seed import demo_store
from services.audio_alert_service import audio_alert_service

router = APIRouter(prefix="/microphones", tags=["microphones"])


@router.get("")
async def get_microphones():
    demo_store.initialize()
    intersections = demo_store.get_intersections()
    microphones = []
    for inter in intersections:
        for mic in inter.microphones:
            status = audio_alert_service.get_junction_status(inter.id, inter.label)
            microphones.append({
                **mic.model_dump(),
                "intersection_label": inter.label,
                "intersection_name": inter.name,
                "siren_status": status.status.value,
                "monitoring_active": status.monitoring_active,
            })
    return {"microphones": microphones, "count": len(microphones), "data_source": "SIMULATED"}
