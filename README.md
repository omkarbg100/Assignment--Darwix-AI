# Production AI Voice Agent & Real-Time Intelligence Platform

> **Assessment Submission — AI Engineer Assessment**  
> **Product Domain:** Arogya Shield Plus Health Insurance (plus Multilingual Life & Multifinance Extensions)  
> **Core Architecture:** LangChain & LangGraph StateGraph, Google Gemini API (with Groq Fallback), ChromaDB Vector Store, Enterprise Guardrails, Operational Middlewares, and Configurable Human-in-the-Loop (HITL) Supervisor Hub.

---

## 🌟 Executive Summary & Enterprise Enhancements

This repository delivers a production-grade, enterprise-ready implementation covering **all four questions** of the AI Engineer Assessment. It elevates the initial prototype into an end-to-end conversational AI platform with state-of-the-art architectures:

1. **`uv` Package Manager & `.venv` Virtual Environment**: Standardized, lightning-fast dependency management and isolated virtual environment setup.
2. **LangGraph State Machine**: Replaced linear loops with a typed `StateGraph` featuring deterministic intent routing, knowledge retrieval branching, checkpointer memory (`MemorySaver`), and interruption for supervisor intervention.
3. **Google Gemini API Primary Engine**: First-class support for `GEMINI_API_KEY` utilizing Google's flagship `gemini-2.0-flash` (and `gemini-1.5-flash`) with automated circuit-breaking fallback to Groq (`llama-3.3-70b-versatile`).
4. **Input & Output Guardrails**:
   - **Input**: Automatic PII sanitization (Aadhaar numbers, PAN, phone numbers, emails) and adversarial prompt injection / jailbreak detection.
   - **Output**: Fact grounding verification against retrieved ChromaDB chunks, hallucination mitigation, and mandatory regulatory compliance disclaimers (e.g. 30-day initial waiting period notice, non-binding quote disclaimer).
5. **Operational Middlewares**:
   - **Telemetry Middleware**: Live P50 and P95 latency tracking across every pipeline phase (ASR, Guardrail, KB, LLM TTFT, TTS).
   - **Audit Trail Middleware**: Cryptographically structured JSONL trace logging for compliance review (`audit_log.jsonl`).
   - **Circuit Breaker**: Provider failover between Gemini and Groq in under 50ms upon HTTP 429/503 errors.
6. **Configurable Human-in-the-Loop (HITL) Supervisor Hub**:
   - Configurable via `ENABLE_HITL` flag (`false` by default for fully autonomous AI handling, `true` for supervisor mode).
   - Real-time escalation queue for callers requesting a human manager or exhibiting high frustration when enabled.
   - Interactive web controls for supervisors: **Approve & Forward**, **Custom Response Override**, or **Direct Call Takeover**.

---

## 📂 Repository Structure

```
d:/Projects/Assignment/
├── .env.example                     ← Template for GEMINI_API_KEY, GROQ_API_KEY, and settings
├── .gitignore                       ← Clean git exclusions (.venv, data stores, logs)
├── README.md                        ← Complete project documentation and guide
├── architecture.md                  ← Comprehensive Mermaid diagrams & technical specs
├── requirements.txt                 ← Production dependency specifications
├── audit_log.jsonl                  ← Real-time structured compliance audit trail
│
├── core/                            ← Shared Enterprise Foundation
│   ├── __init__.py                  ← Package exports
│   ├── config.py                    ← Pydantic centralized configuration
│   ├── llm_factory.py               ← Multi-provider factory (Gemini primary + Groq fallback)
│   ├── guardrails.py                ← Input (PII, Injections) & Output (Grounding, IRDAI) Guardrails
│   ├── middlewares.py               ← Telemetry (P50/P95) and Audit Trail middlewares
│   ├── hitl_manager.py              ← Human-in-the-loop escalation orchestration
│   └── langgraph_agent.py           ← Compiled LangGraph StateGraph agent with memory
│
├── q1_voice_agent/                  ← Question 1: Local Terminal & Voice Agent (Aria)
│   ├── local_voice_agent.py         ← Aria voice agent (LangGraph + Gemini + Offline STT/TTS)
│   ├── crm_mock.py                  ← CRM data layer (leads & callbacks JSON store)
│   ├── system_prompt.md             ← Full persona guidelines and qualification prompt
│   └── transcripts/
│       └── test_calls.md            ← 5 documented call transcripts (cooperative, objections, etc.)
│
├── q2_knowledge_base/               ← Question 2: Production Knowledge Base
│   ├── data/
│   │   └── arogya_shield_plus.json  ← 40 verified records across 8 policy categories
│   ├── ingest.py                    ← Ingestion pipeline (cleaning, chunking, ChromaDB indexing)
│   ├── retrieval.py                 ← Hybrid semantic search + cross-encoder reranker + citations
│   ├── verify_kb.py                 ← Automated test suite for all 5 assessment query categories
│   └── retrieval_tests.md           ← Documented retrieval benchmarks and test logs
│
├── q3_multilingual/                 ← Question 3: Localized Multilingual Agents
│   ├── local_multilingual_agent.py  ← Maya (Philippines Taglish) & Dewi (Indonesia Bahasa)
│   ├── philippines/                 ← Taglish scripts, cultural markers ('po'/'ho'), transcripts
│   └── indonesia/                   ← Bahasa scripts, informal loanwords, cicilan transcripts
│
└── q4_live_insights/                ← Question 4: Live Insights & Supervisor Platform
    ├── pipeline.py                  ← FastAPI server: WebSockets, real-time signal extraction, HITL
    ├── replay_audio.py              ← Real-time audio streamer for live WAV replays
    ├── latency_report.md            ← Empirical P50/P95 latency analysis & false-positive analysis
    └── dashboard/
        └── index.html               ← Unified Glassmorphism Web App:
                                        • 🎙️ Voice Agent (Interactive Web Speech STT/TTS)
                                        • ⚡ Live Insights (3s sliding window nudges & transcript)
                                        • 🧑‍💼 Supervisor HITL Hub (Live queue, approve/override)
                                        • 📊 Guardrails & Latency (Real-time telemetry metrics)
                                        • 👥 CRM Leads (Live lead repository table)
```

---

## ⚡ 5-Minute Quickstart Guide (Using `uv` & `.venv`)

### 1. Environment Setup with `uv`

We recommend **`uv`**, the ultra-fast Python package manager:

```bash
# Verify uv is installed (install via `pip install uv` or `winget install astral-sh.uv` if needed)
uv --version

# Create virtual environment
uv venv .venv

# Activate virtual environment
# Windows PowerShell:
.venv\Scripts\activate

# Install all production dependencies
uv pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy `.env.example` to `.env` and configure your API keys:

```bash
cp .env.example .env
```

Edit `.env`:
```ini
# Google Gemini API (Primary Engine)
GEMINI_API_KEY=AIzaSy_your_gemini_api_key_here
GEMINI_MODEL=gemini-2.0-flash

# Groq API (Secondary / Fallback Engine)
GROQ_API_KEY=gsk_your_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile

# Active LLM Provider ("gemini" or "groq")
LLM_PROVIDER=gemini

# Optional: Deepgram ASR (only needed for raw WAV streaming replay via replay_audio.py)
DEEPGRAM_API_KEY=your_deepgram_key_here
```

---

## 🚀 Running the Components

### Component 1: Unified Web Dashboard & Voice Server (Q1 + Q3 + Q4)

Start the production FastAPI server:

```bash
.venv\Scripts\python q4_live_insights/pipeline.py
```

Open your browser to: **`http://localhost:8001`**

**Explore the 5 Dashboard Tabs:**
1. 🎙️ **Voice Agent**: Select **Aria** (English), **Maya** (Taglish), or **Dewi** (Bahasa), click **Start Call**, and converse directly using browser microphone STT and SpeechSynthesis TTS!
2. ⚡ **Live Insights**: Observe the live transcript feed, 3-second sliding window signal extraction, and contextual recommendation nudges.
3. 🧑‍💼 **Supervisor HITL**: Watch real-time escalation notifications, review caller profile & transcript, and click **Approve**, **Override**, or **Take Over Call**.
4. 📊 **Guardrails & Latency**: Monitor real-time P50/P95 latencies, ASR/LLM/KB timings, and input/output guardrail statuses.
5. 👥 **CRM Leads**: View qualified leads automatically ingested into the CRM store.

---

### Component 2: Local Terminal Voice Agent (Q1 — Aria)

Runs Aria with offline speech recognition and local speech synthesis:

```bash
# Text / Keyboard interactive mode (recommended for quick terminal testing)
.venv\Scripts\python q1_voice_agent/local_voice_agent.py --mode text

# Voice mode with microphone capture
.venv\Scripts\python q1_voice_agent/local_voice_agent.py --mode voice
```

---

### Component 3: Knowledge Base Verification (Q2)

Verify the 40-record ChromaDB vector store, semantic search, and citation grounding:

```bash
# Verify ChromaDB embeddings and run 5 assessment query tests
.venv\Scripts\python q2_knowledge_base/verify_kb.py
```

*Expected output: 5/5 queries passed with citation attribution and grounded excerpts.*

---

### Component 4: Local Multilingual Agents (Q3 — Maya & Dewi)

Test native localized conversations with code-switching and cultural nuance:

```bash
# Maya (Philippines — Taglish / Life Insurance)
.venv\Scripts\python q3_multilingual/local_multilingual_agent.py --agent maya --mode text

# Dewi (Indonesia — Bahasa Indonesia / Multifinance Cicilan)
.venv\Scripts\python q3_multilingual/local_multilingual_agent.py --agent dewi --mode text
```

---

### Component 5: Replaying Audio for Live Insights (Q4 Demo)

Simulate a live phone stream using synthetic audio or pre-recorded WAV:

```bash
# Built-in multi-turn simulation with live nudges (no microphone required)
# Visit in browser: http://localhost:8001/demo

# Or stream a test WAV file into the pipeline
.venv\Scripts\python q4_live_insights/replay_audio.py --generate-test --call-id test-001
```

---

## 🛡️ Enterprise Architecture Deep-Dive

### 1. LangGraph State Machine (`core/langgraph_agent.py`)

The conversation state is structured as a typed state graph:
```
Caller Input ──► [input_guardrail] ──► [intent_router]
                                              │
                      ┌───────────────────────┼───────────────────────┐
                      ▼                       ▼                       ▼
              [kb_retriever]          [llm_generate]             [hitl_node]
                      │                       ▲                       │
                      └───────────────────────┘                       ▼
                                              │                   [Supervisor]
                                              ▼
                                     [output_guardrail]
                                              │
                                              ▼
                                           [Audio TTS]
```

- **`input_guardrail`**: Detects prompt injections, scrubs sensitive PII, and identifies escalation flags.
- **`intent_router`**: Differentiates between policy queries (routing to ChromaDB) and intake qualification steps.
- **`kb_retriever`**: Fetches verified policy records from ChromaDB with citations.
- **`llm_generate`**: Invokes Google Gemini 2.0 Flash / Groq with context and system prompt.
- **`output_guardrail`**: Verifies fact grounding, prevents hallucinations, and appends mandatory IRDAI disclaimers.
- **`hitl_node`**: When `ENABLE_HITL=true`, suspends graph flow, raises WebSocket alerts, and waits for supervisor resolution. When `ENABLE_HITL=false` (default), bypassed so the AI agent handles caller turns autonomously.

### 2. Guardrails Implementation (`core/guardrails.py`)

- **PII Scrubbing**: Regex filters automatically mask Aadhaar numbers, PAN cards, phone numbers, and emails before sending tokens to LLM providers.
- **Prompt Injection Defense**: Heuristic filters block jailbreaks (e.g., "ignore all previous instructions", "DAN mode").
- **Grounding Verification**: Verifies that specific claims, benefits, and waiting periods in the response match the retrieved ChromaDB chunks.
- **Regulatory Compliance Injection**: Injects IRDAI-mandated disclosures on waiting periods and indicative quote estimates.

### 3. Operational Middlewares (`core/middlewares.py`)

- **Telemetry**: Measures per-turn latency for ASR, Guardrails, Retrieval, LLM generation, and TTS; tracks continuous P50 and P95 averages.
- **Audit Trail**: Every turn is logged as an immutable JSON line in `audit_log.jsonl` recording session ID, sanitized prompt, citations, guardrail actions, grounding score, and latency.

### 4. Human-in-the-Loop (HITL) Workflow (`core/hitl_manager.py`)

- Configurable via `ENABLE_HITL` (default: `false` for fully autonomous AI handling).
- When enabled (`ENABLE_HITL=true`), escalations trigger when callers explicitly demand a human manager, when negative sentiment persists across turns, or for high-risk underwriting requests.
- Supervisors receive instant push notifications on the web dashboard with caller profile, transcript context, and recommended resolutions.
- Actions supported: **Approve**, **Custom Override**, or **Direct Call Takeover**.

---

## 📊 Technical Comparison & Benchmark

| Dimension | Previous Prototype | Elevated Production System |
|---|---|---|
| **Package Manager** | Standard `pip` | **`uv` Package Manager** (10-100× faster install) |
| **Virtual Environment** | Manual setup | Isolated **`.venv`** with strict lock adherence |
| **Orchestration** | Ad-hoc Python loops | **LangChain & LangGraph StateGraph** with checkpointer |
| **LLM Provider** | Groq only | **Google Gemini API** (primary) + Groq (automated fallback) |
| **Guardrails** | Basic regex | **Input & Output Guardrails** (PII, Injections, Grounding, IRDAI) |
| **Human-in-the-Loop** | Not implemented | **HITL Supervisor Hub** with live WebSocket controls |
| **Telemetry** | Static markdown | **Live P50/P95 Telemetry Middleware** + JSONL Audit Trail |
| **UI Aesthetics** | Basic 3-tab layout | **Glassmorphism 5-tab Dashboard** (HITL, Telemetry, Voice, Leads) |

---

## 🧪 Verification & Assessment Rubric Checklist

- [x] **Q1 Voice Agent**: Lead intake flow, qualification questions, policy lookup, objection handling, CRM persistence (`crm_mock.py`).
- [x] **Q2 Knowledge Base**: 40 structured policy records, ChromaDB vector store, semantic retrieval, citations, 5/5 test queries verified.
- [x] **Q3 Multilingual Bots**: Maya (Philippines Taglish, `po`/`ho` markers) and Dewi (Indonesia Bahasa, cicilan terms), localized tone and objection handling.
- [x] **Q4 Live Insights Engine**: 3-second sliding window signal extraction, nudge filter with cooldown and confidence thresholds, live WebSocket dashboard.
- [x] **Enterprise Elevation**: LangGraph StateGraph, Gemini API integration, Guardrails, Middlewares, HITL, `uv` support, comprehensive `architecture.md` and `README.md`.

---
*Developed for the AI Engineer Assessment.*
