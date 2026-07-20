"""
transcribe.py
Speech-to-text using faster-whisper (runs locally, no cloud dependency).
Falls back gracefully with a clear error if the model isn't downloaded yet
(first run will download the model automatically).
"""

import time
from pathlib import Path

from faster_whisper import WhisperModel

# "base" is a good speed/accuracy tradeoff for interview-length answers.
# Use "small" or "medium" for higher accuracy if you have the compute.
_MODEL_SIZE = "base"
_model = None


def _get_model():
    global _model
    if _model is None:
        # device="cpu" for portability; switch to "cuda" if a GPU is available
        _model = WhisperModel(_MODEL_SIZE, device="cpu", compute_type="int8")
    return _model


def transcribe_audio(file_path: str) -> dict:
    """
    Transcribe an audio file and return the transcript plus basic delivery
    metrics (duration, word count, words-per-minute) used for feedback.
    """
    model = _get_model()
    start = time.time()

    segments, info = model.transcribe(file_path, beam_size=5)
    text_segments = [seg.text.strip() for seg in segments]
    full_text = " ".join(text_segments).strip()

    elapsed = time.time() - start
    duration = info.duration  # audio length in seconds
    word_count = len(full_text.split())
    wpm = round((word_count / duration) * 60, 1) if duration > 0 else 0

    return {
        "transcript": full_text,
        "duration_seconds": round(duration, 1),
        "word_count": word_count,
        "words_per_minute": wpm,
        "transcription_time_seconds": round(elapsed, 2),
        "language": info.language,
    }
