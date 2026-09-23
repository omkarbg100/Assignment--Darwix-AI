"""
Core configuration settings loaded from environment and .env file.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).parent.parent
ENV_FILE = ROOT_DIR / ".env"
if ENV_FILE.exists():
    load_dotenv(dotenv_path=ENV_FILE, override=True)
else:
    # Also load from .env.example as fallback defaults if .env doesn't exist yet
    load_dotenv(dotenv_path=ROOT_DIR / ".env.example", override=False)


class Settings:
    # ── LLM Settings ──────────────────────────────────────────────────────────
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

    # LLM Provider selection: "gemini" or "groq"
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "").lower()
    if not LLM_PROVIDER:
        LLM_PROVIDER = "gemini" if GEMINI_API_KEY else "groq"

    # ── ASR & Audio ───────────────────────────────────────────────────────────
    DEEPGRAM_API_KEY: str = os.getenv("DEEPGRAM_API_KEY", "")

    # ── Networking ────────────────────────────────────────────────────────────
    PORT: int = int(os.getenv("PORT", "8001"))
    HOST: str = os.getenv("HOST", "0.0.0.0")

    # ── Guardrails & HITL ─────────────────────────────────────────────────────
    ENABLE_INPUT_GUARDRAILS: bool = os.getenv("ENABLE_INPUT_GUARDRAILS", "true").lower() in ("true", "1", "yes")
    ENABLE_OUTPUT_GUARDRAILS: bool = os.getenv("ENABLE_OUTPUT_GUARDRAILS", "true").lower() in ("true", "1", "yes")
    ENABLE_HITL: bool = os.getenv("ENABLE_HITL", "false").lower() in ("true", "1", "yes")
    HITL_FRUSTRATION_THRESHOLD: float = float(os.getenv("HITL_FRUSTRATION_THRESHOLD", "0.75"))
    HITL_SUM_INSURED_THRESHOLD: int = int(os.getenv("HITL_SUM_INSURED_THRESHOLD", "2500000"))

    # ── Path Directories ──────────────────────────────────────────────────────
    BASE_DIR: Path = ROOT_DIR
    CHROMA_DIR: Path = ROOT_DIR / "02_knowledge_base" / "chroma_db"
    DATA_DIR: Path = ROOT_DIR / "02_knowledge_base" / "data"
    CRM_LEADS_FILE: Path = ROOT_DIR / "01_voice_agent" / "crm_leads.json"
    CRM_CALLBACKS_FILE: Path = ROOT_DIR / "01_voice_agent" / "callbacks.json"
    AUDIT_LOG_FILE: Path = ROOT_DIR / "audit_log.jsonl"


settings = Settings()
