"""
feedback.py
Generates structured interview feedback from a (question, transcript) pair.

Two modes:
  - "cloud": uses the Anthropic Claude API (requires ANTHROPIC_API_KEY)
  - "local": uses a local model via Ollama (requires Ollama running locally)

Mode is chosen via the FEEDBACK_MODE env var, defaulting to "cloud".
"""

import json
import os

FEEDBACK_MODE = os.getenv("FEEDBACK_MODE", "cloud")  # "cloud" or "local"
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1")
# Inside Docker, "localhost" refers to the container itself, not the host machine.
# host.docker.internal is Docker's special DNS name for reaching the host OS.
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://host.docker.internal:11434")

SYSTEM_PROMPT = """You are an expert technical and behavioral interview coach.
Given an interview question and a candidate's spoken (transcribed) answer,
evaluate the answer and return ONLY valid JSON with this exact structure,
no markdown fences, no preamble:

{
  "score": <integer 1-10>,
  "structure_feedback": "<1-2 sentences on structure, e.g. STAR method for behavioral questions>",
  "content_feedback": "<1-2 sentences on correctness/depth of content>",
  "delivery_feedback": "<1-2 sentences on clarity, filler words, conciseness, based on the transcript text itself>",
  "improvements": ["<specific tip 1>", "<specific tip 2>"],
  "model_answer": "<a concise strong example answer, 3-5 sentences>"
}
"""


def _build_user_prompt(question: str, transcript: str, category: str) -> str:
    return f"""Interview question ({category}): {question}

Candidate's transcribed answer:
\"\"\"{transcript}\"\"\"

Evaluate this answer and return the JSON as specified."""


def _parse_json_response(text: str) -> dict:
    cleaned = text.replace("```json", "").replace("```", "").strip()
    return json.loads(cleaned)


def _get_feedback_cloud(question: str, transcript: str, category: str) -> dict:
    import anthropic

    client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=800,
        system=SYSTEM_PROMPT,
        messages=[
            {"role": "user", "content": _build_user_prompt(question, transcript, category)}
        ],
    )
    text = "".join(
        block.text for block in message.content if getattr(block, "type", None) == "text"
    )
    return _parse_json_response(text)


def _get_feedback_local(question: str, transcript: str, category: str) -> dict:
    import requests

    response = requests.post(
        f"{OLLAMA_HOST}/api/chat",
        json={
            "model": OLLAMA_MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": _build_user_prompt(question, transcript, category)},
            ],
            "stream": False,
        },
        timeout=120,
    )
    response.raise_for_status()
    text = response.json()["message"]["content"]
    return _parse_json_response(text)


def get_feedback(question: str, transcript: str, category: str = "behavioral") -> dict:
    """
    Returns structured feedback dict. Falls back to a safe default
    if the LLM response can't be parsed, so the API never hard-fails.
    """
    try:
        if FEEDBACK_MODE == "local":
            return _get_feedback_local(question, transcript, category)
        return _get_feedback_cloud(question, transcript, category)
    except Exception as e:
        return {
            "score": None,
            "structure_feedback": "Feedback generation failed.",
            "content_feedback": "",
            "delivery_feedback": "",
            "improvements": [],
            "model_answer": "",
            "error": str(e),
        }
