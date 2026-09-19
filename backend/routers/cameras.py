"""ClearWay AI — Cameras router"""
from fastapi import APIRouter
from data.demo_seed import demo_store
from services.vision_service import vision_service

router = APIRouter(prefix="/cameras", tags=["cameras"])


@router.get("")
async def get_cameras():
    demo_store.initialize()
    intersections = demo_store.get_intersections()
    cameras = []
    for inter in intersections:
        for cam in inter.cameras:
            cameras.append({**cam.model_dump(), "intersection_label": inter.label, "intersection_name": inter.name})
    return {"cameras": cameras, "count": len(cameras)}


@router.get("/{camera_id}/analyze")
async def analyze_camera(camera_id: str):
    """Analyze a camera feed (simulated when no real frame)."""
    demo_store.initialize()
    intersections = demo_store.get_intersections()
    for inter in intersections:
        for cam in inter.cameras:
            if cam.id == camera_id:
                result = vision_service.analyze_frame(cam, None, inter.vehicle_count, inter.congestion_score)
                return result
    return {"error": "Camera not found"}
