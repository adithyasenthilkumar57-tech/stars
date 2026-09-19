"""
ClearWay AI — Demo Data Seed
Generates 6 interconnected intersections in Tiruppur, Tamil Nadu.
"""
import math
import random
from datetime import datetime
from typing import List, Dict

BASE_LAT = 11.1085
BASE_LON = 77.3411

INTERSECTIONS_SEED = [
    {"id": "J1", "label": "J1", "name": "Town Hall Junction",      "lat_offset": 0.000, "lon_offset": 0.000, "road_capacity": 900, "lane_count": 4, "connections": ["J2", "J4"]},
    {"id": "J2", "label": "J2", "name": "Market Road Junction",    "lat_offset": 0.005, "lon_offset": 0.000, "road_capacity": 750, "lane_count": 4, "connections": ["J1", "J3", "J5"]},
    {"id": "J3", "label": "J3", "name": "College Road Junction",   "lat_offset": 0.010, "lon_offset": 0.000, "road_capacity": 700, "lane_count": 3, "connections": ["J2", "J6"]},
    {"id": "J4", "label": "J4", "name": "Ring Road Junction",      "lat_offset": 0.000, "lon_offset": 0.008, "road_capacity": 1000,"lane_count": 6, "connections": ["J1", "J5"]},
    {"id": "J5", "label": "J5", "name": "Hospital Road Junction",  "lat_offset": 0.005, "lon_offset": 0.008, "road_capacity": 800, "lane_count": 4, "connections": ["J2", "J4", "J6"]},
    {"id": "J6", "label": "J6", "name": "City Hospital Junction",  "lat_offset": 0.010, "lon_offset": 0.008, "road_capacity": 600, "lane_count": 3, "connections": ["J3", "J5"]},
]

ROADS_SEED = [
    ("J1", "J2", "Town Hall - Market Road", 450),
    ("J2", "J3", "Market - College Road", 380),
    ("J4", "J5", "Ring Road North", 500),
    ("J5", "J6", "Hospital Road", 350),
    ("J1", "J4", "East Connector", 420),
    ("J2", "J5", "Central Link", 480),
    ("J3", "J6", "North Bypass", 410),
]

DEMO_ORG = {"id": "org-tnta-001", "name": "Tamil Nadu Traffic Authority", "country": "India", "state": "Tamil Nadu"}
DEMO_CITY = {"id": "city-tpr-001", "organization_id": "org-tnta-001", "name": "Tiruppur", "state": "Tamil Nadu", "country": "India", "latitude": BASE_LAT, "longitude": BASE_LON}
DEMO_ZONE = {"id": "zone-tpr-01", "city_id": "city-tpr-001", "organization_id": "org-tnta-001", "name": "Traffic Zone 01 — Central Tiruppur"}

DEMO_USERS = [
    {"id": "user-admin-001",  "email": "admin@clearway.demo",    "display_name": "System Admin",       "role": "super_admin",       "password": "demo123"},
    {"id": "user-op-001",     "email": "operator@clearway.demo", "display_name": "Traffic Operator",   "role": "operator",          "password": "demo123"},
    {"id": "user-police-001", "email": "police@clearway.demo",   "display_name": "Officer Rajan Kumar","role": "traffic_police",    "password": "demo123", "assigned_junction_id": "J1"},
    {"id": "user-analyst-001","email": "analyst@clearway.demo",  "display_name": "Traffic Analyst",    "role": "analyst",           "password": "demo123"},
]


def generate_demo_vehicle_count(capacity: int, time_hour: int = None) -> int:
    if time_hour is None:
        time_hour = datetime.utcnow().hour
    if 8 <= time_hour <= 10 or 17 <= time_hour <= 19:
        factor = random.uniform(0.70, 0.95)
    elif 11 <= time_hour <= 16:
        factor = random.uniform(0.40, 0.65)
    elif 0 <= time_hour <= 5:
        factor = random.uniform(0.05, 0.15)
    else:
        factor = random.uniform(0.25, 0.45)
    return int(capacity * factor / 60)


def generate_intersections():
    from models.intersection import Intersection, Signal, Camera, Microphone, SignalPhase, CongestionLevel
    intersections = []
    directions = ["north", "south", "east", "west"]
    for seed in INTERSECTIONS_SEED:
        vehicle_count = generate_demo_vehicle_count(seed["road_capacity"])
        congestion_score = min(vehicle_count / (seed["road_capacity"] / 60), 1.0)
        if congestion_score < 0.3: level = CongestionLevel.LOW
        elif congestion_score < 0.6: level = CongestionLevel.MODERATE
        elif congestion_score < 0.8: level = CongestionLevel.HEAVY
        else: level = CongestionLevel.SEVERE

        signal = Signal(
            id=f"sig-{seed['id'].lower()}", intersection_id=seed["id"],
            current_phase=SignalPhase.NORTH_SOUTH_GREEN,
            phase_remaining_seconds=random.randint(5, 45),
            ns_green_duration=random.randint(30, 55),
            ew_green_duration=random.randint(25, 45),
        )
        cameras = [
            Camera(id=f"cam-{seed['id'].lower()}-{d}", intersection_id=seed["id"],
                   label=f"Camera {seed['label']}-{d[0].upper()}", direction=d, is_online=random.random() > 0.05)
            for d in directions[:4]
        ]
        microphones = [
            Microphone(id=f"mic-{seed['id'].lower()}-{d}", intersection_id=seed["id"],
                       label=f"Mic {seed['label']}-{d[0].upper()}", direction=d, ambient_db=random.uniform(62, 78))
            for d in ["north", "south"]
        ]
        intersection = Intersection(
            id=seed["id"], zone_id="zone-tpr-01", city_id="city-tpr-001",
            organization_id="org-tnta-001", name=seed["name"], label=seed["label"],
            latitude=BASE_LAT + seed["lat_offset"], longitude=BASE_LON + seed["lon_offset"],
            road_capacity=seed["road_capacity"], lane_count=seed["lane_count"],
            vehicle_count=vehicle_count, queue_length=int(vehicle_count * congestion_score * 0.6),
            average_speed_kmh=max(5.0, 60.0 * (1 - congestion_score)),
            congestion_level=level, congestion_score=round(congestion_score, 3),
            waiting_time_seconds=round(congestion_score * 120, 1),
            throughput_vph=int(seed["road_capacity"] * (1 - congestion_score * 0.5)),
            signal=signal, cameras=cameras, microphones=microphones,
            connected_intersection_ids=seed["connections"], data_source="DEMO",
        )
        intersections.append(intersection)
    return intersections


def generate_roads():
    from models.intersection import Road
    return [
        Road(id=f"road-{f.lower()}-{t.lower()}", from_intersection_id=f, to_intersection_id=t,
             name=n, distance_meters=float(d), speed_limit_kmh=50, lane_count=2, is_bidirectional=True)
        for f, t, n, d in ROADS_SEED
    ]


class DemoStore:
    def __init__(self):
        self.intersections = {}
        self.roads = []
        self.alerts = []
        self.siren_events = []
        self.police_dispatches = []
        self.optimization_runs = []
        self.simulation_results = []
        self.emergency_state = None
        self._initialized = False

    def initialize(self):
        if self._initialized:
            return
        for i in generate_intersections():
            self.intersections[i.id] = i
        self.roads = generate_roads()
        self._initialized = True

    def get_intersections(self):
        return list(self.intersections.values())

    def get_intersection(self, id: str):
        return self.intersections.get(id)

    def update_intersection(self, intersection):
        self.intersections[intersection.id] = intersection


demo_store = DemoStore()
