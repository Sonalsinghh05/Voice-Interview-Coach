"""
main.py
FastAPI backend for the Voice-Based Interview Prep Coach.

Endpoints:
  GET  /questions          -> retrieve questions by role/category/difficulty
  POST /questions/by-jd    -> retrieve questions matched to a pasted job description
  POST /answer              -> upload audio for a question, get transcript + feedback
  GET  /session/{id}/history
  GET  /session/{id}/summary
"""

import json
import shutil
import uuid
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from rag import retrieve_questions, search_by_jd
from transcribe import transcribe_audio
from feedback import get_feedback
from db import init_db, save_attempt, get_session_history, get_session_summary

app = FastAPI(title="Voice Interview Prep Coach API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten this in production
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = Path(__file__).parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

init_db()


@app.get("/")
def root():
    return {"status": "ok", "service": "voice-interview-coach"}


@app.get("/questions")
def get_questions(role: str = "general", category: str = None, difficulty: str = None, n: int = 5):
    questions = retrieve_questions(role=role, category=category, difficulty=difficulty, n=n)
    return {"questions": questions}


@app.post("/questions/by-jd")
def get_questions_by_jd(job_description: str = Form(...), n: int = Form(5)):
    questions = search_by_jd(job_description, n=n)
    return {"questions": questions}


@app.post("/answer")
async def submit_answer(
    question_id: str = Form(...),
    question: str = Form(...),
    role: str = Form("general"),
    category: str = Form("behavioral"),
    session_id: str = Form(None),
    audio: UploadFile = File(...),
):
    if not session_id:
        session_id = str(uuid.uuid4())

    # Save uploaded audio temporarily
    temp_path = UPLOAD_DIR / f"{uuid.uuid4()}_{audio.filename}"
    with open(temp_path, "wb") as f:
        shutil.copyfileobj(audio.file, f)

    try:
        transcription = transcribe_audio(str(temp_path))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {e}")
    finally:
        temp_path.unlink(missing_ok=True)

    feedback = get_feedback(
        question=question, transcript=transcription["transcript"], category=category
    )

    save_attempt(
        session_id=session_id,
        question_id=question_id,
        question=question,
        role=role,
        transcript=transcription["transcript"],
        wpm=transcription["words_per_minute"],
        score=feedback.get("score"),
        feedback_json=json.dumps(feedback),
    )

    return {
        "session_id": session_id,
        "transcription": transcription,
        "feedback": feedback,
    }


@app.get("/session/{session_id}/history")
def session_history(session_id: str):
    return {"history": get_session_history(session_id)}


@app.get("/session/{session_id}/summary")
def session_summary(session_id: str):
    return get_session_summary(session_id)
