"""
Q3 - Local Multilingual Voice Agents: Maya (Philippines) & Dewi (Indonesia)
===========================================================================
Runs localized native financial agents handling natural code-switching (Taglish),
regional nuances (Bahasa Indonesia / Javanese loanwords), and cultural politeness.

Stack:
  Input       -> sounddevice + Google Speech Recognition (fil-PH / id-ID) or keyboard text
  Framework   -> LangGraph State Machine
  LLM Engine  -> Google Gemini API (gemini-2.0-flash) with Groq fallback
  TTS         -> Windows PowerShell .NET SpeechSynthesizer (offline)

Usage:
    .venv\\Scripts\\python q3_multilingual/local_multilingual_agent.py --agent maya --mode text
    .venv\\Scripts\\python q3_multilingual/local_multilingual_agent.py --agent dewi --mode text
    .venv\\Scripts\\python q3_multilingual/local_multilingual_agent.py --agent maya --mode voice
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

SAMPLE_RATE = 16000
CHANNELS = 1

AGENTS = {
    "maya": {
        "id": "Philippines",
        "name": "Maya",
        "sector": "SunLife Assurance Philippines (Life / Bancassurance)",
        "language": "Taglish (Filipino + English)",
        "stt_lang": "fil-PH",
        "opening": (
            "Magandang araw po! I'm Maya from SunLife Assurance Philippines. "
            "I'm reaching out regarding our SunShield Life Plus protection plan. "
            "May I have just 3 to 4 minutes of your time po?"
        ),
        "goodbye": "Maraming salamat po sa inyong oras! Stay safe and have a blessed day po. Goodbye!",
    },
    "dewi": {
        "id": "Indonesia",
        "name": "Dewi",
        "sector": "ArthaPrime Multifinance Indonesia (Consumer Finance)",
        "language": "Bahasa Indonesia (Natural & Colloquial)",
        "stt_lang": "id-ID",
        "opening": (
            "Halo selamat siang Bapak/Ibu, saya Dewi dari ArthaPrime Multifinance. "
            "Saya menghubungi untuk menginformasikan simulasi pembiayaan dan cicilan ringan kami. "
            "Bisa minta waktunya sebentar sekitar 3 menit?"
        ),
        "goodbye": "Terima kasih banyak atas waktunya Bapak/Ibu. Semoga sehat dan lancar selalu rezekinya. Sampai jumpa!",
    },
}


def speak(agent_name: str, text: str):
    """Speak text using Windows built-in .NET SpeechSynthesizer via PowerShell."""
    print(f"\n  {agent_name.upper()} : {text}")
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

    print("  [Listening... speak now in local language, pause when finished]", end="", flush=True)
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


def listen_microphone(lang_code: str) -> str | None:
    """Capture audio from mic and transcribe with language-specific Google STT."""
    import speech_recognition as sr

    try:
        audio_data = record_audio(duration_s=7)
        wav_bytes = audio_to_wav_bytes(audio_data)
        recognizer = sr.Recognizer()
        audio_file = sr.AudioData(wav_bytes, SAMPLE_RATE, 2)
        text = recognizer.recognize_google(audio_file, language=lang_code)
        print(f"  YOU  : {text}")
        return text
    except sr.UnknownValueError:
        print("  [Could not understand speech -- please repeat]")
        return None
    except Exception as e:
        print(f"  [Microphone note: {e} -- switching to text prompt for this turn]")
        return input("  YOU (Type here) : ").strip() or None


def run_multilingual_agent(agent_key: str = "maya", mode: str = "voice"):
    agent_info = AGENTS.get(agent_key.lower(), AGENTS["maya"])
    agent_name = agent_info["name"]
    call_id = f"call_{agent_key}_{uuid.uuid4().hex[:8]}"
    thread_id = f"thread_{call_id}"
    config = {"configurable": {"thread_id": thread_id}}

    print()
    print("=" * 70)
    print(f"  {agent_name.upper()} -- {agent_info['sector']}")
    print(f"  Market & Language: {agent_info['id']} | {agent_info['language']}")
    print("=" * 70)
    print(f"  Call Session ID : {call_id}")
    print(f"  LLM Engine      : {settings.LLM_PROVIDER.upper()} ({settings.GEMINI_MODEL if settings.LLM_PROVIDER == 'gemini' else settings.GROQ_MODEL})")
    print(f"  Interaction Mode: {mode.upper()}")
    print("  Controls        : Type or say 'goodbye', 'quit', or 'exit' to end call")
    print("=" * 70)
    print()

    # Turn 0: Opening Greeting
    speak(agent_name, agent_info["opening"])

    while True:
        if mode == "voice":
            user_text = listen_microphone(agent_info["stt_lang"])
        else:
            try:
                user_text = input("\n  YOU : ").strip()
            except (KeyboardInterrupt, EOFError):
                break

        if not user_text:
            continue

        # Exit conditions
        if any(w in user_text.lower() for w in ["goodbye", "bye", "exit", "quit", "salamat", "terima kasih"]):
            speak(agent_name, agent_info["goodbye"])
            print(f"\n  [Call Ended Gracefully -- {agent_name}]\n")
            break

        turn_start = time.time()

        initial_state = {
            "messages": [HumanMessage(content=user_text)],
            "agent_name": agent_key.lower(),
            "call_id": call_id,
            "start_time": turn_start,
        }

        try:
            result = agent_app.invoke(initial_state, config=config)
            last_message = result["messages"][-1].content

            latency = result.get("turn_latency_ms", (time.time() - turn_start) * 1000)
            grounding = result.get("grounding_score", 1.0)
            in_action = result.get("guardrail_input_action", "allow")
            out_action = result.get("guardrail_output_action", "allow")

            print(f"  [TELEMETRY] Latency: {latency:.0f}ms | Grounding: {grounding:.2f} | Guardrails: In={in_action}, Out={out_action}")

            speak(agent_name, last_message)

        except Exception as e:
            print(f"  [Agent Exception: {e}]")
            speak(agent_name, "I apologize, could you please say that again?")


def main():
    parser = argparse.ArgumentParser(description="Run Multilingual Voice Agent (Maya or Dewi)")
    parser.add_argument(
        "--agent",
        choices=["maya", "dewi", "1", "2"],
        default="maya",
        help="Agent to run: 'maya' (Philippines Taglish) or 'dewi' (Indonesia Bahasa)",
    )
    parser.add_argument(
        "--mode",
        choices=["voice", "text"],
        default="text" if "--text" in sys.argv else "voice",
        help="Interaction mode: 'voice' (microphone) or 'text' (interactive keyboard)",
    )
    args = parser.parse_args()

    agent_key = "maya" if args.agent in ("maya", "1") else "dewi"
    run_multilingual_agent(agent_key=agent_key, mode=args.mode)


if __name__ == "__main__":
    main()
