#!/usr/bin/env python3
"""Benchmark script comparing Moonshine vs Whisper API transcription speed.

Usage:
    python scripts/benchmark.py [--audio-file PATH] [--duration SECONDS]

This script generates test audio (or uses a provided file) and measures
transcription time for each available engine.

Requirements:
    - Moonshine: pip install useful-moonshine-onnx
    - Whisper API: pip install openai + set OPENAI_API_KEY env var
"""

import argparse
import os
import sys
import time
from pathlib import Path

import numpy as np

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from claude_stt.engines.moonshine import MoonshineEngine
from claude_stt.engines.whisper_api import WhisperAPIEngine


def generate_test_audio(duration_seconds: float = 5.0, sample_rate: int = 16000) -> np.ndarray:
    """Generate test audio (silence with some noise to simulate real audio).

    In production benchmarks, you'd use real speech samples.
    """
    samples = int(duration_seconds * sample_rate)
    # Generate white noise as placeholder audio
    audio = np.random.randn(samples).astype(np.float32) * 0.1
    return audio


def load_audio_file(path: str, sample_rate: int = 16000) -> np.ndarray:
    """Load audio from a WAV file."""
    import wave

    with wave.open(path, "rb") as wav_file:
        assert wav_file.getnchannels() == 1, "Audio must be mono"
        assert wav_file.getframerate() == sample_rate, f"Sample rate must be {sample_rate}"

        frames = wav_file.readframes(wav_file.getnframes())
        audio = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0

    return audio


def benchmark_engine(engine, audio: np.ndarray, sample_rate: int, runs: int = 3) -> dict:
    """Benchmark an engine with multiple runs.

    Returns:
        dict with 'available', 'load_time', 'transcribe_times', 'avg_time', 'result'
    """
    result = {
        "available": False,
        "load_time": None,
        "transcribe_times": [],
        "avg_time": None,
        "result": None,
        "error": None,
    }

    if not engine.is_available():
        result["error"] = "Engine not available (missing dependencies or API key)"
        return result

    result["available"] = True

    # Benchmark model loading
    start = time.perf_counter()
    if not engine.load_model():
        result["error"] = "Failed to load model"
        return result
    result["load_time"] = time.perf_counter() - start

    # Benchmark transcription (multiple runs)
    for _ in range(runs):
        start = time.perf_counter()
        text = engine.transcribe(audio, sample_rate)
        elapsed = time.perf_counter() - start
        result["transcribe_times"].append(elapsed)
        if result["result"] is None:
            result["result"] = text

    result["avg_time"] = sum(result["transcribe_times"]) / len(result["transcribe_times"])
    return result


def print_results(name: str, results: dict, audio_duration: float):
    """Print formatted benchmark results."""
    print(f"\n{'=' * 50}")
    print(f"Engine: {name}")
    print("=" * 50)

    if not results["available"]:
        print(f"  Status: NOT AVAILABLE")
        print(f"  Reason: {results['error']}")
        return

    if results["error"]:
        print(f"  Status: ERROR - {results['error']}")
        return

    print(f"  Status: Available")
    print(f"  Model load time: {results['load_time']:.3f}s")
    print(f"  Transcription times: {[f'{t:.3f}s' for t in results['transcribe_times']]}")
    print(f"  Average time: {results['avg_time']:.3f}s")
    print(f"  Audio duration: {audio_duration:.1f}s")
    print(f"  Real-time factor: {results['avg_time'] / audio_duration:.2f}x")
    print(f"  Result preview: {(results['result'] or '')[:100]!r}")


def main():
    parser = argparse.ArgumentParser(description="Benchmark STT engines")
    parser.add_argument(
        "--audio-file",
        help="Path to WAV file (16kHz mono) to use for benchmarking",
    )
    parser.add_argument(
        "--duration",
        type=float,
        default=5.0,
        help="Duration in seconds for generated test audio (default: 5.0)",
    )
    parser.add_argument(
        "--runs",
        type=int,
        default=3,
        help="Number of transcription runs per engine (default: 3)",
    )
    args = parser.parse_args()

    print("STT Engine Benchmark")
    print("=" * 50)

    # Prepare audio
    if args.audio_file:
        print(f"Loading audio from: {args.audio_file}")
        audio = load_audio_file(args.audio_file)
        audio_duration = len(audio) / 16000
    else:
        print(f"Generating {args.duration}s of test audio (white noise)")
        print("  Note: For meaningful benchmarks, provide a real speech WAV file")
        audio = generate_test_audio(args.duration)
        audio_duration = args.duration

    print(f"Audio duration: {audio_duration:.1f}s")
    print(f"Runs per engine: {args.runs}")

    # Initialize engines
    engines = {
        "Moonshine (moonshine/base)": MoonshineEngine(model_name="moonshine/base"),
        "Whisper API (whisper-1)": WhisperAPIEngine(),
    }

    # Check API key for Whisper API
    if not os.environ.get("OPENAI_API_KEY"):
        print("\nNote: OPENAI_API_KEY not set. Whisper API benchmark will be skipped.")

    # Run benchmarks
    results = {}
    for name, engine in engines.items():
        print(f"\nBenchmarking {name}...")
        results[name] = benchmark_engine(engine, audio, 16000, args.runs)
        print_results(name, results[name], audio_duration)

    # Summary comparison
    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)

    available_engines = [(n, r) for n, r in results.items() if r["available"] and r["avg_time"]]

    if len(available_engines) >= 2:
        sorted_engines = sorted(available_engines, key=lambda x: x[1]["avg_time"])
        fastest_name, fastest_results = sorted_engines[0]
        print(f"\nFastest engine: {fastest_name}")
        print(f"  Average time: {fastest_results['avg_time']:.3f}s")
        print(f"  Real-time factor: {fastest_results['avg_time'] / audio_duration:.2f}x")

        print("\nSpeed comparison:")
        for name, r in sorted_engines:
            relative = r["avg_time"] / fastest_results["avg_time"]
            print(f"  {name}: {relative:.2f}x (avg {r['avg_time']:.3f}s)")
    elif len(available_engines) == 1:
        name, r = available_engines[0]
        print(f"\nOnly one engine available: {name}")
        print(f"  Average time: {r['avg_time']:.3f}s")
    else:
        print("\nNo engines available for benchmarking.")
        print("Install dependencies:")
        print("  - Moonshine: pip install useful-moonshine-onnx")
        print("  - Whisper API: pip install openai && export OPENAI_API_KEY=your-key")


if __name__ == "__main__":
    main()
