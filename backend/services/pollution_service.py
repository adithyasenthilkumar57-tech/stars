"""
ClearWay AI — Pollution Estimation Service
Emission estimates from vehicle count, type, density, and idling time.
Always labeled: ESTIMATED EMISSIONS — not measured sensor data.
"""
import math
import random
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from models.pollution import PollutionEstimate, EMISSION_FACTORS, IDLE_FACTOR
from models.intersection import Intersection
from models.vehicle import VehicleComposition


AQI_BREAKPOINTS = [
    (0, 50, "Good"),
    (51, 100, "Moderate"),
    (101, 150, "Unhealthy for Sensitive Groups"),
    (151, 200, "Unhealthy"),
    (201, 300, "Very Unhealthy"),
    (301, 500, "Hazardous"),
]


class PollutionService:
    """
    Estimates traffic-related emissions from traffic state.
    Formula: emission = Σ(vehicle_type_count × emission_factor × distance_km × idle_multiplier)
    All outputs: ESTIMATED EMISSIONS — not from real sensors.
    """

    def _aqi_from_pm25(self, pm25_g_per_hour: float) -> tuple:
        """Convert PM2.5 estimate to AQI (simplified EPA breakpoints)."""
        # Convert to μg/m³ (very rough approximation for demo)
        ugm3 = pm25_g_per_hour * 1000 / (3600 * 0.1)  # assuming 0.1 m³/s dispersion
        ugm3 = min(ugm3, 500)

        aqi = int(ugm3 * 2.5)  # simplified linear scale
        aqi = max(0, min(500, aqi))

        category = "Unknown"
        for lo, hi, cat in AQI_BREAKPOINTS:
            if lo <= aqi <= hi:
                category = cat
                break

        return aqi, category

    def estimate(
        self,
        intersection: Intersection,
        vehicle_composition: Optional[VehicleComposition] = None,
        duration_minutes: float = 60.0,
    ) -> PollutionEstimate:
        """
        Compute emission estimate for an intersection.
        """
        # Default composition if not provided
        if vehicle_composition is None:
            n = max(intersection.vehicle_count, 1)
            vehicle_composition = VehicleComposition(
                cars=int(n * 0.60),
                motorcycles=int(n * 0.20),
                buses=int(n * 0.08),
                trucks=int(n * 0.07),
                auto_rickshaws=int(n * 0.05),
            )

        idle_fraction = min(
            intersection.queue_length / max(intersection.vehicle_count, 1), 0.95
        )

        # Average travel distance per vehicle through intersection (km)
        avg_distance_km = 0.3

        co2 = co = nox = pm25 = pm10 = fuel = 0.0

        type_map = {
            "cars": vehicle_composition.cars,
            "motorcycles": vehicle_composition.motorcycles,
            "buses": vehicle_composition.buses,
            "trucks": vehicle_composition.trucks,
            "auto_rickshaws": vehicle_composition.auto_rickshaws,
        }

        for vtype, count in type_map.items():
            ef = EMISSION_FACTORS.get(vtype, {})
            idle_mult = 1.0 + idle_fraction * (IDLE_FACTOR - 1.0)
            dist_adjusted = avg_distance_km * idle_mult

            co2  += count * ef.get("co2",  100) * dist_adjusted / 1000  # kg/hr
            co   += count * ef.get("co",   1.0) * dist_adjusted         # g/hr
            nox  += count * ef.get("nox",  0.1) * dist_adjusted         # g/hr
            pm25 += count * ef.get("pm25", 0.005) * dist_adjusted       # g/hr
            pm10 += count * ef.get("pm10", 0.010) * dist_adjusted       # g/hr
            fuel += count * ef.get("fuel_liters", 0.05) * dist_adjusted # L/hr

        # Add noise for realism
        noise = lambda v: v * (1 + random.gauss(0, 0.04))
        co2, co, nox, pm25, pm10, fuel = (
            noise(co2), noise(co), noise(nox), noise(pm25), noise(pm10), noise(fuel)
        )

        aqi, aqi_cat = self._aqi_from_pm25(pm25)

        # Dominant vehicle type
        dominant = max(type_map.items(), key=lambda x: x[1])[0]

        # AI insight
        insight = None
        if aqi > 150:
            insight = (
                f"High estimated emissions at {intersection.label} due to elevated queue "
                f"({intersection.queue_length} vehicles idling). "
                f"Signal optimization could reduce idle time and estimated emissions by ~15-25%."
            )
        elif aqi > 100:
            insight = f"Moderate estimated emissions at {intersection.label}. Queue reduction recommended."

        return PollutionEstimate(
            intersection_id=intersection.id,
            junction_label=intersection.label,
            timestamp=datetime.utcnow(),
            co2_kg_per_hour=round(co2, 3),
            co_g_per_hour=round(co, 2),
            nox_g_per_hour=round(nox, 3),
            pm25_g_per_hour=round(pm25, 4),
            pm10_g_per_hour=round(pm10, 4),
            fuel_liters_per_hour=round(fuel, 3),
            vehicle_count=intersection.vehicle_count,
            queue_length=intersection.queue_length,
            idle_fraction=round(idle_fraction, 3),
            dominant_vehicle_type=dominant,
            aqi_estimate=aqi,
            aqi_category=aqi_cat,
            ai_insight=insight,
            data_source="ESTIMATED",
        )

    def estimate_all(self, intersections: List[Intersection]) -> List[PollutionEstimate]:
        return [self.estimate(i) for i in intersections]

    def historical_trend(
        self,
        intersection: Intersection,
        hours: int = 24,
    ) -> List[Dict]:
        """Generate historical emission trend for the past N hours."""
        now = datetime.utcnow()
        history = []
        for h in range(hours, -1, -1):
            ts = now - timedelta(hours=h)
            hour = ts.hour
            # Simulate historical vehicle count based on time of day
            factor = 0.8 if (8 <= hour <= 10 or 17 <= hour <= 19) else 0.4
            base_vehicles = int(intersection.road_capacity * factor / 60)
            mock_inter = intersection.copy()
            mock_inter.vehicle_count = base_vehicles
            mock_inter.queue_length = int(base_vehicles * 0.3)
            est = self.estimate(mock_inter)
            history.append({
                "timestamp": ts.isoformat(),
                "hour": hour,
                "co2_kg_per_hour": est.co2_kg_per_hour,
                "nox_g_per_hour": est.nox_g_per_hour,
                "pm25_g_per_hour": est.pm25_g_per_hour,
                "aqi_estimate": est.aqi_estimate,
                "vehicle_count": base_vehicles,
                "data_label": "ESTIMATED",
            })
        return history


# Singleton
pollution_service = PollutionService()
