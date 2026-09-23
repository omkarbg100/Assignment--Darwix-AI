"""
Q1 - Local Voice Agent: Aria - Arogya Shield Plus Health Insurance
==================================================================
Runs locally with LangGraph StateGraph, Google Gemini / Groq LLM,
Input/Output Guardrails, Knowledge-Grounded Retrieval, and HITL Escalation.

Stack:
  Audio Input -> sounddevice + Google Speech Recognition (or interactive text mode)
  State Graph -> LangGraph (StateGraph with checkpointer)
  LLM Engine  -> Google Gemini API (gemini-2.0-flash) with Groq fallback
  Grounding   -> Q2 ChromaDB Knowledge Base + Reranking + Citations
  Guardrails  -> PII Sanitization, Prompt Injection Defense, Regulatory Disclosures
  Audio TTS   -> Windows PowerShell .NET SpeechSynthesizer (offline, zero external lag)

Usage:
    .venv\\Scripts\\python q1_voice_agent/local_voice_agent.py
    .venv\\Scripts\\python q1_voice_agent/local_voice_agent.py --mode text
"""

import argparse
import io
import json
import os
import subprocess
import sys
import time
import uuid
import wave
from pathlib import Path

# Add root directory to sys.path
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from langchain_core.messages import HumanMessage
from core.config import settings
from core.langgraph_agent import agent_app
from core.middlewares import telemetry

# Audio capture defaults
SAMPLE_RATE = 16000
CHANNELS = 1


def speak(text: str):
    """Speak text using Windows built-in .NET SpeechSynthesizer via PowerShell."""
    print(f"\n  ARIA : {text}")
    safe = text.replace("'", "''").replace('"', '`"')
    ps_cmd = (
        "Add-Type -AssemblyName System.Speech; "
        "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
        "$s.Rate = 1; "
        f"$s.Speak('{safe}')"
    )
    try:
        subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_cmd],
            capture_output=True,
            timeout=15,
        )
    except Exception:
        pass


def record_audio(duration_s: int = 8) -> any:
    """Record speech from microphone using sounddevice."""
    import numpy as np
    import sounddevice as sd

    print("  [Listening... speak now, pause when finished]", end="", flush=True)
    audio = sd.rec(
        int(duration_s * SAMPLE_RATE),
        samplerate=SAMPLE_RATE,
        channels=CHANNELS,
        dtype="int16",
    )
    sd.wait()
    print(" [Captured]")
    return audio


def audio_to_wav_bytes(audio) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(audio.tobytes())
    return buf.getvalue()


def listen_microphone() -> str | None:
    """Capture audio from mic and transcribe with Google Speech Recognition."""
    import speech_recognition as sr

    try:
        audio_data = record_audio(duration_s=7)
        wav_bytes = audio_to_wav_bytes(audio_data)
        recognizer = sr.Recognizer()
        audio_file = sr.AudioData(wav_bytes, SAMPLE_RATE, 2)
        text = recognizer.recognize_google(audio_file, language="en-IN")
        print(f"  YOU  : {text}")
        return text
    except sr.UnknownValueError:
        print("  [Could not understand speech -- please repeat]")
        return None
    except Exception as e:
        print(f"  [Microphone note: {e} -- switching to text prompt for this turn]")
        return input("  YOU (Type here) : ").strip() or None


def run_call(mode: str = "voice"):
    call_id = f"call_{uuid.uuid4().hex[:8]}"
    thread_id = f"thread_{call_id}"
    config = {"configurable": {"thread_id": thread_id}}

    print()
    print("=" * 70)
    print("  ARIA -- AROGYA SHIELD PLUS  (Enterprise LangGraph Voice Agent)")
    print("=" * 70)
    print(f"  Call Session ID : {call_id}")
    print(f"  LLM Engine      : {settings.LLM_PROVIDER.upper()} ({settings.GEMINI_MODEL if settings.LLM_PROVIDER == 'gemini' else settings.GROQ_MODEL})")
    print(f"  Knowledge Base  : Q2 ChromaDB (Arogya Shield Plus Vector Store)")
    print(f"  Guardrails      : Active (PII Scrubbing, Prompt Injection, Grounding)")
    print(f"  Interaction Mode: {mode.upper()}")
    print("  Controls        : Type or say 'goodbye', 'quit', or 'exit' to end call")
    print("=" * 70)
    print()

    # Turn 0: Opening Greeting
    opening = (
        "Hello! I am Aria from ShieldCare Insurance, representing our Arogya Shield Plus health plan. "
        "Do you have about 3 to 4 minutes to discuss your health coverage needs?"
    )
    speak(opening)

    while True:
        if mode == "voice":
            user_text = listen_microphone()
        else:
            try:
                user_text = input("\n  YOU : ").strip()
            except (KeyboardInterrupt, EOFError):
                break

        if not user_text:
            continue

        # Exit conditions
        if any(w in user_text.lower() for w in ["goodbye", "bye", "exit", "quit", "hang up", "end call"]):
            speak("Thank you for speaking with ShieldCare Insurance. Have a great day ahead! Goodbye!")
            print("\n  [Call Ended Gracefully]\n")
            break

        turn_start = time.time()

        # Invoke LangGraph State Machine
        initial_state = {
            "messages": [HumanMessage(content=user_text)],
            "agent_name": "aria",
            "call_id": call_id,
            "start_time": turn_start,
        }

        try:
            result = agent_app.invoke(initial_state, config=config)
            last_message = result["messages"][-1].content

            # Display real-time telemetry badge
            latency = result.get("turn_latency_ms", (time.time() - turn_start) * 1000)
            grounding = result.get("grounding_score", 1.0)
            in_action = result.get("guardrail_input_action", "allow")
            out_action = result.get("guardrail_output_action", "allow")
            hitl = result.get("hitl_status", "none")

            print(f"  [TELEMETRY] Latency: {latency:.0f}ms | Grounding: {grounding:.2f} | Guardrail: In={in_action}, Out={out_action} | HITL={hitl}")

            speak(last_message)

        except Exception as e:
            print(f"  [Agent Exception: {e}]")
            speak("I apologize for the momentary connection lapse. Could you please repeat that?")


def main():
    parser = argparse.ArgumentParser(description="Run Aria Voice Agent")
    parser.add_argument(
        "--mode",
        choices=["voice", "text"],
        default="text" if "--text" in sys.argv else "voice",
        help="Input mode: 'voice' (microphone) or 'text' (interactive keyboard)",
    )
    args = parser.parse_args()
    run_call(mode=args.mode)


if __name__ == "__main__":
    main()
