"""
app.py
Streamlit frontend for the Voice Interview Prep Coach.
Talks to the FastAPI backend over HTTP.
"""

import os
import uuid

import requests
import streamlit as st
from audio_recorder_streamlit import audio_recorder

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.set_page_config(page_title="Voice Interview Prep Coach", page_icon="🎙️", layout="centered")

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "current_question" not in st.session_state:
    st.session_state.current_question = None

st.title("🎙️ Voice Interview Prep Coach")
st.caption("Practice out loud. Get instant AI feedback on content, structure, and delivery.")

with st.sidebar:
    st.header("Session Setup")
    role = st.selectbox("Target role", ["general", "SDE", "Data Analyst", "ML Engineer"])
    category = st.selectbox("Question type", [None, "behavioral", "technical"], format_func=lambda x: "Any" if x is None else x)
    difficulty = st.selectbox("Difficulty", [None, "easy", "medium", "hard"], format_func=lambda x: "Any" if x is None else x)

    if st.button("Get a Question", use_container_width=True):
        params = {"role": role, "n": 1}
        if category:
            params["category"] = category
        if difficulty:
            params["difficulty"] = difficulty
        resp = requests.get(f"{BACKEND_URL}/questions", params=params)
        if resp.ok and resp.json()["questions"]:
            st.session_state.current_question = resp.json()["questions"][0]
        else:
            st.warning("No matching questions found — try different filters.")

    st.divider()
    if st.button("View Session Summary", use_container_width=True):
        summary = requests.get(f"{BACKEND_URL}/session/{st.session_state.session_id}/summary").json()
        st.metric("Questions answered", summary.get("total_questions", 0))
        st.metric("Average score", summary.get("average_score", "-"))
        st.metric("Average WPM", summary.get("average_wpm", "-"))

# Main panel
if st.session_state.current_question:
    q = st.session_state.current_question
    st.subheader("Question")
    st.info(q["question"])
    st.caption(f"Role: {q['metadata']['role']} · Category: {q['metadata']['category']} · Difficulty: {q['metadata']['difficulty']}")

    st.subheader("Your Answer")
    st.write("Record your spoken answer below:")
    audio_bytes = audio_recorder(text="Click to record", icon_size="2x")

    if audio_bytes:
        st.audio(audio_bytes, format="audio/wav")
        if st.button("Submit for Feedback", type="primary"):
            with st.spinner("Transcribing and generating feedback..."):
                files = {"audio": ("answer.wav", audio_bytes, "audio/wav")}
                data = {
                    "question_id": q["id"],
                    "question": q["question"],
                    "role": role,
                    "category": q["metadata"]["category"],
                    "session_id": st.session_state.session_id,
                }
                resp = requests.post(f"{BACKEND_URL}/answer", files=files, data=data)

            if resp.ok:
                result = resp.json()
                transcription = result["transcription"]
                feedback = result["feedback"]

                st.subheader("Transcript")
                st.write(transcription["transcript"])
                st.caption(f"{transcription['word_count']} words · {transcription['words_per_minute']} wpm · {transcription['duration_seconds']}s")

                st.subheader("Feedback")
                if feedback.get("score") is not None:
                    st.metric("Score", f"{feedback['score']}/10")
                st.markdown(f"**Structure:** {feedback.get('structure_feedback', '')}")
                st.markdown(f"**Content:** {feedback.get('content_feedback', '')}")
                st.markdown(f"**Delivery:** {feedback.get('delivery_feedback', '')}")

                if feedback.get("improvements"):
                    st.markdown("**Improvements:**")
                    for imp in feedback["improvements"]:
                        st.markdown(f"- {imp}")

                if feedback.get("model_answer"):
                    with st.expander("See a model answer"):
                        st.write(feedback["model_answer"])
            else:
                st.error(f"Something went wrong: {resp.text}")
else:
    st.write("👈 Pick a role and click **Get a Question** to start practicing.")
