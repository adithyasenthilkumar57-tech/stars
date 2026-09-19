"""
ClearWay AI — Report Service
Generates PDF and CSV traffic reports.
"""
import csv
import io
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

logger = logging.getLogger(__name__)


class ReportService:
    """Generates PDF and CSV reports for traffic, emergency, and optimization data."""

    def _generate_daily_data(self, intersections: List, alerts: List) -> Dict:
        total_vehicles = sum(getattr(i, "vehicle_count", 0) for i in intersections)
        avg_wait = sum(getattr(i, "waiting_time_seconds", 0) for i in intersections) / max(len(intersections), 1)
        avg_congestion = sum(getattr(i, "congestion_score", 0) for i in intersections) / max(len(intersections), 1)
        worst = max(intersections, key=lambda i: getattr(i, "congestion_score", 0), default=None)

        return {
            "total_vehicles_detected": total_vehicles,
            "average_waiting_time_seconds": round(avg_wait, 1),
            "average_congestion_score": round(avg_congestion, 3),
            "peak_congestion_junction": getattr(worst, "label", "N/A") if worst else "N/A",
            "total_active_alerts": len([a for a in alerts if getattr(a, "is_active", False)]),
            "report_date": datetime.utcnow().strftime("%Y-%m-%d"),
            "data_source": "DEMO",
            "label": "ESTIMATED / DEMO DATA",
        }

    def generate_csv(self, intersections: List, alerts: List) -> bytes:
        """Generate CSV report content."""
        output = io.StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow(["ClearWay AI — Traffic Report"])
        writer.writerow(["Generated:", datetime.utcnow().isoformat()])
        writer.writerow(["Data Source:", "DEMO / SIMULATED / ESTIMATED"])
        writer.writerow([])

        # Intersections
        writer.writerow(["Junction", "Vehicles", "Queue", "Congestion%", "Wait(s)", "Status", "Data Source"])
        for inter in intersections:
            writer.writerow([
                getattr(inter, "label", "?"),
                getattr(inter, "vehicle_count", 0),
                getattr(inter, "queue_length", 0),
                f"{getattr(inter, 'congestion_score', 0):.0%}",
                f"{getattr(inter, 'waiting_time_seconds', 0):.1f}",
                getattr(inter, "congestion_level", "?"),
                getattr(inter, "data_source", "DEMO"),
            ])

        writer.writerow([])
        writer.writerow(["Active Alerts"])
        writer.writerow(["Time", "Severity", "Title", "Junction", "Status"])
        for alert in alerts[:20]:
            writer.writerow([
                getattr(alert, "created_at", "?"),
                getattr(alert, "severity", "?"),
                getattr(alert, "title", "?"),
                getattr(alert, "junction_label", "?"),
                "Active" if getattr(alert, "is_active", False) else "Resolved",
            ])

        return output.getvalue().encode("utf-8")

    def generate_pdf_bytes(self, intersections: List, alerts: List, report_type: str = "daily") -> bytes:
        """Generate PDF using fpdf2."""
        try:
            from fpdf import FPDF

            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Helvetica", "B", 18)
            pdf.cell(0, 12, "ClearWay AI — Traffic Report", ln=True, align="C")
            pdf.set_font("Helvetica", size=10)
            pdf.cell(0, 8, f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}", ln=True, align="C")
            pdf.cell(0, 6, "DATA SOURCE: DEMO / SIMULATED / ESTIMATED — Not real sensor data", ln=True, align="C")
            pdf.ln(8)

            # Summary
            pdf.set_font("Helvetica", "B", 13)
            pdf.cell(0, 9, "Network Summary", ln=True)
            pdf.set_font("Helvetica", size=10)
            data = self._generate_daily_data(intersections, alerts)
            for k, v in data.items():
                if k not in ("label", "data_source"):
                    pdf.cell(0, 7, f"  {k.replace('_', ' ').title()}: {v}", ln=True)

            pdf.ln(6)

            # Intersection table
            pdf.set_font("Helvetica", "B", 12)
            pdf.cell(0, 9, "Intersection Status", ln=True)
            pdf.set_font("Helvetica", size=9)
            col_widths = [20, 25, 20, 30, 25, 40, 30]
            headers = ["Label", "Vehicles", "Queue", "Congestion", "Wait(s)", "Level", "Source"]
            for i, (h, w) in enumerate(zip(headers, col_widths)):
                pdf.cell(w, 7, h, border=1)
            pdf.ln()
            for inter in intersections:
                row = [
                    getattr(inter, "label", "?"),
                    str(getattr(inter, "vehicle_count", 0)),
                    str(getattr(inter, "queue_length", 0)),
                    f"{getattr(inter, 'congestion_score', 0):.0%}",
                    f"{getattr(inter, 'waiting_time_seconds', 0):.1f}",
                    str(getattr(inter, "congestion_level", "?")).upper(),
                    getattr(inter, "data_source", "DEMO"),
                ]
                for val, w in zip(row, col_widths):
                    pdf.cell(w, 7, str(val)[:18], border=1)
                pdf.ln()

            pdf.ln(6)
            pdf.set_font("Helvetica", "I", 9)
            pdf.cell(0, 6, "* All emission values are ESTIMATED. Quantum results use QUANTUM SIMULATOR (not real hardware).", ln=True)

            return bytes(pdf.output())

        except ImportError:
            logger.warning("fpdf2 not available. Returning CSV as fallback.")
            return self.generate_csv(intersections, alerts)
        except Exception as e:
            logger.error(f"PDF generation error: {e}")
            return self.generate_csv(intersections, alerts)


# Singleton
report_service = ReportService()
