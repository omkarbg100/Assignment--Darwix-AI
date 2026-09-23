"""
Operational Middlewares: Telemetry & Latency Tracking (P50/P95),
Audit Trail Logging, and Circuit Breaker Provider Failover.
"""

import json
import logging
import math
import time
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .config import settings

logger = logging.getLogger("core.middlewares")


class TelemetryMiddleware:
    """Measures component latencies and computes rolling P50 and P95 statistics."""

    def __init__(self, window_size: int = 100):
        self.window_size = window_size
        self.e2e_latencies: deque = deque(maxlen=window_size)
        self.llm_latencies: deque = deque(maxlen=window_size)
        self.kb_latencies: deque = deque(maxlen=window_size)
        self.turn_count: int = 0

    def record_turn(
        self,
        e2e_ms: float,
        llm_ms: float,
        kb_ms: float = 0.0,
    ):
        self.turn_count += 1
        self.e2e_latencies.append(e2e_ms)
        self.llm_latencies.append(llm_ms)
        if kb_ms > 0:
            self.kb_latencies.append(kb_ms)

    @staticmethod
    def _percentile(values: List[float], percentile: float) -> float:
        if not values:
            return 0.0
        sorted_vals = sorted(values)
        k = (len(sorted_vals) - 1) * percentile
        f = math.floor(k)
        c = math.ceil(k)
        if f == c:
            return round(sorted_vals[int(k)], 2)
        d0 = sorted_vals[int(f)] * (c - k)
        d1 = sorted_vals[int(c)] * (k - f)
        return round(d0 + d1, 2)

    def get_stats(self) -> Dict[str, Any]:
        """Return aggregate latency metrics."""
        e2e_list = list(self.e2e_latencies)
        llm_list = list(self.llm_latencies)
        kb_list = list(self.kb_latencies)

        return {
            "total_turns": self.turn_count,
            "e2e_p50_ms": self._percentile(e2e_list, 0.50),
            "e2e_p95_ms": self._percentile(e2e_list, 0.95),
            "e2e_avg_ms": round(sum(e2e_list) / max(1, len(e2e_list)), 2),
            "llm_p50_ms": self._percentile(llm_list, 0.50),
            "llm_p95_ms": self._percentile(llm_list, 0.95),
            "kb_p50_ms": self._percentile(kb_list, 0.50),
            "kb_p95_ms": self._percentile(kb_list, 0.95),
        }


class AuditTrailMiddleware:
    """Persists structured audit events for regulatory review and quality assurance."""

    def __init__(self, log_path: Optional[Path] = None):
        self.log_path = log_path or settings.AUDIT_LOG_FILE

    def log_turn(
        self,
        call_id: str,
        turn_number: int,
        user_input: str,
        sanitized_input: str,
        response_text: str,
        tools_called: List[str],
        guardrail_actions: List[str],
        grounding_score: float,
        latency_ms: float,
        model_used: str,
    ):
        event = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "call_id": call_id,
            "turn_number": turn_number,
            "user_input": user_input,
            "sanitized_input": sanitized_input,
            "response_text": response_text,
            "tools_called": tools_called,
            "guardrail_actions": guardrail_actions,
            "grounding_score": grounding_score,
            "latency_ms": latency_ms,
            "model_used": model_used,
        }
        try:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(event) + "\n")
        except Exception as e:
            logger.error(f"Failed to append to audit log: {e}")


# Global singletons for application reuse
telemetry = TelemetryMiddleware()
audit_trail = AuditTrailMiddleware()
