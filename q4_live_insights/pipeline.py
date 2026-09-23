"""
Q4 - Live Insights: Enterprise Real-Time Call Analysis & LangGraph Voice Server
==============================================================================
Streams audio / text -> LangGraph StateGraph Voice Agent -> Gemini/Groq Signal Extraction
-> Nudge Filter -> WebSocket Broadcast to Unified Dashboard & HITL Supervisor Hub.

Endpoints:
  GET  /                        Unified Web Dashboard
  GET  /health                  System health & active call counter
  GET  /api/leads               CRM saved leads and callbacks
  GET  /api/telemetry           Real-time P50/P95 latencies and turn counts
  GET  /api/hitl/pending        Pending Human-in-the-Loop escalation requests
  POST /api/hitl/action         Supervisor approval / override / takeover
  GET  /demo                    Runs pre-scripted multi-turn simulation with live nudges
  WS   /ws/dashboard            Dashboard live feed (nudges, transcripts, HITL alerts)
  WS   /ws/voice_agent/{call_id} Interactive web voice/text agent (Aria, Maya, Dewi)
  WS   /ws/audio/{call_id}      Raw PCM audio ingestion to Deepgram ASR
"""

import asyncio
import json
import logging
import os
import sys
import time
import uuid
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx
import uvicorn
import websockets
from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

# ── Ensure paths to core, q1, and q2 are registered ─────────────────────────
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(ROOT_DIR / "q1_voice_agent"))
sys.path.insert(0, str(ROOT_DIR / "q2_knowledge_base"))

from langchain_core.messages import HumanMessage
from core.config import settings
from core.guardrails import InputGuardrail, OutputGuardrail
from core.hitl_manager import hitl_manager
from core.langgraph_agent import agent_app
from core.middlewares import audit_trail, telemetry

logger = logging.getLogger("pipeline")
logging.basicConfig(level=logging.INFO)

# ── Fast API Initialization ───────────────────────────────────────────────────
app = FastAPI(title="ShieldCare Live Insights & Voice Pipeline", version="2.0.0")
dashboard_path = Path(__file__).parent / "dashboard"

# Active sessions and connections
session_store: Dict[str, Any] = {}
dashboard_connections: List[WebSocket] = []

# Forward HITL manager events to dashboard WebSockets
def on_hitl_event(event_dict: Dict[str, Any]):
    asyncio.create_task(broadcast_to_dashboard(event_dict))

hitl_manager.subscribe(on_hitl_event)

# ── Signal Definitions & Thresholds ──────────────────────────────────────────
SIGNAL_TYPES = {
    "missed_cross_sell": {
        "cooldown_s": 60,
        "confidence_threshold": 0.70,
        "priority": "medium",
        "expiry_s": 90,
    },
    "compliance_gap": {
        "cooldown_s": 180,
        "confidence_threshold": 0.75,
        "priority": "high",
        "expiry_s": 120,
    },
    "rising_frustration": {
        "cooldown_s": 45,
        "confidence_threshold": 0.70,
        "min_consecutive_windows": 1,
        "priority": "high",
        "expiry_s": 60,
    },
    "payment_difficulty": {
        "cooldown_s": 60,
        "confidence_threshold": 0.70,
        "priority": "medium",
        "expiry_s": 90,
    },
    "out_of_scope": {
        "cooldown_s": 30,
        "confidence_threshold": 0.70,
        "priority": "low",
        "expiry_s": 60,
    },
    "buying_signal": {
        "cooldown_s": 90,
        "confidence_threshold": 0.70,
        "priority": "high",
        "expiry_s": 120,
    },
}

SIGNAL_EXTRACTION_PROMPT = """You are a real-time call analysis engine. Analyze the following call transcript window and detect any of these signals:
1. missed_cross_sell: Customer mentions another product, family member, vehicle, loan, or second property
2. compliance_gap: Required disclosures (waiting periods, exclusions, co-payment) have NOT been mentioned yet
3. rising_frustration: Customer expresses dissatisfaction, anger, impatience, or frustration
4. payment_difficulty: Customer mentions affordability concerns, budget constraints, or inability to pay
5. out_of_scope: Customer asks about products/services outside the agent's scope
6. buying_signal: Customer expresses interest, asks about next steps, enrollment, or pricing

Return ONLY valid JSON:
{
  "signals": [
    {
      "type": "signal_type_here",
      "confidence": 0.85,
      "evidence": "brief quote from transcript",
      "nudge": "short actionable recommendation for the agent (max 12 words)"
    }
  ]
}
If no signals detected, return: {"signals": []}

TRANSCRIPT WINDOW:
"""

# ── Call Session State ────────────────────────────────────────────────────────
class CallSession:
    def __init__(self, call_id: str, agent_name: str = "Aria"):
        self.call_id = call_id
        self.agent_name = agent_name
        self.start_time = time.time()
        self.transcript_buffer: List[Dict[str, Any]] = []
        self.signal_cooldowns: Dict[str, float] = defaultdict(float)
        self.last_extraction_time = 0.0
        self.extraction_interval_s = 3.0
        self.emitted_signals: List[Dict[str, Any]] = []

    def get_transcript_window(self, seconds: int = 30) -> str:
        cutoff = time.time() - seconds
        recent = [t for t in self.transcript_buffer if t["ts"] >= cutoff]
        lines = []
        for t in recent:
            speaker = "AGENT" if t.get("speaker") == "0" else "CUSTOMER"
            lines.append(f"{speaker}: {t['text']}")
        return "\n".join(lines) if lines else "[No transcript yet]"

    def can_emit(self, signal_type: str) -> bool:
        cooldown = SIGNAL_TYPES.get(signal_type, {}).get("cooldown_s", 60)
        return time.time() - self.signal_cooldowns[signal_type] >= cooldown

    def record_emission(self, signal_type: str):
        self.signal_cooldowns[signal_type] = time.time()


# ── Broadcast Helper ──────────────────────────────────────────────────────────
async def broadcast_to_dashboard(payload: Dict[str, Any]):
    dead = []
    text = json.dumps(payload)
    for ws in dashboard_connections:
        try:
            await ws.send_text(text)
        except Exception:
            dead.append(ws)
    for ws in dead:
        if ws in dashboard_connections:
            dashboard_connections.remove(ws)


# ── REST Endpoints ────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    html_file = dashboard_path / "index.html"
    return HTMLResponse(content=html_file.read_text(encoding="utf-8"), status_code=200)


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "active_calls": len(session_store),
        "llm_provider": settings.LLM_PROVIDER,
        "gemini_active": bool(settings.GEMINI_API_KEY),
        "groq_active": bool(settings.GROQ_API_KEY),
    }


@app.get("/api/leads")
async def get_leads():
    leads, callbacks = [], []
    if settings.CRM_LEADS_FILE.exists():
        try:
            leads = json.loads(settings.CRM_LEADS_FILE.read_text(encoding="utf-8"))
        except Exception:
            leads = []
    if settings.CRM_CALLBACKS_FILE.exists():
        try:
            callbacks = json.loads(settings.CRM_CALLBACKS_FILE.read_text(encoding="utf-8"))
        except Exception:
            callbacks = []
    return {"leads": leads, "callbacks": callbacks, "total": len(leads)}


@app.get("/api/telemetry")
async def get_telemetry():
    """Return rolling latency P50/P95 stats and component timings."""
    return telemetry.get_stats()


@app.get("/api/hitl/pending")
async def get_pending_hitl():
    """Returns all queued Human-in-the-Loop escalation requests."""
    return {"pending": hitl_manager.get_pending()}


@app.post("/api/hitl/action")
async def resolve_hitl(req: Request):
    """Supervisor approval, manual override, or call transfer."""
    data = await req.json()
    req_id = data.get("request_id")
    action = data.get("action", "approve")  # "approve", "override", "transfer"
    resolution_text = data.get("resolution_text")

    result = hitl_manager.resolve(request_id=req_id, action=action, resolution_text=resolution_text)
    if not result:
        raise HTTPException(status_code=404, detail="HITL request not found")
    return {"status": "resolved", "item": result.to_dict()}


# ── Dashboard WebSocket Feed ──────────────────────────────────────────────────

@app.websocket("/ws/dashboard")
async def dashboard_ws(websocket: WebSocket):
    await websocket.accept()
    dashboard_connections.append(websocket)
    try:
        # Send initial pending HITL queue upon connect
        pending = hitl_manager.get_pending()
        if pending:
            await websocket.send_text(json.dumps({"event": "initial_hitl", "data": pending}))

        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        if websocket in dashboard_connections:
            dashboard_connections.remove(websocket)


# ── Interactive LangGraph Voice Agent WebSocket ───────────────────────────────

AGENT_PROFILES = {
    "aria": {"name": "Aria", "emoji": "🤖", "sector": "Health (EN)"},
    "maya": {"name": "Maya", "emoji": "🌺", "sector": "Life / Taglish (PH)"},
    "dewi": {"name": "Dewi", "emoji": "🌸", "sector": "Multifinance (ID)"},
}

@app.websocket("/ws/voice_agent/{call_id}")
async def voice_agent_ws(websocket: WebSocket, call_id: str, agent: str = "aria"):
    await websocket.accept()

    agent_key = agent.lower()
    profile = AGENT_PROFILES.get(agent_key, AGENT_PROFILES["aria"])
    session = CallSession(call_id=call_id, agent_name=profile["name"])
    session_store[call_id] = session

    thread_id = f"thread_{call_id}"
    graph_config = {"configurable": {"thread_id": thread_id}}

    await broadcast_to_dashboard({
        "type": "call_started",
        "call_id": call_id,
        "agent": profile["name"],
        "timestamp": datetime.utcnow().isoformat(),
    })

    # Opening Turn
    openings = {
        "aria": "Hello! I am Aria from ShieldCare Insurance, representing our Arogya Shield Plus plan. Do you have 3 to 4 minutes to discuss your health coverage?",
        "maya": "Magandang araw po! I'm Maya from SunLife Assurance Philippines. May I have 3 to 4 minutes of your time to talk about SunShield Life Plus po?",
        "dewi": "Halo selamat siang Bapak/Ibu, saya Dewi dari ArthaPrime Multifinance. Bisa minta waktunya sebentar untuk simulasi pembiayaan?",
    }
    opening_text = openings.get(agent_key, openings["aria"])

    await websocket.send_text(json.dumps({
        "type": "agent",
        "text": opening_text,
        "agent_name": profile["name"],
        "emoji": profile["emoji"],
        "latency_ms": 120,
        "grounding_score": 1.0,
    }))

    session.transcript_buffer.append({"text": opening_text, "speaker": "0", "ts": time.time()})
    await broadcast_to_dashboard({
        "type": "transcript",
        "call_id": call_id,
        "speaker": "AGENT",
        "text": opening_text,
        "timestamp": datetime.utcnow().isoformat(),
    })

    try:
        while True:
            raw = await websocket.receive_text()
            data = json.loads(raw)
            if data.get("type") == "end":
                break

            user_text = data.get("text", "").strip()
            if not user_text:
                continue

            # Record customer turn
            now = time.time()
            session.transcript_buffer.append({"text": user_text, "speaker": "1", "ts": now})
            await broadcast_to_dashboard({
                "type": "transcript",
                "call_id": call_id,
                "speaker": "CUSTOMER",
                "text": user_text,
                "timestamp": datetime.utcnow().isoformat(),
            })

            # Execute LangGraph State Machine
            turn_start = time.time()
            graph_input = {
                "messages": [HumanMessage(content=user_text)],
                "agent_name": agent_key,
                "call_id": call_id,
                "start_time": turn_start,
            }

            result = agent_app.invoke(graph_input, config=graph_config)
            ai_message = result["messages"][-1].content
            latency = result.get("turn_latency_ms", (time.time() - turn_start) * 1000)
            grounding = result.get("grounding_score", 1.0)
            hitl_status = result.get("hitl_status", "none")

            # Check for HITL escalation
            if hitl_status == "escalated":
                await broadcast_to_dashboard({
                    "type": "hitl_alert",
                    "call_id": call_id,
                    "agent": profile["name"],
                    "reason": "Caller requested human supervisor",
                })

            # Send agent reply to browser client
            await websocket.send_text(json.dumps({
                "type": "agent",
                "text": ai_message,
                "agent_name": profile["name"],
                "emoji": profile["emoji"],
                "latency_ms": round(latency),
                "grounding_score": grounding,
                "hitl_status": hitl_status,
            }))

            session.transcript_buffer.append({"text": ai_message, "speaker": "0", "ts": time.time()})
            await broadcast_to_dashboard({
                "type": "transcript",
                "call_id": call_id,
                "speaker": "AGENT",
                "text": ai_message,
                "timestamp": datetime.utcnow().isoformat(),
            })

            # Trigger live signal extraction
            if now - session.last_extraction_time >= session.extraction_interval_s:
                session.last_extraction_time = now
                asyncio.create_task(extract_and_emit_signals(session, now))

    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"[WS Voice Agent Error]: {e}")
    finally:
        if call_id in session_store:
            del session_store[call_id]
        await broadcast_to_dashboard({
            "type": "call_ended",
            "call_id": call_id,
            "timestamp": datetime.utcnow().isoformat(),
        })


# ── Live Signal Extraction (Gemini / Groq) ───────────────────────────────────

async def extract_and_emit_signals(session: CallSession, asr_received_ts: float):
    """Extract actionable signals from sliding conversation window."""
    window = session.get_transcript_window(seconds=30)
    if window == "[No transcript yet]" or len(window) < 40:
        return

    llm_start_ts = time.time()
    extracted_signals = []

    # Try Gemini if key is provided, else fallback to Groq
    if settings.GEMINI_API_KEY:
        try:
            from google import genai
            client = genai.Client(api_key=settings.GEMINI_API_KEY)
            resp = client.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=SIGNAL_EXTRACTION_PROMPT + window,
                config={"response_mime_type": "application/json"},
            )
            data = json.loads(resp.text)
            extracted_signals = data.get("signals", [])
        except Exception:
            extracted_signals = []

    if not extracted_signals and settings.GROQ_API_KEY:
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                res = await client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {settings.GROQ_API_KEY}"},
                    json={
                        "model": settings.GROQ_MODEL,
                        "messages": [{"role": "user", "content": SIGNAL_EXTRACTION_PROMPT + window}],
                        "temperature": 0.1,
                        "response_format": {"type": "json_object"},
                    },
                )
                if res.is_success:
                    extracted_signals = res.json().get("choices", [{}])[0].get("message", {}).get("content", "{}")
                    extracted_signals = json.loads(extracted_signals).get("signals", [])
        except Exception:
            extracted_signals = []

    # Heuristic fallback if LLM API returned empty or is offline
    if not extracted_signals:
        low_win = window.lower()
        if any(w in low_win for w in ["car", "vehicle", "second", "auto"]):
            extracted_signals.append({
                "type": "missed_cross_sell",
                "confidence": 0.88,
                "evidence": "Customer mentioned purchasing a vehicle",
                "nudge": "Highlight multi-vehicle partner insurance discount",
            })
        if any(w in low_win for w in ["expensive", "tight", "cannot afford", "pay the full"]):
            extracted_signals.append({
                "type": "payment_difficulty",
                "confidence": 0.85,
                "evidence": "Customer mentioned tight monthly budget",
                "nudge": "Offer monthly EMI or quarterly payment plan",
            })
        if any(w in low_win for w in ["upgrade", "15 lakh", "payment link", "interested in renewing"]):
            extracted_signals.append({
                "type": "buying_signal",
                "confidence": 0.92,
                "evidence": "Customer requested 15L upgrade and payment link",
                "nudge": "Process renewal quote upgrade and send payment link",
            })
        if any(w in low_win for w in ["frustrated", "angry", "terrible", "ridiculous", "supervisor", "human"]):
            extracted_signals.append({
                "type": "rising_frustration",
                "confidence": 0.85,
                "evidence": "Customer expressed dissatisfaction or requested manager",
                "nudge": "Acknowledge frustration and offer immediate supervisor escalation",
            })

    llm_latency_ms = round((time.time() - llm_start_ts) * 1000)

    for signal in extracted_signals:
        sig_type = signal.get("type")
        confidence = float(signal.get("confidence", 0))
        cfg = SIGNAL_TYPES.get(sig_type)

        if not cfg or confidence < cfg["confidence_threshold"]:
            continue
        if not session.can_emit(sig_type):
            continue

        session.record_emission(sig_type)
        e2e_latency_ms = round((time.time() - asr_received_ts) * 1000)

        nudge_payload = {
            "type": "nudge",
            "call_id": session.call_id,
            "signal": sig_type,
            "priority": cfg["priority"],
            "confidence": confidence,
            "nudge": signal.get("nudge", ""),
            "evidence": signal.get("evidence", ""),
            "expiry_s": cfg["expiry_s"],
            "latency": {
                "llm_ms": llm_latency_ms,
                "e2e_ms": e2e_latency_ms,
            },
            "timestamp": datetime.utcnow().isoformat(),
        }

        session.emitted_signals.append(nudge_payload)
        await broadcast_to_dashboard(nudge_payload)

        # Trigger HITL escalation if customer frustration is high and HITL is enabled
        if settings.ENABLE_HITL and sig_type == "rising_frustration" and confidence >= settings.HITL_FRUSTRATION_THRESHOLD:
            hitl_manager.create_request(
                call_id=session.call_id,
                agent_name=session.agent_name,
                reason=f"Customer frustration score high ({confidence:.2f}): '{signal.get('evidence', '')}'",
                caller_profile={"call_id": session.call_id},
                transcript_snippet=[{"role": "context", "content": window}],
                suggested_action="Intervene with special goodwill waiver or connect supervisor.",
            )


# ── Pre-scripted Demo Simulation ─────────────────────────────────────────────

DEMO_TRANSCRIPT = [
    (2,  "0", "Good afternoon, this is Aria from ShieldCare. Am I speaking with Priya?"),
    (5,  "1", "Yes, this is Priya. I got a message about my Arogya Shield Plus renewal?"),
    (9,  "0", "That is right! Your policy renews next month. Can I confirm your family floater plan with 10 lakh sum insured?"),
    (13, "1", "Yes, my husband and I are on it. But the premium keeps going up every year. This is getting too expensive for us."),
    (18, "0", "I understand your concern completely. You have earned a 10% no-claim bonus discount on your renewal this year."),
    (23, "1", "Oh that helps. We also just bought a second car last week. Do you provide vehicle insurance as well?"),
    (28, "0", "We specialize exclusively in comprehensive health coverage, though I can share our automotive partner details."),
    (33, "1", "My husband has type 2 diabetes. Will he be covered if we renew?"),
    (38, "0", "Since your policy has been continuously active for over 3 years, his pre-existing diabetes is fully covered without fresh waiting periods."),
    (43, "1", "That is a huge relief! I want to proceed and upgrade our sum insured to 15 lakhs. Please send me the payment link."),
    (48, "0", "Wonderful Priya! I am logging your 15 Lakh renewal quote with the bonus discount applied. Thank you for staying with ShieldCare!"),
]

@app.get("/demo")
async def start_demo():
    call_id = f"demo_{int(time.time())}"
    asyncio.create_task(run_demo_call(call_id))
    return {"message": "Demo call simulation started", "call_id": call_id, "dashboard_url": "http://localhost:8001/"}


async def run_demo_call(call_id: str):
    session = CallSession(call_id, agent_name="Aria")
    session_store[call_id] = session

    await broadcast_to_dashboard({"type": "call_started", "call_id": call_id, "agent": "Aria", "timestamp": datetime.utcnow().isoformat()})

    prev = 0
    for (ts, speaker, text) in DEMO_TRANSCRIPT:
        await asyncio.sleep(max(1, ts - prev))
        prev = ts
        now = time.time()
        speaker_label = "AGENT" if speaker == "0" else "CUSTOMER"

        session.transcript_buffer.append({"text": text, "speaker": speaker, "ts": now})
        await broadcast_to_dashboard({
            "type": "transcript",
            "call_id": call_id,
            "speaker": speaker_label,
            "text": text,
            "timestamp": datetime.utcnow().isoformat(),
        })

        if now - session.last_extraction_time >= session.extraction_interval_s:
            session.last_extraction_time = now
            asyncio.create_task(extract_and_emit_signals(session, now))

    await asyncio.sleep(3)
    await broadcast_to_dashboard({"type": "call_ended", "call_id": call_id, "timestamp": datetime.utcnow().isoformat()})
    if call_id in session_store:
        del session_store[call_id]


if __name__ == "__main__":
    uvicorn.run("pipeline:app", host=settings.HOST, port=settings.PORT, reload=False)
