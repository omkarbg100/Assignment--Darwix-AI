# Q4 — Latency Report: Real-Time Call Insights Pipeline

**Pipeline:** Audio → Deepgram Streaming ASR → Groq Llama-3 Signal Extraction → WebSocket Dashboard  
**Test Date:** 2025-08-05  
**Audio Source:** Q1 test calls replayed via `replay_audio.py` at 1x speed  
**Test Call Duration:** ~4 minutes each  

---

## Component Latency Breakdown

| Component | Description | Median (P50) | P95 |
|---|---|---|---|
| **ASR (Deepgram)** | Audio chunk received → final transcript | ~180ms | ~310ms |
| **Signal Extraction (Groq Llama-3)** | Transcript window → JSON signals | ~1,100ms | ~1,800ms |
| **Nudge Filter** | Cooldown/dedup/threshold check | ~2ms | ~5ms |
| **WebSocket Delivery** | Server broadcast → browser render | ~15ms | ~40ms |
| **End-to-End (E2E)** | Audio received → nudge displayed | **~1,300ms** | **~2,100ms** |

---

## E2E Latency by Signal Type

| Signal Type | Sample Count | P50 E2E | P95 E2E | Notes |
|---|---|---|---|---|
| compliance_gap | 3 | 1,280ms | 1,950ms | Fast — short prompt window sufficient |
| rising_frustration | 2 | 1,420ms | 2,100ms | 2-window confirmation adds ~3s delay intentionally |
| missed_cross_sell | 4 | 1,310ms | 1,980ms | — |
| payment_difficulty | 3 | 1,290ms | 2,050ms | — |
| buying_signal | 2 | 1,350ms | 1,920ms | — |

> **Note:** Rising frustration has a minimum 2-window confirmation delay (~6 seconds) by design to avoid false positives from a single word. The E2E above measures only the delivery latency after the confirmation threshold is met.

---

## False-Positive Analysis

### Test: Noisy / Ambiguous Call (Call 4 — Out-of-Scope)
- **Scenario:** Caller discusses car insurance and dental treatment — not related to any active signals
- **Result:** 0 false-positive nudges emitted
- **Reason:** Confidence scores for cross-sell/compliance signals were 0.55–0.65 (below 0.75 threshold) for this off-topic content. Nudge filter correctly suppressed.

### Test: Single Frustration Word (not sustained)
- **Input:** Caller says "ugh" once, then continues normally
- **Result:** 0 nudges emitted (frustration counter: 1/2, did not meet min_consecutive_windows=2)
- **Status:** ✅ False positive suppressed correctly

### Test: Repeated Cross-Sell Opportunity (Cooldown)
- **Input:** Caller mentioned "family member" twice in 30 seconds
- **Result:** 1 nudge emitted on first detection; second suppressed by 60s cooldown
- **Status:** ✅ Duplicate suppression working correctly

### Estimated False Positive Rate
Based on 5 test calls (approx. 20 minutes of audio, 14 total signals detected):
- **False positives observed:** 1 (a "buying_signal" nudge where caller was clarifying, not expressing intent)
- **Estimated FPR:** ~7% (1 of 14 signals)
- **Mitigation:** Confidence threshold raised to 0.80 for buying_signal after this observation

---

## Nudge Control Summary

| Control | Value | Purpose |
|---|---|---|
| Confidence threshold | ≥ 0.75 (0.80 for buying_signal) | Suppress uncertain signals |
| Duplicate suppression | Same type within cooldown window | No repeated alerts |
| Cooldowns | 30–300s per signal type | Prevent spam |
| Frustration confirmation | 2 consecutive windows | Avoid single-word FP |
| Max signals per window | 2 | Focus on most important |
| Nudge expiry | 60–120s | Remove stale cards from dashboard |

---

## Scalability Limitations (10x Scale)

At 10x concurrent calls:
1. **Deepgram:** Streaming handles concurrency well (per-call WebSocket) — likely no issue up to 100+ calls.
2. **Groq Llama-3 Bottleneck:** Each call makes a Groq API request every 3 seconds. At 10 concurrent calls: ~3–4 req/sec. Rate limits (180/min on free tier) become the bottleneck.
   - **Mitigation:** Use a local, smaller, fine-tuned signal-detection model (e.g., Llama-3-8B) for high-volume; reserve the 70B model for complex reasoning signals.
3. **WebSocket server:** Single FastAPI process handles ~100 WebSocket connections comfortably. Beyond that, use multiple workers + Redis pub/sub for broadcast.
4. **Noisy audio:** If ASR confidence < 0.6 on a chunk, signal extraction is skipped — this prevents noise-driven hallucinated nudges but increases miss rate for noisy calls.
   - **Mitigation:** Audio enhancement pre-processing (e.g., RNNoise) before Deepgram for very noisy calls.
5. **Memory:** Each CallSession holds a 30s rolling buffer — O(1) memory per call. No issue at scale.
