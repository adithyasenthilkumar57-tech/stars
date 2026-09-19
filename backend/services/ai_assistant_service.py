"""
ClearWay AI — AI Assistant Service (AIRA)
Primary:   Google Gemini (google-generativeai SDK)
Secondary: Featherless AI (OpenAI-compatible) via httpx
Fallback:  Rule-based deterministic responses
"""
import asyncio
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any

logger = logging.getLogger(__name__)

# Featherless AI settings
FEATHERLESS_BASE_URL = "https://api.featherless.ai/v1"
DEFAULT_FEATHERLESS_MODEL = "Qwen/Qwen2.5-7B-Instruct"

# Gemini settings
DEFAULT_GEMINI_MODEL = "gemini-2.0-flash"

FALLBACK_RESPONSES = {
    "default": (
        "AIRA is operating in rule-based mode (AI providers not reachable). "
        "Current network status: {n_intersections} intersections monitored, "
        "{active_alerts} active alerts, data mode: {data_mode}."
    ),
}

SYSTEM_PROMPT = """You are AIRA (AI Road Intelligence Assistant), the AI assistant for ClearWay AI — an intelligent urban traffic management platform for Tiruppur, Tamil Nadu, India.

YOUR RULES:
1. Answer ONLY from the context data provided in each prompt. Never invent traffic facts.
2. Always distinguish: LIVE DATA, DEMO DATA, SIMULATED DATA, AI PREDICTION, ESTIMATED EMISSIONS, QUANTUM SIMULATION, SIMULATED RADIO DISPATCH.
3. When discussing the quantum optimizer, always note it runs on a QUANTUM SIMULATOR (Qiskit Aer) — never real quantum hardware.
4. When discussing emissions, always label them ESTIMATED — not measured sensor data.
5. When discussing the siren/radio dispatch, always label it SIMULATED RADIO DISPATCH — not a real police radio integration.
6. Be concise, precise and professional — this is a government traffic operations system.
7. If asked about something outside the context, say so clearly.
8. Format key numbers clearly (e.g., "Junction J4: congestion 78%, queue 32 vehicles").
9. Keep responses under 200 words unless the user asks for a detailed summary.
"""


class AIAssistantService:
    """
    AIRA — AI Road Intelligence Assistant.
    Priority: Gemini -> Featherless AI -> Rule-based.
    """

    def __init__(self, gemini_api_key="", featherless_api_key="", featherless_model=""):
        self.gemini_api_key = gemini_api_key.strip()
        self.featherless_api_key = featherless_api_key.strip()
        self.featherless_model = featherless_model.strip() or DEFAULT_FEATHERLESS_MODEL
        self._history = []
        self._gemini_client = None

        if self.gemini_api_key:
            self._mode = "gemini"
            self._init_gemini()
        elif self.featherless_api_key:
            self._mode = "featherless"
        else:
            self._mode = "rules"

        logger.info("AIRA: mode=%s", self._mode)

    @property
    def available(self):
        return self._mode in ("gemini", "featherless")

    def _init_gemini(self):
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.gemini_api_key)
            self._gemini_client = genai.GenerativeModel(
                model_name=DEFAULT_GEMINI_MODEL,
                system_instruction=SYSTEM_PROMPT,
            )
            logger.info("AIRA: Gemini client initialised (model=%s).", DEFAULT_GEMINI_MODEL)
        except ImportError:
            logger.warning("AIRA: google-generativeai not installed — falling back to Featherless.")
            self._gemini_client = None
            self._mode = "featherless" if self.featherless_api_key else "rules"
        except Exception as exc:
            logger.warning("AIRA: Gemini init failed: %s", exc)
            self._gemini_client = None
            self._mode = "featherless" if self.featherless_api_key else "rules"

    def _build_context(self, backend_state):
        parts = [
            f"Current time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}",
            f"Data mode: {backend_state.get('data_mode', 'DEMO')}",
        ]
        intersections = backend_state.get("intersections", [])
        if intersections:
            parts.append(f"\nACTIVE INTERSECTIONS ({len(intersections)}):")
            for i in intersections[:6]:
                if isinstance(i, dict):
                    parts.append(
                        f"  {i.get('label', i.get('id', '?'))}: "
                        f"vehicles={i.get('vehicle_count', 0)}, "
                        f"queue={i.get('queue_length', 0)}, "
                        f"congestion={i.get('congestion_score', 0):.1%}, "
                        f"level={i.get('congestion_level', '?')}, "
                        f"wait={i.get('waiting_time_seconds', 0):.0f}s "
                        f"[{i.get('data_source', 'DEMO')}]"
                    )
        emergency = backend_state.get("emergency", {})
        if isinstance(emergency, dict) and emergency.get("active"):
            parts.append(f"\nEMERGENCY CORRIDOR: {emergency.get('corridor_status', '?').upper()}")
            route = emergency.get("route") or {}
            ev = emergency.get("emergency_vehicle") or {}
            if ev:
                parts.append(f"  Vehicle at: {ev.get('current_intersection_id', '?')}")
            if route:
                parts.append(
                    f"  Route: {' -> '.join(route.get('route_intersection_ids', []))}"
                    f"  |  ETA: {route.get('eta_seconds', 0):.0f}s"
                    f"  |  Improvement vs classical: {route.get('improvement_pct', 0):.1f}% [SIMULATED]"
                )
        alerts = [a for a in backend_state.get("alerts", []) if isinstance(a, dict) and a.get("is_active")]
        if alerts:
            parts.append(f"\nACTIVE ALERTS ({len(alerts)}):")
            for a in alerts[:5]:
                parts.append(f"  [{a.get('severity', '?').upper()}] {a.get('title', '?')} -- {a.get('junction_label', '?')}")
        opt = backend_state.get("latest_optimization")
        if isinstance(opt, dict):
            parts.append(
                f"\nLATEST OPTIMIZATION [{opt.get('method', '?')}] [QUANTUM SIMULATION]:"
                f"\n  Cost: {opt.get('cost_before', 0):.1f} -> {opt.get('cost_after', 0):.1f}"
                f"  |  Improvement: {opt.get('improvement_pct', 0):.1f}%"
                f"  |  Wait: {opt.get('avg_waiting_before', 0):.1f}s -> {opt.get('avg_waiting_after', 0):.1f}s"
            )
        sirens = [s for s in backend_state.get("siren_events", []) if isinstance(s, dict) and s.get("is_active")]
        if sirens:
            parts.append(f"\nACTIVE SIREN ALERTS ({len(sirens)}) [SIMULATED RADIO DISPATCH]:")
            for s in sirens[:3]:
                parts.append(
                    f"  Junction {s.get('junction_label', '?')}: "
                    f"confidence={s.get('confidence', 0):.0%}, "
                    f"direction={s.get('approach_direction', '?')}, "
                    f"status={s.get('status', '?')}"
                )
        pollution = backend_state.get("pollution", [])
        if pollution:
            parts.append("\nESTIMATED EMISSIONS (top 3) [ESTIMATED -- NOT MEASURED]:")
            for p in sorted(pollution, key=lambda x: x.get("co2_kg_per_hour", 0) if isinstance(x, dict) else 0, reverse=True)[:3]:
                if isinstance(p, dict):
                    parts.append(
                        f"  {p.get('junction_label', '?')}: "
                        f"CO2={p.get('co2_kg_per_hour', 0):.2f}kg/hr, "
                        f"AQI={p.get('aqi_estimate', 0)} ({p.get('aqi_category', '?')})"
                    )
        return "\n".join(parts)

    async def chat(self, user_message, backend_state):
        context = self._build_context(backend_state)
        if self._mode == "gemini" and self._gemini_client:
            return await self._gemini_chat(user_message, context, backend_state)
        if self._mode == "featherless" and self.featherless_api_key:
            return await self._featherless_chat(user_message, context, backend_state)
        return self._rule_based_response(user_message, backend_state)

    async def _gemini_chat(self, user_message, context, backend_state):
        try:
            grounded_user = (
                f"CURRENT SYSTEM STATE (use ONLY this data):\n{context}\n\n"
                f"USER QUESTION: {user_message}\n\n"
                f"Respond based strictly on the data above. Label all sources clearly."
            )
            history = []
            for msg in self._history[-20:]:
                role = "user" if msg["role"] == "user" else "model"
                history.append({"role": role, "parts": [msg["content"]]})

            def _call():
                chat_session = self._gemini_client.start_chat(history=history)
                return chat_session.send_message(grounded_user)

            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, _call)
            reply = response.text or ""

            self._history.append({"role": "user", "content": user_message})
            self._history.append({"role": "assistant", "content": reply})
            if len(self._history) > 20:
                self._history = self._history[-20:]

            return {
                "response": reply,
                "source": f"Google Gemini -- {DEFAULT_GEMINI_MODEL}",
                "grounded": True,
                "model": DEFAULT_GEMINI_MODEL,
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as exc:
            logger.error("Gemini chat error: %s -- trying Featherless fallback.", exc)
            if self.featherless_api_key:
                try:
                    result = await self._featherless_chat(user_message, context, backend_state)
                    result["source"] += " (Gemini error -- fell back to Featherless)"
                    return result
                except Exception as exc2:
                    logger.error("Featherless fallback also failed: %s", exc2)
            result = self._rule_based_response(user_message, backend_state)
            result["source"] += " (Gemini error -- fell back to rules)"
            return result

    async def _featherless_chat(self, user_message, context, backend_state):
        try:
            grounded_user = (
                f"CURRENT SYSTEM STATE (use ONLY this data):\n{context}\n\n"
                f"USER QUESTION: {user_message}\n\n"
                f"Respond based strictly on the data above. Label all sources clearly."
            )
            messages = [{"role": "system", "content": SYSTEM_PROMPT}]
            messages += self._history[-10:]
            messages.append({"role": "user", "content": grounded_user})

            import httpx
            payload = {
                "model": self.featherless_model,
                "messages": messages,
                "max_tokens": 400,
                "temperature": 0.3,
            }
            headers = {
                "Authorization": f"Bearer {self.featherless_api_key}",
                "Content-Type": "application/json",
            }
            async with httpx.AsyncClient(timeout=30.0) as client:
                res = await client.post(
                    f"{FEATHERLESS_BASE_URL}/chat/completions",
                    json=payload,
                    headers=headers,
                )
                res.raise_for_status()
                data = res.json()
                reply = data["choices"][0]["message"]["content"] or ""

            self._history.append({"role": "user", "content": user_message})
            self._history.append({"role": "assistant", "content": reply})
            if len(self._history) > 20:
                self._history = self._history[-20:]

            return {
                "response": reply,
                "source": f"Featherless AI -- {self.featherless_model}",
                "grounded": True,
                "model": self.featherless_model,
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as exc:
            logger.error("Featherless AI chat error: %s", exc)
            result = self._rule_based_response(user_message, backend_state)
            result["source"] += " (Featherless AI error -- fell back to rules)"
            return result

    def _rule_based_response(self, user_message, backend_state):
        msg = user_message.lower()
        intersections = backend_state.get("intersections", [])
        worst = (
            max(intersections, key=lambda i: i.get("congestion_score", 0) if isinstance(i, dict) else 0, default=None)
            if intersections else None
        )
        if any(kw in msg for kw in ["congestion", "congested", "traffic", "queue", "jam", "worst"]):
            if worst and isinstance(worst, dict):
                response = (
                    f"[DEMO DATA] Junction {worst.get('label', '?')} has the highest congestion at "
                    f"{worst.get('congestion_score', 0):.0%} with {worst.get('queue_length', 0)} vehicles queued. "
                    f"Average wait: {worst.get('waiting_time_seconds', 0):.0f}s. "
                    f"[Source: {worst.get('data_source', 'DEMO')}]"
                )
            else:
                response = "No intersection data available. Enable Demo Data or connect live sensors."
        elif any(kw in msg for kw in ["emergency", "ambulance", "corridor"]):
            em = backend_state.get("emergency", {})
            if em and em.get("active"):
                route = em.get("route") or {}
                response = (
                    f"[SIMULATED] Emergency corridor ACTIVE -- {em.get('corridor_status', '?').upper()}. "
                    f"Route: {' -> '.join(route.get('route_intersection_ids', []))}. "
                    f"ETA: {route.get('eta_seconds', 0):.0f}s. "
                    f"Travel time improvement: {route.get('improvement_pct', 0):.1f}% vs classical."
                )
            else:
                response = "No active emergency corridor. Go to Emergency Corridor -> Activate Corridor."
        elif any(kw in msg for kw in ["siren", "police", "dispatch", "sound"]):
            sirens = [s for s in backend_state.get("siren_events", []) if isinstance(s, dict) and s.get("is_active")]
            if sirens:
                s = sirens[0]
                response = (
                    f"[SIMULATED] Active siren at Junction {s.get('junction_label', '?')} -- "
                    f"confidence {s.get('confidence', 0):.0%}, "
                    f"approaching from {s.get('approach_direction', '?')}. "
                    f"Officer status: {s.get('status', '?').replace('_', ' ').title()}. "
                    f"Note: SIMULATED RADIO DISPATCH."
                )
            else:
                response = "No active siren alerts. Visit Siren Detection to trigger a demo."
        elif any(kw in msg for kw in ["quantum", "qubo", "qaoa", "optim"]):
            opt = backend_state.get("latest_optimization")
            n = len(intersections)
            if isinstance(opt, dict):
                response = (
                    f"[QUANTUM SIMULATION -- Qiskit Aer, not real hardware] "
                    f"Latest {opt.get('method', 'quantum')} run: "
                    f"{opt.get('improvement_pct', 0):.1f}% cost reduction. "
                    f"QUBO vars: {n * 2}. Time: {opt.get('execution_time_ms', 0):.0f}ms."
                )
            else:
                response = f"Quantum optimizer ready for {n} junctions. Go to Quantum Optimizer -> Run Optimization."
        elif any(kw in msg for kw in ["pollution", "emission", "co2", "nox", "pm", "air", "aqi"]):
            pollution = backend_state.get("pollution", [])
            if pollution:
                wp = max(pollution, key=lambda p: p.get("co2_kg_per_hour", 0) if isinstance(p, dict) else 0, default={})
                if isinstance(wp, dict):
                    response = (
                        f"[ESTIMATED -- not measured] Highest emissions at Junction {wp.get('junction_label', '?')}: "
                        f"CO2={wp.get('co2_kg_per_hour', 0):.2f} kg/hr, "
                        f"NOx={wp.get('nox_g_per_hour', 0):.2f} g/hr, "
                        f"AQI={wp.get('aqi_estimate', 0)} ({wp.get('aqi_category', '?')})."
                    )
                else:
                    response = "Pollution data unavailable."
            else:
                response = "Enable Demo Data to see pollution estimates."
        elif any(kw in msg for kw in ["summary", "summarize", "status", "overview", "network"]):
            n = len(intersections)
            avg_cong = sum(i.get("congestion_score", 0) for i in intersections if isinstance(i, dict)) / max(n, 1)
            total_v = sum(i.get("vehicle_count", 0) for i in intersections if isinstance(i, dict))
            response = (
                f"Network summary [{backend_state.get('data_mode', 'DEMO')}]: "
                f"{n} intersections active, {total_v} total vehicles, "
                f"average congestion {avg_cong:.0%}. "
                + (f"Worst: {worst.get('label', '?')} at {worst.get('congestion_score', 0):.0%}." if worst else "")
            )
        elif any(kw in msg for kw in ["hello", "hi", "help", "what can", "aira"]):
            response = (
                f"Hi! I am AIRA -- AI Road Intelligence Assistant for ClearWay AI. "
                f"I am monitoring {len(intersections)} intersections in {backend_state.get('data_mode', 'DEMO')} mode. "
                f"Ask me about: congestion, emergency corridors, siren detection, quantum optimization, pollution estimates, or network status."
            )
        else:
            response = (
                f"I can answer questions about: traffic congestion, emergency corridors, "
                f"siren detection, quantum optimization, emission estimates, and predictions. "
                f"Network: {len(intersections)} junctions, mode: {backend_state.get('data_mode', 'DEMO')}. "
                f"Try: 'Which junction has the worst queue?' or 'Summarize the network status.'"
            )
        return {
            "response": response,
            "source": "Rule-Based Fallback (AI providers not configured)",
            "grounded": True,
            "timestamp": datetime.utcnow().isoformat(),
        }


def create_ai_assistant(settings):
    """Create the AI assistant, preferring Gemini over Featherless AI."""
    return AIAssistantService(
        gemini_api_key=getattr(settings, "GEMINI_API_KEY", ""),
        featherless_api_key=getattr(settings, "FEATHERLESS_API_KEY", ""),
        featherless_model=getattr(settings, "FEATHERLESS_MODEL", DEFAULT_FEATHERLESS_MODEL),
    )
