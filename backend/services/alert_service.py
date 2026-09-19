"""
ClearWay AI — Alert Service
Central alert/notification bus.
"""
import uuid
from datetime import datetime, timedelta
from typing import List, Optional, Dict
from models.alert import Alert, AlertType, AlertSeverity, ALERT_SEVERITY_MAP
from models.intersection import Intersection, CongestionLevel


class AlertService:
    def __init__(self):
        self._alerts: List[Alert] = []
        self._max_alerts = 200

    def create_alert(
        self,
        alert_type: AlertType,
        title: str,
        message: str,
        intersection: Optional[Intersection] = None,
        related_event_id: Optional[str] = None,
        ai_explanation: Optional[str] = None,
        recommended_action: Optional[str] = None,
        auto_resolve_minutes: Optional[int] = None,
        data_source: str = "DEMO",
    ) -> Alert:
        severity = ALERT_SEVERITY_MAP.get(alert_type, AlertSeverity.INFO)
        alert = Alert(
            type=alert_type,
            severity=severity,
            title=title,
            message=message,
            intersection_id=intersection.id if intersection else None,
            junction_label=intersection.label if intersection else None,
            related_event_id=related_event_id,
            ai_explanation=ai_explanation,
            recommended_action=recommended_action,
            auto_resolve_at=(
                datetime.utcnow() + timedelta(minutes=auto_resolve_minutes)
                if auto_resolve_minutes else None
            ),
            data_source=data_source,
        )
        self._alerts.insert(0, alert)
        if len(self._alerts) > self._max_alerts:
            self._alerts = self._alerts[:self._max_alerts]
        return alert

    def acknowledge(self, alert_id: str, user_id: str) -> Optional[Alert]:
        for alert in self._alerts:
            if alert.id == alert_id:
                alert.acknowledged = True
                alert.acknowledged_by = user_id
                alert.acknowledged_at = datetime.utcnow()
                return alert
        return None

    def resolve(self, alert_id: str):
        for alert in self._alerts:
            if alert.id == alert_id:
                alert.is_active = False
                return alert
        return None

    def get_all(self, active_only: bool = False) -> List[Alert]:
        if active_only:
            return [a for a in self._alerts if a.is_active]
        return self._alerts

    def get_by_type(self, alert_type: AlertType) -> List[Alert]:
        return [a for a in self._alerts if a.type == alert_type]

    def get_active_count(self) -> int:
        return sum(1 for a in self._alerts if a.is_active)

    def auto_resolve_expired(self):
        now = datetime.utcnow()
        for alert in self._alerts:
            if alert.auto_resolve_at and alert.is_active and now > alert.auto_resolve_at:
                alert.is_active = False

    def check_and_create_traffic_alerts(self, intersections: List[Intersection]) -> List[Alert]:
        """Auto-generate alerts based on current intersection state."""
        new_alerts = []
        for inter in intersections:
            if inter.congestion_level == CongestionLevel.SEVERE:
                existing = any(
                    a.intersection_id == inter.id and a.type == AlertType.SEVERE_CONGESTION and a.is_active
                    for a in self._alerts
                )
                if not existing:
                    alert = self.create_alert(
                        AlertType.SEVERE_CONGESTION,
                        f"Severe Congestion — {inter.label}",
                        f"Junction {inter.label} ({inter.name}) is at {inter.congestion_score:.0%} capacity. "
                        f"Queue: {inter.queue_length} vehicles, wait: {inter.waiting_time_seconds:.0f}s.",
                        intersection=inter,
                        ai_explanation=(
                            f"AI detected sustained high vehicle density at {inter.label}. "
                            f"Contributing factors: queue growth rate, high vehicle count, signal phase mismatch."
                        ),
                        recommended_action="Run AI optimization to redistribute signal timing.",
                        auto_resolve_minutes=30,
                        data_source=inter.data_source,
                    )
                    new_alerts.append(alert)
        return new_alerts


# Singleton
alert_service = AlertService()
