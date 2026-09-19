"""
ClearWay AI — AI Assistant Service (AIRA)
Uses Featherless AI (OpenAI-compatible API) for chat.
Falls back to rule-based answers when FEATHERLESS_API_KEY is not configured.
"""
import asyncio
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any

logger = logging.getLogger(__name__)

# ── Featherless AI settings ───────────────────────────────────────────────────
FEATHERLESS_BASE_URL = "https://api.featherless.ai/v1"
DEFAULT_FEATHERLESS_MODEL = "Qwen/Qwen2.5-7B-Instruct"   # fast, capable, non-gated

# ── Rule-based fallbacks (shown when API unavailable) ────────────────────────
FALLBACK_RESPONSES = {
    "congestion": (
        "Based on current traffic data, junction {junction} has a congestion score of {score:.0%} "
        "with {queue} vehicles in queue. The AI recommends {action}."
    ),
    "emergency": (
        "Emergency corridor status: {status}. "
        "The ambulance is currently at {location} with ETA {eta:.0f} seconds to destination."
    ),
    "siren": (
        "Siren detection at junction {junction}: confidence {confidence:.0%}, "
        "approach from {direction}. Officer status: {officer_status}."
    ),
    "quantum": (
        "The quantum optimizer used QUBO with {n_vars} binary variables across {n_junctions} junctions. "
        "QAOA (Qiskit Aer simulator) achieved {improvement:.1f}% cost reduction "
        "vs. classical fixed timing. Simulator: never real quantum hardware."
    ),
    "pollution": (
        "Estimated emissions at {junction}: CO₂={co2:.2f} kg/hr, NOx={nox:.2f} g/hr, "
        "PM2.5={pm25:.4f} g/hr. AQI estimate: {aqi} ({aqi_cat}). "
        "All values labeled ESTIMATED — not from real sensors."
    ),
    "default": (
        "AIRA is operating in rule-based mode (Featherless AI not reachable). "
        "Current network status: {n_intersections} intersections monitored, "
        "{active_alerts} active alerts, data mode: {data_mode}."
    ),
}

SYSTEM_PROMPT = """You are AIRA (AI Road Intelligence Assistant), the AI assistant for ClearWay AI — \
an intelligent urban traffic management platform for Tiruppur, Tamil Nadu, India.

YOUR RULES:
1. Answer ONLY from the context data provided in each prompt. Never invent traffic facts.
2. Always distinguish: LIVE DATA, DEMO DATA, SIMULATED DATA, AI PREDICTION, ESTIMATED EMISSIONS, \
QUANTUM SIMULATION, SIMULATED RADIO DISPATCH.
3. When discussing the quantum optimizer, always note it runs on a QUANTUM SIMULATOR (Qiskit Aer) — \
never real quantum hardware.
4. When discussing emissions, always label them ESTIMATED — not measured sensor data.
5. When discussing the siren/radio dispatch, always label it SIMULATED RADIO DISPATCH — \
not a real police radio integration.
6. Be concise, precise and professional — this is a government traffic operations system.
7. If asked about something outside the context, say so clearly.
8. Format key numbers clearly (e.g., "Junction J4: congestion 78%, queue 32 vehicles").
9. Keep responses under 200 words unless the user asks for a detailed summary.
"""


class AIAssistantService:
    """
    AIRA — AI Road Intelligence Assistant.
    Grounds every response in real backend state.
    Uses Featherless AI (OpenAI-compatible) when API key is set;
    falls back to rule-based responses otherwise.
    """

    def __init__(self, api_key: str = "", model: str = ""):
        self.api_key  = api_key.strip()
        self.model    = model.strip() or DEFAULT_FEATHERLESS_MODEL
        self.available = bool(self.api_key)
        self._history: List[Dict[str, str]] = []   # [{"role":…, "content":…}]
        self._openai_client = None

        if self.available:
            self._init_client()

    # ── Initialisation ────────────────────────────────────────────────────────

    def _init_client(self):
        try:
            from openai import AsyncOpenAI
            self._openai_client = AsyncOpenAI(
                api_key=self.api_key,
                base_url=FEATHERLESS_BASE_URL,
            )
            logger.info("AIRA: Featherless AI client initialised via OpenAI SDK (model=%s).", self.model)
        except ImportError:
            logger.info("AIRA: 'openai' package not installed — will use httpx for Featherless API (model=%s).", self.model)
            self._openai_client = None
        except Exception as exc:
            logger.warning("AIRA: Featherless AI init failed: %s — will use httpx.", exc)
            self._openai_client = None

    # ── Context builder ───────────────────────────────────────────────────────

    def _build_context(self, backend_state: Dict[str, Any]) -> str:
        """Serialise live backend state into a compact context string."""
        parts = [
            f"Current time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}",
            f"Data mode: {backend_state.get('data_mode', 'DEMO')}",
        ]

        # Intersections
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

        # Emergency
        emergency = backend_state.get("emergency", {})
        if isinstance(emergency, dict) and emergency.get("active"):
            parts.append(f"\nEMERGENCY CORRIDOR: {emergency.get('corridor_status', '?').upper()}")
            route = emergency.get("route") or {}
            ev    = emergency.get("emergency_vehicle") or {}
            if ev:
                parts.append(f"  Vehicle at: {ev.get('current_intersection_id', '?')}")
            if route:
                parts.append(
                    f"  Route: {' → '.join(route.get('route_intersection_ids', []))}"
                    f"  |  ETA: {route.get('eta_seconds', 0):.0f}s"
                    f"  |  Improvement vs classical: {route.get('improvement_pct', 0):.1f}% [SIMULATED]"
                )

        # Active alerts
        alerts = [a for a in backend_state.get("alerts", []) if isinstance(a, dict) and a.get("is_active")]
        if alerts:
            parts.append(f"\nACTIVE ALERTS ({len(alerts)}):")
            for a in alerts[:5]:
                parts.append(f"  [{a.get('severity', '?').upper()}] {a.get('title', '?')} — {a.get('junction_label', '?')}")

        # Latest optimization
        opt = backend_state.get("latest_optimization")
        if isinstance(opt, dict):
            parts.append(
                f"\nLATEST OPTIMIZATION [{opt.get('method', '?')}] [QUANTUM SIMULATION]:"
                f"\n  Cost: {opt.get('cost_before', 0):.1f} → {opt.get('cost_after', 0):.1f}"
                f"  |  Improvement: {opt.get('improvement_pct', 0):.1f}%"
                f"  |  Wait: {opt.get('avg_waiting_before', 0):.1f}s → {opt.get('avg_waiting_after', 0):.1f}s"
            )

        # Siren events
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

        # Pollution
        pollution = backend_state.get("pollution", [])
        if pollution:
            parts.append("\nESTIMATED EMISSIONS (top 3) [ESTIMATED — NOT MEASURED]:")
            for p in sorted(pollution, key=lambda x: x.get("co2_kg_per_hour", 0) if isinstance(x, dict) else 0, reverse=True)[:3]:
                if isinstance(p, dict):
                    parts.append(
                        f"  {p.get('junction_label', '?')}: "
                        f"CO₂={p.get('co2_kg_per_hour', 0):.2f}kg/hr, "
                        f"AQI={p.get('aqi_estimate', 0)} ({p.get('aqi_category', '?')})"
                    )

        return "\n".join(parts)

    # ── Main chat entry point ─────────────────────────────────────────────────

    async def chat(self, user_message: str, backend_state: Dict[str, Any]) -> Dict[str, Any]:
        context = self._build_context(backend_state)
        if self.available:
            return await self._featherless_chat(user_message, context, backend_state)
        return self._rule_based_response(user_message, backend_state)

    # ── Featherless AI call ───────────────────────────────────────────────────

    async def _featherless_chat(
        self, user_message: str, context: str, backend_state: Dict
    ) -> Dict[str, Any]:
        """Call Featherless AI (OpenAI-compatible) with grounded context."""
        try:
            grounded_user = (
                f"CURRENT SYSTEM STATE (use ONLY this data):\n{context}\n\n"
                f"USER QUESTION: {user_message}\n\n"
                f"Respond based strictly on the data above. Label all sources clearly."
            )

            # Build message list — keep last 10 turns for context
            messages = [{"role": "system", "content": SYSTEM_PROMPT}]
            messages += self._history[-10:]
            messages.append({"role": "user", "content": grounded_user})

            if self._openai_client:
                response = await self._openai_client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    max_tokens=400,
                    temperature=0.3,     # low temp = factual, consistent
                )
                reply = response.choices[0].message.content or ""
            else:
                import httpx
                payload = {
                    "model": self.model,
                    "messages": messages,
                    "max_tokens": 400,
                    "temperature": 0.3,
                }
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
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

            # Store trimmed history (without the injected context for brevity)
            self._history.append({"role": "user", "content": user_message})
            self._history.append({"role": "assistant", "content": reply})
            if len(self._history) > 20:
                self._history = self._history[-20:]

            return {
                "response": reply,
                "source": f"Featherless AI — {self.model}",
                "grounded": True,
                "model": self.model,
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as exc:
            logger.error("Featherless AI chat error: %s", exc)
            result = self._rule_based_response(user_message, backend_state)
            result["source"] += " (Featherless AI error — fell back to rules)"
            return result

    # ── Rule-based fallback ───────────────────────────────────────────────────

    def _rule_based_response(
        self, user_message: str, backend_state: Dict
    ) -> Dict[str, Any]:
        msg           = user_message.lower()
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
                    f"[SIMULATED] Emergency corridor ACTIVE — {em.get('corridor_status', '?').upper()}. "
                    f"Route: {' → '.join(route.get('route_intersection_ids', []))}. "
                    f"ETA: {route.get('eta_seconds', 0):.0f}s. "
                    f"Travel time improvement: {route.get('improvement_pct', 0):.1f}% vs classical."
                )
            else:
                response = "No active emergency corridor. Go to Emergency Corridor → Activate Corridor."

        elif any(kw in msg for kw in ["siren", "police", "dispatch", "sound"]):
            sirens = [s for s in backend_state.get("siren_events", []) if isinstance(s, dict) and s.get("is_active")]
            if sirens:
                s = sirens[0]
                response = (
                    f"[SIMULATED] Active siren at Junction {s.get('junction_label', '?')} — "
                    f"confidence {s.get('confidence', 0):.0%}, "
                    f"approaching from {s.get('approach_direction', '?')}. "
                    f"Officer status: {s.get('status', '?').replace('_', ' ').title()}. "
                    f"Note: SIMULATED RADIO DISPATCH."
                )
            else:
                response = "No active siren alerts. Visit Siren Detection to trigger a demo."

        elif any(kw in msg for kw in ["quantum", "qubo", "qaoa", "optim"]):
            opt = backend_state.get("latest_optimization")
            n   = len(intersections)
            if isinstance(opt, dict):
                response = (
                    f"[QUANTUM SIMULATION — Qiskit Aer, not real hardware] "
                    f"Latest {opt.get('method', 'quantum')} run: "
                    f"{opt.get('improvement_pct', 0):.1f}% cost reduction. "
                    f"QUBO vars: {n * 2}. Time: {opt.get('execution_time_ms', 0):.0f}ms."
                )
            else:
                response = (
                    f"Quantum optimizer ready for {n} junctions. "
                    f"Go to Quantum Optimizer → Run Optimization."
                )

        elif any(kw in msg for kw in ["pollution", "emission", "co2", "nox", "pm", "air", "aqi"]):
            pollution = backend_state.get("pollution", [])
            if pollution:
                wp = max(pollution, key=lambda p: p.get("co2_kg_per_hour", 0) if isinstance(p, dict) else 0, default={})
                if isinstance(wp, dict):
                    response = (
                        f"[ESTIMATED — not measured] Highest emissions at Junction {wp.get('junction_label', '?')}: "
                        f"CO₂={wp.get('co2_kg_per_hour', 0):.2f} kg/hr, "
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
            total_v  = sum(i.get("vehicle_count", 0) for i in intersections if isinstance(i, dict))
            response = (
                f"Network summary [{backend_state.get('data_mode', 'DEMO')}]: "
                f"{n} intersections active, {total_v} total vehicles, "
                f"average congestion {avg_cong:.0%}. "
                + (f"Worst: {worst.get('label', '?')} at {worst.get('congestion_score', 0):.0%}." if worst else "")
            )

        elif any(kw in msg for kw in ["hello", "hi", "help", "what can", "aira"]):
            response = (
                f"Hi! I'm AIRA — AI Road Intelligence Assistant for ClearWay AI. "
                f"I'm monitoring {len(intersections)} intersections in {backend_state.get('data_mode', 'DEMO')} mode. "
                f"Ask me about: congestion, emergency corridors, siren detection, "
                f"quantum optimization, pollution estimates, or network status."
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
            "source": "Rule-Based Fallback (Featherless AI not configured)",
            "grounded": True,
            "timestamp": datetime.utcnow().isoformat(),
        }


# ── Factory ───────────────────────────────────────────────────────────────────

def create_ai_assistant(settings) -> AIAssistantService:
    key = getattr(settings, "FEATHERLESS_API_KEY", "") or getattr(settings, "GEMINI_API_KEY", "")
    model = getattr(settings, "FEATHERLESS_MODEL", DEFAULT_FEATHERLESS_MODEL)
    return AIAssistantService(api_key=key, model=model)
