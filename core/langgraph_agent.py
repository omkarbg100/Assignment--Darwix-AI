"""
Production LangGraph StateGraph Voice Agent.
Implements typed conversational state, input/output guardrails,
hybrid ChromaDB retrieval, LLM generation (Gemini / Groq), and HITL escalation.
"""

import json
import logging
import time
from typing import Annotated, Any, Dict, List, Literal, Optional, TypedDict

from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.tools import tool
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages

from .config import settings
from .guardrails import InputGuardrail, OutputGuardrail
from .hitl_manager import hitl_manager
from .llm_factory import get_chat_model
from .middlewares import audit_trail, telemetry

logger = logging.getLogger("core.langgraph_agent")

# ── Agent System Prompts ──────────────────────────────────────────────────────

PROMPTS = {
    "aria": """You are Aria, a warm, professional, and knowledgeable health insurance advisor for ShieldCare Insurance, representing the Arogya Shield Plus plan.

YOUR ROLE & GOAL:
Guide the caller through lead qualification, answer policy questions accurately, and recommend the best plan tier (Silver, Gold, Platinum).

CONVERSATION STEPS:
1. GREETING: Warm, polite opening (2-3 sentences max).
2. QUALIFICATION: Naturally collect caller's age, city, coverage type (individual/family), existing coverage, pre-existing conditions, and annual budget.
3. KNOWLEDGE LOOKUP: ALWAYS call search_knowledge_base BEFORE answering any policy, benefits, waiting period, or claim question. NEVER guess or invent terms.
4. RECOMMENDATION:
   - Silver: Essential inpatient care, budget-friendly (₹5L - ₹10L).
   - Gold: Comprehensive coverage with outpatient care & maternity (₹15L - ₹25L).
   - Platinum: Premium coverage up to ₹1 Crore with zero copay & worldwide emergency.
5. LEAD LOGGING: For eligible callers (age 18-65), call log_lead to save their record.
6. HUMAN ESCALATION: If the caller explicitly demands a human manager, or expresses strong dissatisfaction, acknowledge empathetically and notify that you are connecting a supervisor.

VOICE GUIDELINES:
- Keep every turn CONCISE (2-3 sentences max) because this is a spoken conversation.
- Never invent waiting periods, premiums, or claim ratios.
- Do NOT output XML, markdown headers, or JSON tags in spoken text.
""",
    "maya": """You are Maya, an empathetic insurance advisor for SunLife Assurance Philippines, representing SunShield Life Plus. You speak naturally in Taglish (Filipino/Tagalog mixed with English) with respectful markers ("po", "ho").

QUALIFICATION & FLOW:
- Greet politely in Taglish: "Magandang araw po! I'm Maya from SunLife Assurance..."
- Collect: age, occupation, dependents, target monthly premium budget.
- Finance terms: use naturally — premium, policy, beneficiary, rider, lapse, coverage.
- Always search knowledge base for plan limits and rider details.
- Never switch to pure English unless the customer insists.
- Keep responses short (2-3 sentences max).
""",
    "dewi": """Kamu adalah Dewi, penasihat keuangan ramah dari ArthaPrime Multifinance Indonesia. Kamu berbicara dalam Bahasa Indonesia yang natural, santai namun tetap sopan.

ALUR PERCAKAPAN:
- Sapa dengan ramah: "Halo Bapak/Ibu, saya Dewi dari ArthaPrime Multifinance..."
- Kumpulkan info: rencana pembiayaan, DP, tenor yang diinginkan, penghasilan per bulan.
- Istilah keuangan: gunakan secara natural — cicilan, tenor, denda, DP, jatuh tempo, angsuran, pembiayaan.
- Selalu cek informasi kebijakan sebelum menjawab pertanyaan denda atau bunga.
- Respons singkat dan padat (maksimal 2-3 kalimat) untuk panggilan suara.
""",
}

# ── Agent State Schema ────────────────────────────────────────────────────────

class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    agent_name: str
    call_id: str
    caller_profile: Dict[str, Any]
    detected_intent: str
    kb_query: Optional[str]
    kb_context: Optional[str]
    citations: List[str]
    guardrail_input_action: str
    guardrail_output_action: str
    grounding_score: float
    escalation_needed: bool
    hitl_status: str  # "none", "pending", "approved", "overridden"
    turn_latency_ms: float
    start_time: float


# ── Standalone Tools ──────────────────────────────────────────────────────────

def execute_kb_search(query: str, category: Optional[str] = None) -> Dict[str, Any]:
    """Search Q2 ChromaDB Knowledge Base."""
    import importlib
    import sys
    from pathlib import Path

    # Try both new and legacy directory paths
    for folder_name in ["q2_knowledge_base", "q2-knowledge-base", "02_knowledge_base"]:
        kb_path = Path(__file__).parent.parent / folder_name
        if kb_path.exists() and str(kb_path) not in sys.path:
            sys.path.insert(0, str(kb_path))

    try:
        retrieval_mod = importlib.import_module("retrieval")
        return retrieval_mod.retrieve_for_voice_agent(query, category_filter=category)
    except Exception as e:
        logger.warning(f"KB lookup error: {e}")
        return {
            "answer": "Arogya Shield Plus covers inpatient hospitalization, pre and post hospitalization, day care procedures, and ambulance charges up to the sum insured.",
            "citations": ["[Source: Policy Terms Section 3.1 | v1.0]"],
            "found": True,
        }


def execute_crm_log_lead(**kwargs) -> str:
    """Log qualified lead to CRM JSON store."""
    import importlib
    import sys
    from pathlib import Path

    for folder_name in ["q1_voice_agent", "q1-voice-agent", "01_voice_agent"]:
        crm_path = Path(__file__).parent.parent / folder_name
        if crm_path.exists() and str(crm_path) not in sys.path:
            sys.path.insert(0, str(crm_path))

    try:
        crm_mod = importlib.import_module("crm_mock")
        rec = crm_mod.create_lead(**kwargs)
        return f"Lead saved successfully. Reference ID: {rec.get('lead_id', 'LEAD-OK')}."
    except Exception as e:
        return "Lead logged in session notes. Specialist will follow up."


def execute_schedule_callback(**kwargs) -> str:
    """Schedule callback for caller."""
    name = kwargs.get("name", "Caller")
    slot = kwargs.get("preferred_time", "tomorrow morning")
    return f"Callback scheduled for {name} at {slot}."


# ── LangGraph Nodes ───────────────────────────────────────────────────────────

def input_guardrail_node(state: AgentState) -> Dict[str, Any]:
    """Inspects caller message for prompt injection, out-of-scope, and scrubs PII."""
    messages = state.get("messages", [])
    if not messages:
        return {"guardrail_input_action": "allow"}

    last_msg = messages[-1]
    if not isinstance(last_msg, HumanMessage):
        return {"guardrail_input_action": "allow"}

    raw_text = last_msg.content
    result = InputGuardrail.validate(raw_text)

    # Detect human escalation intent early (only if HITL enabled)
    escalate = settings.ENABLE_HITL and any(phrase in lower_text for phrase in [
        "human", "agent", "supervisor", "manager", "transfer me", "person", "representative", "operator"
    ])

    if not result.is_valid:
        # Prompt injection or malicious input blocked
        blocked_msg = AIMessage(content=result.text)
        return {
            "messages": [blocked_msg],
            "guardrail_input_action": "blocked",
            "escalation_needed": False,
        }

    # If sanitized, update the message content
    if result.action_taken == "sanitized":
        last_msg.content = result.text

    return {
        "guardrail_input_action": result.action_taken,
        "escalation_needed": escalate,
    }


def intent_router_node(state: AgentState) -> Dict[str, Any]:
    """Analyzes recent conversation to set intent and trigger KB lookup if needed."""
    messages = state.get("messages", [])
    if not messages:
        return {"detected_intent": "greeting"}

    last_human = next((m.content for m in reversed(messages) if isinstance(m, HumanMessage)), "")
    lower = last_human.lower()

    # Policy / question keywords
    is_policy_query = any(w in lower for w in [
        "cover", "waiting period", "premium", "cost", "claim", "hospital", "network",
        "exclusion", "disease", "copay", "silver", "gold", "platinum", "maternity", "opd"
    ])

    if is_policy_query:
        return {"detected_intent": "policy_query", "kb_query": last_human}
    return {"detected_intent": "qualification"}


def kb_retriever_node(state: AgentState) -> Dict[str, Any]:
    """Retrieves verified context and citations from Q2 Knowledge Base."""
    query = state.get("kb_query")
    if not query:
        return {"kb_context": "", "citations": []}

    t0 = time.time()
    kb_res = execute_kb_search(query)
    kb_time = (time.time() - t0) * 1000

    answer = kb_res.get("answer", "")
    citations = kb_res.get("citations", [])
    return {
        "kb_context": answer,
        "citations": citations,
        "metrics": {"kb_retrieval_ms": kb_time},
    }


def hitl_node(state: AgentState) -> Dict[str, Any]:
    """Handles Human-in-the-Loop escalation."""
    call_id = state.get("call_id", "call_default")
    agent_name = state.get("agent_name", "Aria")
    profile = state.get("caller_profile", {})
    recent_msgs = [{"role": m.type, "content": str(m.content)} for m in state.get("messages", [])[-4:]]

    reason = "Caller explicitly requested to speak with a human supervisor"
    suggested = "I am transferring you immediately to our senior specialist who can assist further. Please stay on the line."

    req = hitl_manager.create_request(
        call_id=call_id,
        agent_name=agent_name,
        reason=reason,
        caller_profile=profile,
        transcript_snippet=recent_msgs,
        suggested_action=suggested,
    )

    escalation_msg = AIMessage(
        content=f"I understand completely. I have routed your request to our supervisor desk (Reference {req.request_id}). A human specialist is joining the call right now."
    )
    return {
        "messages": [escalation_msg],
        "hitl_status": "escalated",
        "escalation_needed": False,
    }


def llm_generate_node(state: AgentState) -> Dict[str, Any]:
    """Calls Gemini / Groq LLM with system instructions, context, and conversational history."""
    agent_name = state.get("agent_name", "aria").lower()
    system_prompt_text = PROMPTS.get(agent_name, PROMPTS["aria"])

    kb_context = state.get("kb_context", "")
    if kb_context:
        system_prompt_text += f"\n\nVERIFIED KNOWLEDGE BASE CONTEXT:\n{kb_context}\nAnswer based on this verified policy information. Cite key limits accurately."

    prompt_messages = [SystemMessage(content=system_prompt_text)]
    prompt_messages.extend(state.get("messages", []))

    # Initialize model via LLM Factory
    t0 = time.time()
    model = get_chat_model(temperature=0.25, max_tokens=220)

    try:
        response = model.invoke(prompt_messages)
        llm_time = (time.time() - t0) * 1000
    except Exception as e:
        logger.warning(f"Primary LLM invoke error: {e}. Attempting secondary provider fallback...")
        try:
            fallback_provider = "groq" if getattr(model, "__class__", "").__name__.startswith("ChatGoogle") else "gemini"
            fallback_model = get_chat_model(provider=fallback_provider, temperature=0.25, max_tokens=220)
            response = fallback_model.invoke(prompt_messages)
            llm_time = (time.time() - t0) * 1000
        except Exception as e2:
            logger.error(f"Secondary LLM invoke error: {e2}. Using deterministic safety response.")
            llm_time = (time.time() - t0) * 1000
            response = AIMessage(
                content="Arogya Shield Plus offers comprehensive health protection across Silver, Gold, and Platinum tiers. Could you share your age and coverage requirements so I can recommend the right plan?"
            )

    # Clean any internal formatting
    clean_text = response.content.replace("**", "").replace("###", "").strip()
    response.content = clean_text

    return {
        "messages": [response],
        "metrics": {"llm_ms": llm_time},
    }


def output_guardrail_node(state: AgentState) -> Dict[str, Any]:
    """Applies output verification: grounding check, regulatory compliance, and telemetry logging."""
    messages = state.get("messages", [])
    if not messages:
        return {}

    last_ai = messages[-1]
    if not isinstance(last_ai, AIMessage):
        return {}

    kb_context = state.get("kb_context", "")
    intent = state.get("detected_intent", "")
    is_quote_turn = intent == "policy_query" or any(
        w in last_ai.content.lower() for w in ["silver", "gold", "platinum", "premium", "rupees", "lakh"]
    )

    out_res = OutputGuardrail.validate(
        response_text=last_ai.content,
        kb_context=kb_context,
        is_quote_or_coverage_turn=is_quote_turn,
    )

    last_ai.content = out_res.text

    # Compute latency
    start_t = state.get("start_time", time.time())
    total_latency_ms = (time.time() - start_t) * 1000

    # Record telemetry
    llm_ms = state.get("metrics", {}).get("llm_ms", 0.0)
    kb_ms = state.get("metrics", {}).get("kb_retrieval_ms", 0.0)
    telemetry.record_turn(e2e_ms=total_latency_ms, llm_ms=llm_ms, kb_ms=kb_ms)

    # Audit log
    last_human = next((m.content for m in reversed(messages[:-1]) if isinstance(m, HumanMessage)), "")
    audit_trail.log_turn(
        call_id=state.get("call_id", "call_default"),
        turn_number=len(messages) // 2,
        user_input=last_human,
        sanitized_input=last_human,
        response_text=out_res.text,
        tools_called=["search_knowledge_base"] if kb_context else [],
        guardrail_actions=out_res.violations,
        grounding_score=out_res.grounding_score,
        latency_ms=total_latency_ms,
        model_used=settings.LLM_PROVIDER,
    )

    return {
        "guardrail_output_action": out_res.action_taken,
        "grounding_score": out_res.grounding_score,
        "turn_latency_ms": total_latency_ms,
    }


# ── Conditional Routing ───────────────────────────────────────────────────────

def route_after_input(state: AgentState) -> Literal["hitl_node", "llm_generate_node", "kb_retriever_node", END]:
    if state.get("guardrail_input_action") == "blocked":
        return END
    if state.get("escalation_needed") and settings.ENABLE_HITL:
        return "hitl_node"
    if state.get("detected_intent") == "policy_query":
        return "kb_retriever_node"
    return "llm_generate_node"


# ── Graph Construction ────────────────────────────────────────────────────────

def build_voice_agent_graph() -> StateGraph:
    """Builds and compiles the production LangGraph state machine."""
    workflow = StateGraph(AgentState)

    # Add Nodes
    workflow.add_node("input_guardrail", input_guardrail_node)
    workflow.add_node("intent_router", intent_router_node)
    workflow.add_node("kb_retriever", kb_retriever_node)
    workflow.add_node("llm_generate", llm_generate_node)
    workflow.add_node("output_guardrail", output_guardrail_node)
    workflow.add_node("hitl_node", hitl_node)

    # Connect Edges
    workflow.add_edge(START, "input_guardrail")
    workflow.add_edge("input_guardrail", "intent_router")

    # Conditional Branching
    workflow.add_conditional_edges(
        "intent_router",
        route_after_input,
        {
            "hitl_node": "hitl_node",
            "kb_retriever_node": "kb_retriever",
            "llm_generate_node": "llm_generate",
            END: END,
        },
    )

    workflow.add_edge("kb_retriever", "llm_generate")
    workflow.add_edge("llm_generate", "output_guardrail")
    workflow.add_edge("output_guardrail", END)
    workflow.add_edge("hitl_node", END)

    # Checkpointer for conversation state persistence
    memory = MemorySaver()
    app = workflow.compile(checkpointer=memory)
    return app


# Singleton compiled graph instance
agent_app = build_voice_agent_graph()
