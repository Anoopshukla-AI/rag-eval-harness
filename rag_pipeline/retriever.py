"""
rag_pipeline/retriever.py

Minimal standalone retriever: embeds a query, searches a local ChromaDB
collection, and returns ranked chunk IDs.
"""
from __future__ import annotations
import os
import sys

from dotenv import load_dotenv
import chromadb
from openai import OpenAI

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

NVIDIA_KEY = os.environ.get("NVIDIA_API_KEY")
OPENAI_KEY = os.environ.get("OPENAI_API_KEY")
NVIDIA_BASE_URL = os.environ.get("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "nvidia/nemotron-3-embed-1b" if NVIDIA_KEY else "text-embedding-3-small")

if NVIDIA_KEY:
    client = OpenAI(base_url=NVIDIA_BASE_URL, api_key=NVIDIA_KEY, timeout=45.0)
else:
    client = OpenAI(api_key=OPENAI_KEY, timeout=45.0)

CHROMA_PATH = os.path.join(os.path.dirname(__file__), "chroma_store")
COLLECTION_NAME = "eval_stub_docs"

_chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)


def _get_collection():
    return _chroma_client.get_or_create_collection(COLLECTION_NAME)


def embed_text(text: str) -> list[float]:
    response = client.embeddings.create(model=EMBEDDING_MODEL, input=text)
    return response.data[0].embedding


def retrieve(query: str, top_k: int = 5) -> list[str]:
    """
    Returns a ranked list of chunk IDs for the given query.
    """
    collection = _get_collection()
    query_embedding = embed_text(query)
    results = collection.query(query_embeddings=[query_embedding], n_results=top_k)
    return results["ids"][0] if results["ids"] else []


def get_chunk_text(chunk_id: str) -> str:
    """Fetch the raw text of a chunk by its ID, used by the generation judge."""
    collection = _get_collection()
    result = collection.get(ids=[chunk_id])
    if result["documents"]:
        return result["documents"][0]
    return ""
