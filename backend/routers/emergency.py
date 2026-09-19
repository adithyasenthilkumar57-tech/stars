"""ClearWay AI — Emergency router"""
from fastapi import APIRouter, HTTPException
from models.emergency import EmergencyActivateRequest, CorridorStatus
from services.emergency_service import emergency_service
from data.demo_seed import demo_store

router = APIRouter(prefix="/emergency", tags=["emergency"])


@router.post("/activate")
async def activate_emergency(request: EmergencyActivateRequest):
    """Activate emergency green corridor."""
    demo_store.initialize()
    intersections = demo_store.get_intersections()
    roads = demo_store.roads
    status = emergency_service.activate_corridor(request, intersections, roads)
    return status.model_dump()


@router.post("/advance")
async def advance_corridor():
    """Advance ambulance one junction (for demo purposes)."""
    status = emergency_service.advance_corridor()
    return status.model_dump()


@router.post("/complete")
async def complete_corridor():
    """Mark corridor as complete and start re-optimization."""
    status = emergency_service.complete_corridor()
    return status.model_dump()


@router.post("/reset")
async def reset_corridor():
    """Reset corridor to inactive."""
    emergency_service.reset()
    return {"status": "reset", "corridor_status": CorridorStatus.INACTIVE.value}


@router.get("/status")
async def get_emergency_status():
    """Get current emergency corridor status."""
    status = emergency_service.get_status()
    return status.model_dump()


@router.post("/route")
async def calculate_route(request: EmergencyActivateRequest):
    """Calculate optimal route without activating corridor (preview)."""
    demo_store.initialize()
    intersections = demo_store.get_intersections()
    roads = demo_store.roads
    # Temporarily activate then get route
    status = emergency_service.activate_corridor(request, intersections, roads)
    return {
        "route": status.route.model_dump() if status.route else None,
        "data_source": "SIMULATED",
    }
