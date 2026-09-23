"""
Human-in-the-Loop (HITL) Orchestration Manager.
Allows human supervisors to inspect escalated calls, approve or override
underwriting proposals, and handle manual agent takeovers.
"""

import asyncio
import logging
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger("core.hitl")


@dataclass
class HITLRequest:
    request_id: str
    call_id: str
    agent_name: str
    reason: str
    caller_profile: Dict[str, Any]
    transcript_snippet: List[Dict[str, str]]
    suggested_action: str
    status: str = "pending"  # "pending", "approved", "overridden", "transferred"
    resolution_text: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    resolved_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class HITLManager:
    """In-memory store and lifecycle dispatcher for Human-in-the-Loop requests."""

    def __init__(self):
        self._requests: Dict[str, HITLRequest] = {}
        self._listeners: List[Callable[[Dict[str, Any]], None]] = []
        self._waiters: Dict[str, asyncio.Event] = {}

    def subscribe(self, callback: Callable[[Dict[str, Any]], None]):
        """Register a callback (e.g. WebSocket broadcaster)."""
        self._listeners.append(callback)

    def _notify(self, event_type: str, item: HITLRequest):
        payload = {"event": event_type, "data": item.to_dict()}
        for cb in self._listeners:
            try:
                if asyncio.iscoroutinefunction(cb):
                    asyncio.create_task(cb(payload))
                else:
                    cb(payload)
            except Exception as e:
                logger.error(f"HITL listener error: {e}")

    def create_request(
        self,
        call_id: str,
        agent_name: str,
        reason: str,
        caller_profile: Dict[str, Any],
        transcript_snippet: List[Dict[str, str]],
        suggested_action: str,
    ) -> HITLRequest:
        req_id = f"hitl_{uuid.uuid4().hex[:8]}"
        req = HITLRequest(
            request_id=req_id,
            call_id=call_id,
            agent_name=agent_name,
            reason=reason,
            caller_profile=caller_profile,
            transcript_snippet=transcript_snippet,
            suggested_action=suggested_action,
        )
        self._requests[req_id] = req
        self._waiters[req_id] = asyncio.Event()
        self._notify("hitl_queued", req)
        logger.info(f"[HITL] Queued escalation {req_id} for call {call_id}: {reason}")
        return req

    def get_pending(self) -> List[Dict[str, Any]]:
        return [r.to_dict() for r in self._requests.values() if r.status == "pending"]

    def get_all(self) -> List[Dict[str, Any]]:
        return [r.to_dict() for r in self._requests.values()]

    def resolve(
        self,
        request_id: str,
        action: str,  # "approve", "override", "transfer"
        resolution_text: Optional[str] = None,
    ) -> Optional[HITLRequest]:
        req = self._requests.get(request_id)
        if not req:
            return None

        req.status = action
        req.resolved_at = datetime.utcnow().isoformat() + "Z"
        req.resolution_text = resolution_text or req.suggested_action

        # Unblock any waiting asynchronous task
        if request_id in self._waiters:
            self._waiters[request_id].set()

        self._notify("hitl_resolved", req)
        logger.info(f"[HITL] Resolved {request_id} with action '{action}'")
        return req

    async def wait_for_resolution(self, request_id: str, timeout_s: float = 30.0) -> Optional[HITLRequest]:
        """Async wait until human supervisor resolves the request or timeout expires."""
        waiter = self._waiters.get(request_id)
        if not waiter:
            return self._requests.get(request_id)

        try:
            await asyncio.wait_for(waiter.wait(), timeout=timeout_s)
        except asyncio.TimeoutError:
            # Auto-fallback if supervisor doesn't respond in time
            req = self._requests.get(request_id)
            if req and req.status == "pending":
                req.status = "approved"
                req.resolved_at = datetime.utcnow().isoformat() + "Z"
                req.resolution_text = req.suggested_action + " (Auto-approved on timeout)"
                self._notify("hitl_timeout_auto_approved", req)
        return self._requests.get(request_id)


hitl_manager = HITLManager()
