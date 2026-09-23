"""
LLM Factory providing unified access to Google Gemini and Groq models.
Supports LangChain ChatGoogleGenerativeAI and ChatGroq with automatic fallback.
"""

import logging
from typing import Any, Optional
from langchain_core.language_models.chat_models import BaseChatModel

from .config import settings

logger = logging.getLogger("core.llm_factory")


def get_chat_model(
    provider: Optional[str] = None,
    model_name: Optional[str] = None,
    temperature: float = 0.2,
    max_tokens: int = 400,
) -> BaseChatModel:
    """
    Returns a configured LangChain ChatModel instance.
    Defaults to Gemini if GEMINI_API_KEY is configured, otherwise Groq.
    """
    selected_provider = (provider or settings.LLM_PROVIDER or "gemini").lower()

    # ── Attempt 1: Google Gemini ─────────────────────────────────────────────
    if selected_provider == "gemini" and settings.GEMINI_API_KEY:
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI

            actual_model = model_name or settings.GEMINI_MODEL
            logger.info(f"Instantiating ChatGoogleGenerativeAI: {actual_model}")
            return ChatGoogleGenerativeAI(
                model=actual_model,
                google_api_key=settings.GEMINI_API_KEY,
                temperature=temperature,
                max_output_tokens=max_tokens,
            )
        except Exception as e:
            logger.warning(f"Failed to initialize Gemini ({e}). Falling back to Groq.")

    # ── Attempt 2: Groq ──────────────────────────────────────────────────────
    if settings.GROQ_API_KEY:
        try:
            from langchain_groq import ChatGroq

            actual_model = model_name or settings.GROQ_MODEL
            logger.info(f"Instantiating ChatGroq: {actual_model}")
            return ChatGroq(
                model=actual_model,
                api_key=settings.GROQ_API_KEY,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        except Exception as e:
            logger.warning(f"Failed to initialize Groq ({e}).")

    # ── Attempt 3: If Gemini key is set, try again with standard name ────────
    if settings.GEMINI_API_KEY:
        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(
            model=model_name or settings.GEMINI_MODEL,
            google_api_key=settings.GEMINI_API_KEY,
            temperature=temperature,
            max_output_tokens=max_tokens,
        )

    # If neither key is supplied, instantiate ChatGroq or ChatGoogleGenerativeAI
    # with placeholder so code structure remains valid
    try:
        from langchain_groq import ChatGroq
        return ChatGroq(model=settings.GROQ_MODEL, api_key="placeholder_key")
    except Exception:
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(model=settings.GEMINI_MODEL, google_api_key="placeholder_key")
