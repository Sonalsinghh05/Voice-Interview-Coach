"""
rag.py
Loads the interview question bank into a Chroma vector store and exposes
a retrieval function that pulls role/category/difficulty-relevant questions.

Uses sentence-transformers for local, free embeddings (no API key needed).
"""

import json
import os
from pathlib import Path

import chromadb
from chromadb.utils import embedding_functions

# Locally: backend/rag.py -> ../data/questions.json
# In Docker: /app/rag.py -> /app/data/questions.json (data/ is volume-mounted there)
_LOCAL_PATH = Path(__file__).parent.parent / "data" / "questions.json"
_DOCKER_PATH = Path(__file__).parent / "data" / "questions.json"
DATA_PATH = _DOCKER_PATH if _DOCKER_PATH.exists() else _LOCAL_PATH
CHROMA_DIR = Path(__file__).parent / "chroma_store"

_embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)

_client = chromadb.PersistentClient(path=str(CHROMA_DIR))


def _load_questions():
    with open(DATA_PATH, "r") as f:
        return json.load(f)


def get_or_create_collection():
    collection = _client.get_or_create_collection(
        name="interview_questions",
        embedding_function=_embedding_fn,
    )
    # Only populate once
    if collection.count() == 0:
        questions = _load_questions()
        collection.add(
            ids=[q["id"] for q in questions],
            documents=[q["question"] for q in questions],
            metadatas=[
                {
                    "role": q["role"],
                    "category": q["category"],
                    "difficulty": q["difficulty"],
                }
                for q in questions
            ],
        )
    return collection


def retrieve_questions(role: str, category: str = None, difficulty: str = None, n: int = 5):
    """
    Retrieve questions relevant to a role (optionally filtered by category/difficulty).
    role: 'general', 'SDE', 'Data Analyst', 'ML Engineer'
    """
    collection = get_or_create_collection()

    where_clause = {"role": {"$in": [role, "general"]}}
    if category:
        where_clause = {"$and": [where_clause, {"category": category}]}
    if difficulty:
        where_clause = {"$and": [where_clause, {"difficulty": difficulty}]}

    results = collection.query(
        query_texts=[f"{role} interview question"],
        n_results=n,
        where=where_clause,
    )

    questions = []
    for i in range(len(results["ids"][0])):
        questions.append(
            {
                "id": results["ids"][0][i],
                "question": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
            }
        )
    return questions


def search_by_jd(job_description: str, n: int = 5):
    """Retrieve questions semantically closest to a pasted job description."""
    collection = get_or_create_collection()
    results = collection.query(query_texts=[job_description], n_results=n)
    questions = []
    for i in range(len(results["ids"][0])):
        questions.append(
            {
                "id": results["ids"][0][i],
                "question": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
            }
        )
    return questions
