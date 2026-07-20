#  Voice-Based Interview Prep Coach

An AI-powered interview practice platform that lets you **speak your answers out loud**
and get instant, structured feedback — combining speech-to-text, RAG-based question
retrieval, and LLM-driven evaluation.

Practice behavioral and technical interview questions the way real interviews actually
happen: verbally, under a little time pressure, with no do-overs mid-sentence.

---

##  Features

-  **Speak your answers** — record directly in the browser, transcribed locally via Whisper
-  **RAG-based question retrieval** — semantic search over a curated question bank by role, category, and difficulty (ChromaDB + sentence-transformers)
-  **Structured AI feedback** — scored on structure (STAR method), content accuracy, and delivery (pacing, clarity)
-  **Privacy-preserving local mode** — run transcription and feedback fully offline via `faster-whisper` + Ollama, no data leaves your machine
-  **Session tracking** — SQLite-backed history with average score and speaking-pace trends across a practice session
-  **One-command deploy** — Docker Compose spins up backend + frontend together

---

## Architecture

```
┌─────────────────┐      ┌──────────────────────┐      ┌───────────────────┐
│   Streamlit UI    │ ───► │   FastAPI Backend      │ ───► │   ChromaDB (RAG)    │
│  (record + view)  │      │                        │      │  question retrieval │
└─────────────────┘      │  ┌──────────────────┐  │      └───────────────────┘
                          │  │ faster-whisper    │  │
                          │  │ (speech-to-text)  │  │      ┌───────────────────┐
                          │  └──────────────────┘  │ ───► │  Claude API /       │
                          │  ┌──────────────────┐  │      │  Ollama (feedback)  │
                          │  │ SQLite            │  │      └───────────────────┘
                          │  │ (session history) │  │
                          │  └──────────────────┘  │
                          └──────────────────────┘
```

**Flow:** pick a role → retrieve a relevant question via RAG → record your spoken
answer → Whisper transcribes it → the transcript + question go to the LLM → structured
feedback comes back and gets saved to your session history.

---

## Tech Stack

| Layer | Tech |
|---|---|
| Backend | FastAPI, Python |
| Speech-to-Text | faster-whisper |
| Vector Search / RAG | ChromaDB, sentence-transformers |
| LLM Feedback | Claude API (default) or Ollama (local mode) |
| Session Storage | SQLite |
| Frontend | Streamlit |
| Deployment | Docker, Docker Compose |

---

## Getting Started

### Option A: Docker (recommended)

1. Clone the repo:
   ```bash
   git clone https://github.com/<your-username>/voice-interview-coach.git
   cd voice-interview-coach
   ```

2. Set up environment variables:
   ```bash
   cp .env.example .env
   # then edit .env and add your ANTHROPIC_API_KEY
   ```

3. Run it:
   ```bash
   docker compose up --build
   ```

4. Open the app:
   - Frontend: http://localhost:8501
   - Backend API docs: http://localhost:8000/docs

### Option B: Run locally without Docker

**Backend:**
```bash
cd backend
python -m venv venv && source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
export ANTHROPIC_API_KEY=your_key_here
uvicorn main:app --reload
```

**Frontend** (in a second terminal):
```bash
cd frontend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

### Running fully offline (no cloud API, no API key)

1. Install [Ollama](https://ollama.com) and pull a model:
   ```bash
   ollama pull llama3.1
   ```
2. Set `FEEDBACK_MODE=local` in your `.env` (or export it before running).
3. Whisper transcription is already local by default — no extra setup needed.

---

## Project Structure

```
voice-interview-coach/
├── backend/
│   ├── main.py           # FastAPI app & routes
│   ├── rag.py             # ChromaDB question retrieval
│   ├── transcribe.py      # Whisper speech-to-text
│   ├── feedback.py        # LLM feedback generation (cloud or local)
│   ├── db.py               # SQLite session tracking
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── app.py              # Streamlit UI
│   ├── requirements.txt
│   └── Dockerfile
├── data/
│   └── questions.json     # Curated interview question bank
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## API Reference

| Endpoint | Method | Description |
|---|---|---|
| `/questions` | GET | Retrieve questions by role/category/difficulty |
| `/questions/by-jd` | POST | Retrieve questions matched to a pasted job description |
| `/answer` | POST | Upload an audio answer, get transcript + feedback |
| `/session/{id}/history` | GET | Full history of a practice session |
| `/session/{id}/summary` | GET | Average score & speaking pace for a session |

Full interactive docs available at `/docs` once the backend is running.

---

## Roadmap

- [ ] Text-to-speech so questions are read aloud (interview-realistic)
- [ ] Auto-generate targeted questions from an uploaded job description
- [ ] Filler-word and pause detection for richer delivery feedback
- [ ] Multi-question mock interview mode with a final composite report
- [ ] User accounts + persistent history across devices

---
