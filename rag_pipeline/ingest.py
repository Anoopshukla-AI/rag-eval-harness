"""
rag_pipeline/ingest.py

One-time script to populate the ChromaDB collection with sample
documents, so the eval harness has something real to query against.
Run: python rag_pipeline/ingest.py
"""
from __future__ import annotations
import os
import sys

from dotenv import load_dotenv
import chromadb
from openai import OpenAI

# Ensure project root is in sys.path and load .env
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

NVIDIA_KEY = os.environ.get("NVIDIA_API_KEY")
OPENAI_KEY = os.environ.get("OPENAI_API_KEY")
NVIDIA_BASE_URL = os.environ.get("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "nvidia/nemotron-3-embed-1b" if NVIDIA_KEY else "text-embedding-3-small")

if NVIDIA_KEY:
    client = OpenAI(base_url=NVIDIA_BASE_URL, api_key=NVIDIA_KEY)
else:
    client = OpenAI(api_key=OPENAI_KEY)

CHROMA_PATH = os.path.join(os.path.dirname(__file__), "chroma_store")
COLLECTION_NAME = "eval_stub_docs"

# Sample HR-policy-style chunks matching the test_set.json questions.
SAMPLE_CHUNKS = {
    "chunk_001": "Employees must provide 30 days written notice before resignation. Contractors must provide 15 days notice as per their engagement terms.",
    "chunk_002": "Full-time employees are entitled to 18 days of paid annual leave, with up to 5 days eligible for carry-forward to the next calendar year.",
    "chunk_003": "Contractors are entitled to 12 days of paid annual leave per year, with no carry-forward permitted under the standard contractor agreement.",
    "chunk_004": "To submit an expense reimbursement claim, employees must upload receipts to the finance portal within 30 days of the expense and obtain manager approval.",
    "chunk_005": "Employees on probation who wish to resign must provide 7 days written notice, shorter than the standard 30-day period, and remain eligible for prorated leave accrued during probation.",
}


def main() -> None:
    chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = chroma_client.get_or_create_collection(COLLECTION_NAME)

    ids = list(SAMPLE_CHUNKS.keys())
    documents = list(SAMPLE_CHUNKS.values())
    embeddings = [
        client.embeddings.create(model=EMBEDDING_MODEL, input=doc).data[0].embedding
        for doc in documents
    ]

    collection.upsert(ids=ids, documents=documents, embeddings=embeddings)
    print(f"Ingested {len(ids)} sample chunks into '{COLLECTION_NAME}' at {CHROMA_PATH} using {EMBEDDING_MODEL}")


if __name__ == "__main__":
    main()
