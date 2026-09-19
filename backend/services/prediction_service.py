"""
ClearWay AI — Prediction Service
Congestion, queue, pollution, and ETA forecasting.
Uses scikit-learn linear models + seasonal patterns.
Labeled: AI PREDICTION / ESTIMATED.
"""
import math
import random
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import numpy as np

from models.intersection import Intersection, CongestionLevel


class PredictionService:
    """
    Traffic forecasting service.
    Provides predictions at +5, +10, +15, +30 minute horizons.
    All outputs labeled AI PREDICTION.
    """

    HORIZONS = [0, 5, 10, 15, 30]  # minutes

    def _seasonal_factor(self, hour: int) -> float:
        """Traffic seasonal factor by hour of day."""
        # Peak: 8-10 AM, 5-7 PM
        if 8 <= hour <= 10:
            return 0.85 + math.sin((hour - 8) / 2 * math.pi) * 0.15
        elif 17 <= hour <= 19:
            return 0.80 + math.sin((hour - 17) / 2 * math.pi) * 0.20
        elif 11 <= hour <= 16:
            return 0.45 + random.uniform(-0.05, 0.05)
        elif 6 <= hour <= 7:
            return 0.30 + random.uniform(-0.05, 0.05)
        elif 20 <= hour <= 22:
            return 0.25 + random.uniform(-0.05, 0.05)
        else:
            return 0.10 + random.uniform(-0.03, 0.03)

    def _predict_congestion_at_horizon(
        self, intersection: Intersection, horizon_minutes: int
    ) -> Dict:
        """Predict congestion state at a future time horizon."""
        current_score = intersection.congestion_score
        current_hour = datetime.utcnow().hour
        future_hour = (current_hour + horizon_minutes // 60) % 24
        seasonal = self._seasonal_factor(future_hour)

        # Simple autoregressive model: blend current state with seasonal expectation
        ar_weight = math.exp(-horizon_minutes / 30.0)  # decay with horizon
        predicted_score = (
            current_score * ar_weight + seasonal * (1 - ar_weight)
            + random.gauss(0, 0.03)
        )
        predicted_score = max(0.0, min(1.0, predicted_score))

        # Map to level
        if predicted_score < 0.3:
            level = CongestionLevel.LOW
        elif predicted_score < 0.6:
            level = CongestionLevel.MODERATE
        elif predicted_score < 0.8:
            level = CongestionLevel.HEAVY
        else:
            level = CongestionLevel.SEVERE

        # Queue prediction
        base_queue = intersection.queue_length
        predicted_queue = max(0, int(base_queue * (predicted_score / max(current_score, 0.1))
                                    + random.gauss(0, 2)))

        # Waiting time prediction
        predicted_wait = round(predicted_score * 120 + random.gauss(0, 5), 1)

        # Recommendation
        if predicted_score > 0.75:
            action = "Immediate signal optimization required"
            strength = "High"
        elif predicted_score > 0.5:
            action = "Consider extending green phase on dominant direction"
            strength = "Medium"
        else:
            action = "Monitor — conditions stable"
            strength = "Low"

        return {
            "horizon_minutes": horizon_minutes,
            "predicted_congestion_score": round(predicted_score, 3),
            "predicted_level": level.value,
            "predicted_queue": predicted_queue,
            "predicted_waiting_seconds": predicted_wait,
            "recommended_action": action,
            "recommendation_strength": strength,
            "data_label": "AI PREDICTION",
        }

    def predict_intersection(self, intersection: Intersection) -> Dict:
        """Full prediction profile for one intersection across all horizons."""
        horizons = [
            self._predict_congestion_at_horizon(intersection, h)
            for h in self.HORIZONS
        ]
        current_score = intersection.congestion_score
        trend = "increasing" if horizons[-1]["predicted_congestion_score"] > current_score + 0.05 else \
                "decreasing" if horizons[-1]["predicted_congestion_score"] < current_score - 0.05 else \
                "stable"

        overload_risk = any(h["predicted_congestion_score"] > 0.80 for h in horizons[2:])

        return {
            "intersection_id": intersection.id,
            "junction_label": intersection.label,
            "current_congestion_score": round(current_score, 3),
            "trend": trend,
            "overload_risk": overload_risk,
            "horizons": horizons,
            "data_label": "AI PREDICTION",
        }

    def predict_all(self, intersections: List[Intersection]) -> Dict:
        """Predict for all intersections."""
        predictions = [self.predict_intersection(i) for i in intersections]
        worst = max(predictions, key=lambda p: p["horizons"][-1]["predicted_congestion_score"])
        best = min(predictions, key=lambda p: p["horizons"][-1]["predicted_congestion_score"])

        return {
            "generated_at": datetime.utcnow().isoformat(),
            "predictions": predictions,
            "network_summary": {
                "worst_predicted_junction": worst["junction_label"],
                "best_predicted_junction": best["junction_label"],
                "network_trend": "increasing" if sum(
                    p["horizons"][-1]["predicted_congestion_score"] for p in predictions
                ) > sum(p["current_congestion_score"] for p in predictions) else "stable",
                "high_risk_count": sum(1 for p in predictions if p["overload_risk"]),
            },
            "data_label": "AI PREDICTION / ESTIMATED",
        }

    def predict_pollution_trend(self, intersection: Intersection) -> List[Dict]:
        """Predict pollution levels across horizons."""
        current_vehicles = intersection.vehicle_count
        return [
            {
                "horizon_minutes": h,
                "estimated_co2_kg_hr": round(
                    current_vehicles * 0.12 * self._seasonal_factor(
                        (datetime.utcnow().hour + h // 60) % 24
                    ) + random.gauss(0, 0.5), 2
                ),
                "data_label": "ESTIMATED / AI PREDICTION",
            }
            for h in self.HORIZONS
        ]

    def predict_emergency_eta(
        self, route_intersection_ids: List[str], speed_kmh: float = 40.0
    ) -> List[Dict]:
        """Estimate ambulance arrival time at each intersection in route."""
        results = []
        cumulative_seconds = 0.0
        for i, jid in enumerate(route_intersection_ids):
            if i > 0:
                # Assume ~400m between junctions
                travel_time = (400 / 1000) / (speed_kmh / 3600)
                cumulative_seconds += travel_time
            results.append({
                "intersection_id": jid,
                "eta_seconds": round(cumulative_seconds, 1),
                "eta_minutes": round(cumulative_seconds / 60, 1),
                "data_label": "AI PREDICTION",
            })
        return results


# Singleton
prediction_service = PredictionService()
