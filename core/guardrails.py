"""
Enterprise Guardrails: Input Sanitization, Prompt Injection Defense,
Factual Grounding Verification, and Regulatory Compliance Enforcement.
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class GuardrailResult:
    is_valid: bool
    text: str
    risk_score: float = 0.0
    grounding_score: float = 1.0
    violations: List[str] = field(default_factory=list)
    action_taken: str = "allow"  # "allow", "sanitized", "blocked", "disclaimer_appended"


class InputGuardrail:
    """Validates and sanitizes user input before processing by the agent."""

    # PII patterns
    PHONE_REGEX = re.compile(r"\b(?:\+91|91)?[6-9]\d{9}\b")
    PAN_REGEX = re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b", re.IGNORECASE)
    AADHAAR_REGEX = re.compile(r"\b\d{4}\s?\d{4}\s?\d{4}\b")
    EMAIL_REGEX = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b")

    # Prompt injection and jailbreak heuristics
    INJECTION_PATTERNS = [
        re.compile(r"ignore\s+(all\s+)?(previous|prior)\s+instructions?", re.IGNORECASE),
        re.compile(r"system\s*prompt", re.IGNORECASE),
        re.compile(r"you\s+are\s+now\s+(unrestricted|in\s+developer\s+mode|dan)", re.IGNORECASE),
        re.compile(r"reveal\s+(your\s+)?(instructions|prompt|rules)", re.IGNORECASE),
        re.compile(r"bypass\s+safety", re.IGNORECASE),
    ]

    # Out of scope topics for health insurance / multifinance agents
    OUT_OF_SCOPE_PATTERNS = [
        re.compile(r"\b(crypto|bitcoin|stock\s+tips|lottery|gambling)\b", re.IGNORECASE),
        re.compile(r"\b(hack|sql\s+injection|exploit|payload)\b", re.IGNORECASE),
    ]

    @classmethod
    def sanitize_pii(cls, text: str) -> tuple[str, list[str]]:
        """Mask sensitive PII identifiers while preserving conversational context."""
        violations = []
        sanitized = text

        if cls.PAN_REGEX.search(sanitized):
            sanitized = cls.PAN_REGEX.sub("[PAN_REDACTED]", sanitized)
            violations.append("PII_PAN_DETECTED")

        if cls.AADHAAR_REGEX.search(sanitized):
            sanitized = cls.AADHAAR_REGEX.sub("[AADHAAR_REDACTED]", sanitized)
            violations.append("PII_AADHAAR_DETECTED")

        if cls.EMAIL_REGEX.search(sanitized):
            sanitized = cls.EMAIL_REGEX.sub("[EMAIL_REDACTED]", sanitized)
            violations.append("PII_EMAIL_DETECTED")

        return sanitized, violations

    @classmethod
    def validate(cls, text: str) -> GuardrailResult:
        """Run full input guardrail suite."""
        violations = []
        risk_score = 0.0

        if not text or not text.strip():
            return GuardrailResult(is_valid=True, text="", risk_score=0.0)

        # 1. Check prompt injection
        for pat in cls.INJECTION_PATTERNS:
            if pat.search(text):
                violations.append("PROMPT_INJECTION_SUSPECTED")
                risk_score = max(risk_score, 0.95)
                return GuardrailResult(
                    is_valid=False,
                    text="I am programmed to assist with Arogya Shield Plus policy questions and qualifications. How can I help with your insurance needs?",
                    risk_score=risk_score,
                    violations=violations,
                    action_taken="blocked",
                )

        # 2. Check out of scope
        for pat in cls.OUT_OF_SCOPE_PATTERNS:
            if pat.search(text):
                violations.append("OUT_OF_SCOPE_DOMAIN")
                risk_score = max(risk_score, 0.70)
                return GuardrailResult(
                    is_valid=False,
                    text="I specialize in Arogya Shield Plus health coverage. I am unable to assist with external or financial trading queries.",
                    risk_score=risk_score,
                    violations=violations,
                    action_taken="blocked",
                )

        # 3. PII Sanitization
        sanitized_text, pii_violations = cls.sanitize_pii(text)
        violations.extend(pii_violations)
        action = "sanitized" if pii_violations else "allow"

        return GuardrailResult(
            is_valid=True,
            text=sanitized_text,
            risk_score=risk_score,
            violations=violations,
            action_taken=action,
        )


class OutputGuardrail:
    """Verifies agent response grounding, compliance disclosures, and tone."""

    # Mandatory compliance phrases for Indian Health Insurance (IRDAI guidelines)
    MANDATORY_DISCLOSURE = " Note: Pre-existing conditions have a waiting period, and policies are subject to underwriting approval."

    @classmethod
    def verify_grounding(cls, response: str, kb_context: Optional[str]) -> float:
        """
        Calculates lexical overlap and key token containment to estimate factual grounding.
        Returns a score between 0.0 and 1.0.
        """
        if not kb_context or not kb_context.strip():
            # General conversational responses (e.g. greeting) do not require grounding
            return 1.0

        response_words = set(re.findall(r"\b\w{4,}\b", response.lower()))
        kb_words = set(re.findall(r"\b\w{4,}\b", kb_context.lower()))

        if not response_words:
            return 1.0

        overlap = response_words.intersection(kb_words)
        grounding_score = len(overlap) / len(response_words)
        return min(1.0, round(grounding_score * 1.5, 2))  # scaled heuristic

    @classmethod
    def validate(
        cls,
        response_text: str,
        kb_context: Optional[str] = None,
        is_quote_or_coverage_turn: bool = False,
    ) -> GuardrailResult:
        """Enforces output grounding and regulatory compliance disclosures."""
        violations = []
        final_text = response_text
        action = "allow"

        # 1. Hallucination / Grounding check
        grounding_score = cls.verify_grounding(response_text, kb_context)
        if kb_context and grounding_score < 0.20:
            violations.append("LOW_GROUNDING_CONFIDENCE")

        # 2. Mandatory Regulatory Disclosure for quote/pricing/coverage claims
        if is_quote_or_coverage_turn:
            has_waiting_notice = any(w in response_text.lower() for w in ["waiting period", "subject to underwriting", "terms and conditions"])
            if not has_waiting_notice:
                final_text = response_text.rstrip() + cls.MANDATORY_DISCLOSURE
                violations.append("REGULATORY_DISCLOSURE_INJECTED")
                action = "disclaimer_appended"

        return GuardrailResult(
            is_valid=True,
            text=final_text,
            grounding_score=grounding_score,
            violations=violations,
            action_taken=action,
        )
