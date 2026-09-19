"""ClearWay AI — Intersections router"""
import random
from datetime import datetime
from fastapi import APIRouter, HTTPException
from data.demo_seed import demo_store
from services.pollution_service import pollution_service
from services.prediction_service import prediction_service

router = APIRouter(prefix="/intersections", tags=["intersections"])


@router.get("")
async def get_intersections():
    demo_store.initialize()
    intersections = demo_store.get_intersections()
    return {"intersections": [i.model_dump() for i in intersections], "count": len(intersections)}


@router.get("/{intersection_id}")
async def get_intersection(intersection_id: str):
    demo_store.initialize()
    inter = demo_store.get_intersection(intersection_id)
    if not inter:
        raise HTTPException(status_code=404, detail=f"Intersection {intersection_id} not found")
    prediction = prediction_service.predict_intersection(inter)
    pollution = pollution_service.estimate(inter)
    return {
        "intersection": inter.model_dump(),
        "prediction": prediction,
        "pollution": pollution.model_dump(),
    }
