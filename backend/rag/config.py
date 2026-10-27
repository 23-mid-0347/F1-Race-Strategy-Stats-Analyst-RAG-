"""Configuration for the local Ollama + Chroma RAG pipeline."""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# config.py lives in <repo>/backend/rag/config.py
REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = REPO_ROOT / "backend"

# Support either a repo-root .env or the backend/.env used by some local setups.
load_dotenv(REPO_ROOT / ".env", override=False)
load_dotenv(BACKEND_DIR / ".env", override=False)

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
OLLAMA_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "embeddinggemma")
OLLAMA_CHAT_MODEL = os.getenv("OLLAMA_CHAT_MODEL", "llama3.2")
OLLAMA_TIMEOUT_SECONDS = float(os.getenv("OLLAMA_TIMEOUT_SECONDS", "180"))

_raw_chroma_path = Path(os.getenv("CHROMA_PATH", "backend/rag/chroma_db"))
CHROMA_PATH = _raw_chroma_path if _raw_chroma_path.is_absolute() else REPO_ROOT / _raw_chroma_path
CHROMA_COLLECTION_NAME = os.getenv("CHROMA_COLLECTION_NAME", "f1_race_reports")
DEFAULT_SEASON = int(os.getenv("F1_DEFAULT_SEASON", "2023"))
DEFAULT_TOP_K = int(os.getenv("RAG_TOP_K", "5"))
