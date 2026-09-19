"""ClearWay AI — Siren Detection router"""
import os
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from models.siren import SirenEventRequest, SirenAcknowledgeRequest, SirenStatus
from services.audio_alert_service import audio_alert_service
from data.demo_seed import demo_store

router = APIRouter(prefix="/siren", tags=["siren"])


@router.post("/event")
async def report_siren_event(request: SirenEventRequest):
    """Report a siren detection event (from audio_alert_service)."""
    event = audio_alert_service.process_event_request(request)
    # Auto-dispatch alert
    dispatch = audio_alert_service.dispatch_police_alert(event)
    return {
        "event": event.model_dump(),
        "dispatch": dispatch.model_dump(),
        "label": "SIMULATED RADIO DISPATCH",
    }


@router.post("/detect/{junction_id}")
async def trigger_siren_detection(junction_id: str, force: bool = True):
    """Trigger a simulated siren detection at a junction."""
    demo_store.initialize()
    inter = demo_store.get_intersection(junction_id)
    if not inter:
        raise HTTPException(404, f"Junction {junction_id} not found")

    event = audio_alert_service.simulate_detection(
        junction_id, inter.label, force_detect=force, data_source="SIMULATED"
    )
    if not event:
        return {"detected": False, "message": "No siren detected (below threshold)"}

    dispatch = audio_alert_service.dispatch_police_alert(event)
    return {
        "detected": True,
        "event": event.model_dump(),
        "dispatch": dispatch.model_dump(),
        "label": "SIMULATED",
    }


@router.get("/status/{junction_id}")
async def get_siren_status(junction_id: str):
    demo_store.initialize()
    inter = demo_store.get_intersection(junction_id)
    label = inter.label if inter else junction_id
    status = audio_alert_service.get_junction_status(junction_id, label)
    return status.model_dump()


@router.get("/status")
async def get_all_siren_statuses():
    demo_store.initialize()
    intersections = demo_store.get_intersections()
    statuses = [
        audio_alert_service.get_junction_status(i.id, i.label).model_dump()
        for i in intersections
    ]
    return {"statuses": statuses, "data_source": "SIMULATED"}


@router.post("/acknowledge")
async def acknowledge_siren(request: SirenAcknowledgeRequest):
    """Officer acknowledges/updates clearance status."""
    event = next(
        (e for e in audio_alert_service.get_active_events().values()
         if e.id == request.siren_event_id),
        None
    )
    if event is None:
        raise HTTPException(404, "Siren event not found or already resolved")

    dispatch = audio_alert_service.acknowledge(
        event.junction_id, request.officer_status, request.officer_id
    )
    return {
        "success": True,
        "status": request.officer_status.value,
        "dispatch": dispatch.model_dump() if dispatch else None,
    }


@router.post("/dispatch-alert")
async def dispatch_alert(junction_id: str):
    """Manually dispatch police alert for a junction."""
    active = audio_alert_service.get_active_events()
    event = active.get(junction_id)
    if not event:
        raise HTTPException(404, "No active siren event for this junction")
    dispatch = audio_alert_service.dispatch_police_alert(event)
    return {"dispatch": dispatch.model_dump(), "label": "SIMULATED RADIO DISPATCH"}


@router.get("/events")
async def get_siren_events(active_only: bool = False):
    if active_only:
        events = list(audio_alert_service.get_active_events().values())
    else:
        events = audio_alert_service.get_all_events()
    return {"events": [e.model_dump() for e in events], "count": len(events)}


@router.get("/dispatches")
async def get_dispatches():
    dispatches = audio_alert_service.get_all_dispatches()
    return {"dispatches": [d.model_dump() for d in dispatches], "count": len(dispatches)}


@router.get("/audio/{filename}")
async def get_audio_file(filename: str):
    """Serve generated TTS audio file."""
    path = audio_alert_service.get_audio_file_path(filename)
    if path and os.path.exists(path):
        return FileResponse(path, media_type="audio/mpeg")
    raise HTTPException(404, "Audio file not found")
