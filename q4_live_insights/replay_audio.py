"""
Q4 - Live Insights: Real-Time Audio Replay Simulator
Reads a WAV file and streams it at real-time speed (20ms chunks) to the pipeline.
This simulates a live call for demonstration purposes.

Usage:
    python replay_audio.py --file path/to/call.wav --call-id demo-001 --server ws://localhost:8001
"""

import argparse
import asyncio
import sys
import time
import wave
from pathlib import Path

import websockets


CHUNK_MS = 20          # 20ms chunks — simulates real-time audio frames
SAMPLE_RATE = 16000    # Must match pipeline config
CHANNELS = 1
SAMPLE_WIDTH = 2       # 16-bit PCM = 2 bytes per sample


def validate_wav(file_path: Path) -> wave.Wave_read:
    """Open and validate a WAV file against expected format."""
    try:
        wf = wave.open(str(file_path), "rb")
    except FileNotFoundError:
        print(f"[error] File not found: {file_path}")
        sys.exit(1)

    if wf.getsampwidth() != SAMPLE_WIDTH:
        print(f"[warn] Expected 16-bit PCM, got {wf.getsampwidth() * 8}-bit. Proceeding anyway.")
    if wf.getframerate() != SAMPLE_RATE:
        print(f"[warn] Expected {SAMPLE_RATE}Hz, got {wf.getframerate()}Hz. Pipeline may reject audio.")
    if wf.getnchannels() != CHANNELS:
        print(f"[warn] Expected mono audio, got {wf.getnchannels()} channels.")

    return wf


async def replay_audio(wav_path: Path, call_id: str, server_url: str):
    """Stream WAV audio to the pipeline WebSocket at real-time speed."""
    wf = validate_wav(wav_path)

    frames_per_chunk = int(SAMPLE_RATE * CHUNK_MS / 1000)
    bytes_per_chunk = frames_per_chunk * SAMPLE_WIDTH * CHANNELS
    total_frames = wf.getnframes()
    duration_s = total_frames / SAMPLE_RATE

    ws_url = f"{server_url}/ws/audio/{call_id}"
    print(f"[replay] File: {wav_path.name}")
    print(f"[replay] Duration: {duration_s:.1f}s | Chunk size: {bytes_per_chunk} bytes ({CHUNK_MS}ms)")
    print(f"[replay] Connecting to: {ws_url}")

    async with websockets.connect(ws_url) as ws:
        print(f"[replay] ✅ Connected. Starting real-time replay...")
        start_time = time.time()
        chunks_sent = 0

        while True:
            frames = wf.readframes(frames_per_chunk)
            if not frames:
                break  # End of file

            await ws.send(frames)
            chunks_sent += 1
            elapsed = time.time() - start_time
            expected_elapsed = chunks_sent * CHUNK_MS / 1000

            # Throttle to real-time speed
            drift = expected_elapsed - elapsed
            if drift > 0.002:  # Sleep if we're ahead of real-time
                await asyncio.sleep(drift)

            # Progress indicator
            if chunks_sent % 50 == 0:
                progress = (chunks_sent * frames_per_chunk / total_frames) * 100
                print(f"[replay] Progress: {progress:.0f}% | {chunks_sent * CHUNK_MS / 1000:.1f}s elapsed")

        wf.close()
        actual_duration = time.time() - start_time
        print(f"\n[replay] ✅ Replay complete.")
        print(f"[replay] Audio duration: {duration_s:.1f}s | Actual replay time: {actual_duration:.1f}s")
        print(f"[replay] Playback speed ratio: {duration_s / actual_duration:.2f}x (target: 1.0x)")

        # Send close signal to pipeline
        await ws.close()


def generate_test_audio(output_path: Path, duration_s: int = 60):
    """
    Generate a simple silence WAV file for testing when no real recording is available.
    Replace this with actual call recordings for the assessment.
    """
    import struct
    import math

    print(f"[test_audio] Generating {duration_s}s test tone at {output_path}")
    total_frames = SAMPLE_RATE * duration_s
    with wave.open(str(output_path), "wb") as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(SAMPLE_WIDTH)
        wf.setframerate(SAMPLE_RATE)
        # Generate a low-frequency tone (200Hz) to simulate audio activity
        for i in range(total_frames):
            value = int(1000 * math.sin(2 * math.pi * 200 * i / SAMPLE_RATE))
            wf.writeframes(struct.pack("<h", value))
    print(f"[test_audio] ✅ Generated: {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Replay WAV audio at real-time speed to Q4 pipeline")
    parser.add_argument("--file", type=str, help="Path to WAV file (16kHz, 16-bit, mono)")
    parser.add_argument("--call-id", type=str, default=f"replay-{int(time.time())}")
    parser.add_argument("--server", type=str, default="ws://localhost:8001")
    parser.add_argument("--generate-test", action="store_true", help="Generate a test audio file and replay it")
    args = parser.parse_args()

    if args.generate_test:
        test_path = Path("test_call_audio.wav")
        generate_test_audio(test_path, duration_s=90)
        args.file = str(test_path)

    if not args.file:
        print("[error] Provide --file path/to/call.wav or use --generate-test")
        sys.exit(1)

    wav_path = Path(args.file)
    asyncio.run(replay_audio(wav_path, args.call_id, args.server))
