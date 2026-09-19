"""
ClearWay AI — Vision Service
OpenCV vehicle detection and classification.
Labeled: SIMULATED CAMERA DATA when real camera not connected.
"""
import base64
import logging
import random
import math
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import numpy as np

from models.vehicle import Vehicle, VehicleType, VehicleComposition
from models.intersection import Camera

logger = logging.getLogger(__name__)


class VisionService:
    """
    AI Vision Traffic Monitor.
    Uses OpenCV for vehicle detection when a real frame is provided.
    Falls back to realistic simulation when no camera connected.
    """

    VEHICLE_COLORS = {
        VehicleType.CAR: (0, 120, 255),       # Blue
        VehicleType.MOTORCYCLE: (0, 200, 100), # Green
        VehicleType.BUS: (0, 60, 200),         # Dark Blue
        VehicleType.TRUCK: (180, 30, 30),      # Red
        VehicleType.EMERGENCY: (255, 50, 50),  # Bright Red
        VehicleType.PEDESTRIAN: (200, 200, 0), # Yellow
        VehicleType.AUTO_RICKSHAW: (200, 100, 0), # Orange
    }

    def __init__(self):
        self._opencv_available = self._check_opencv()
        self._bg_subtractors: Dict[str, any] = {}

    def _check_opencv(self) -> bool:
        try:
            import cv2
            return True
        except ImportError:
            logger.warning("OpenCV not available. Using simulated vehicle detection.")
            return False

    def _simulate_detections(
        self, camera: Camera, vehicle_count: int, congestion_score: float
    ) -> List[Dict]:
        """Generate realistic simulated bounding-box detections."""
        detections = []
        # Vehicle type distribution
        types_weights = [
            (VehicleType.CAR, 0.55),
            (VehicleType.MOTORCYCLE, 0.20),
            (VehicleType.BUS, 0.08),
            (VehicleType.TRUCK, 0.07),
            (VehicleType.AUTO_RICKSHAW, 0.07),
            (VehicleType.EMERGENCY, 0.03),
        ]

        for _ in range(min(vehicle_count, 25)):
            # Pick type
            r = random.random()
            cumulative = 0
            vtype = VehicleType.CAR
            for t, w in types_weights:
                cumulative += w
                if r < cumulative:
                    vtype = t
                    break

            # Random bounding box (normalized 0-1)
            x = random.uniform(0.05, 0.85)
            y = random.uniform(0.30, 0.85)
            w_norm = random.uniform(0.06, 0.15) if vtype in [VehicleType.CAR, VehicleType.MOTORCYCLE] \
                     else random.uniform(0.12, 0.22)
            h_norm = w_norm * random.uniform(0.5, 0.8)

            speed = max(0, 60 * (1 - congestion_score) + random.gauss(0, 5))
            is_queued = speed < 5.0

            detections.append({
                "id": f"v-{random.randint(1000, 9999)}",
                "type": vtype.value,
                "bbox": {"x": round(x, 3), "y": round(y, 3), "w": round(w_norm, 3), "h": round(h_norm, 3)},
                "speed_kmh": round(max(0, speed), 1),
                "is_queued": is_queued,
                "confidence": round(random.uniform(0.72, 0.98), 3),
                "lane": camera.direction,
                "data_source": "SIMULATED",
            })

        return detections

    def analyze_frame(
        self,
        camera: Camera,
        frame_data: Optional[bytes] = None,
        vehicle_count: int = 10,
        congestion_score: float = 0.4,
    ) -> Dict:
        """
        Analyze a camera frame. Uses OpenCV if frame provided, else simulation.
        """
        if frame_data and self._opencv_available:
            return self._opencv_analyze(camera, frame_data)
        else:
            return self._simulate_analysis(camera, vehicle_count, congestion_score)

    def _simulate_analysis(
        self, camera: Camera, vehicle_count: int, congestion_score: float
    ) -> Dict:
        detections = self._simulate_detections(camera, vehicle_count, congestion_score)
        comp = self._count_by_type(detections)
        return {
            "camera_id": camera.id,
            "camera_label": camera.label,
            "intersection_id": camera.intersection_id,
            "direction": camera.direction,
            "timestamp": datetime.utcnow().isoformat(),
            "frame_source": "SIMULATED — no real camera connected",
            "detections": detections,
            "vehicle_count": len(detections),
            "vehicle_composition": comp,
            "queue_length": len([d for d in detections if d["is_queued"]]),
            "average_speed_kmh": round(sum(d["speed_kmh"] for d in detections) / max(len(detections), 1), 1),
            "lane_occupancy": round(min(len(detections) / 10.0, 1.0), 2),
            "density": round(congestion_score, 3),
            "data_source": "SIMULATED",
        }

    def _opencv_analyze(self, camera: Camera, frame_data: bytes) -> Dict:
        """Basic OpenCV motion-based detection (when real frame available)."""
        try:
            import cv2
            nparr = np.frombuffer(frame_data, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if frame is None:
                return self._simulate_analysis(camera, 10, 0.4)

            # Background subtraction for motion detection
            cam_key = camera.id
            if cam_key not in self._bg_subtractors:
                self._bg_subtractors[cam_key] = cv2.createBackgroundSubtractorMOG2()

            fgmask = self._bg_subtractors[cam_key].apply(frame)
            contours, _ = cv2.findContours(fgmask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            detections = []
            h, w = frame.shape[:2]
            for cnt in contours:
                area = cv2.contourArea(cnt)
                if area < 500:
                    continue
                x, y, cw, ch = cv2.boundingRect(cnt)
                # Classify by size
                if area > 8000:
                    vtype = VehicleType.BUS.value
                elif area > 4000:
                    vtype = VehicleType.CAR.value
                else:
                    vtype = VehicleType.MOTORCYCLE.value

                detections.append({
                    "id": f"cv-{len(detections)}",
                    "type": vtype,
                    "bbox": {"x": x/w, "y": y/h, "w": cw/w, "h": ch/h},
                    "speed_kmh": random.uniform(5, 40),
                    "is_queued": area > 5000,
                    "confidence": round(min(area / 10000, 0.95), 3),
                    "lane": camera.direction,
                    "data_source": "OPENCV",
                })

            comp = self._count_by_type(detections)
            return {
                "camera_id": camera.id,
                "camera_label": camera.label,
                "intersection_id": camera.intersection_id,
                "direction": camera.direction,
                "timestamp": datetime.utcnow().isoformat(),
                "frame_source": "OPENCV — real frame",
                "detections": detections,
                "vehicle_count": len(detections),
                "vehicle_composition": comp,
                "queue_length": len([d for d in detections if d.get("is_queued")]),
                "average_speed_kmh": round(sum(d["speed_kmh"] for d in detections) / max(len(detections), 1), 1),
                "lane_occupancy": min(len(detections) / 10.0, 1.0),
                "density": min(len(detections) / 20.0, 1.0),
                "data_source": "OPENCV",
            }
        except Exception as e:
            logger.error(f"OpenCV analysis failed: {e}")
            return self._simulate_analysis(camera, 10, 0.4)

    def _count_by_type(self, detections: List[Dict]) -> Dict:
        comp = {vt.value: 0 for vt in VehicleType}
        for d in detections:
            t = d.get("type", VehicleType.CAR.value)
            if t in comp:
                comp[t] += 1
        return comp


# Singleton
vision_service = VisionService()
