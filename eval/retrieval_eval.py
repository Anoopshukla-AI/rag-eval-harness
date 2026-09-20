"""
Retrieval evaluation for the RAG pipeline.
Imports the existing retrieval function from the parent RAG project —
does not duplicate chunking/embedding/retrieval logic.
"""
from __future__ import annotations
from dataclasses import dataclass
import sys
import os

# Ensure parent and eval directories are in sys.path
EVAL_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(EVAL_DIR)
if EVAL_DIR not in sys.path:
    sys.path.insert(0, EVAL_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from rag_pipeline.retriever import retrieve  # type: ignore


@dataclass
class RetrievalResult:
    question_id: str
    hit_at_5: bool
    reciprocal_rank: float
    retrieved_ids: list[str]


def hit_at_k(retrieved_ids: list[str], correct_ids: list[str], k: int = 5) -> bool:
    """True if any correct chunk ID appears in the top-k retrieved results."""
    return any(cid in retrieved_ids[:k] for cid in correct_ids)


def reciprocal_rank(retrieved_ids: list[str], correct_ids: list[str]) -> float:
    """1/rank of the first correct chunk found; 0.0 if none found."""
    for i, rid in enumerate(retrieved_ids, start=1):
        if rid in correct_ids:
            return 1 / i
    return 0.0


def evaluate_retrieval(test_set: list[dict], top_k: int = 5) -> list[RetrievalResult]:
    """Run retrieval for every test question and score it."""
    results: list[RetrievalResult] = []
    for item in test_set:
        if item["category"] == "out_of_scope":
            continue  # retrieval scoring doesn't apply to out-of-scope questions
        retrieved_ids = retrieve(item["question"], top_k=top_k)
        results.append(
            RetrievalResult(
                question_id=item["id"],
                hit_at_5=hit_at_k(retrieved_ids, item["source_chunk_ids"], k=top_k),
                reciprocal_rank=reciprocal_rank(retrieved_ids, item["source_chunk_ids"]),
                retrieved_ids=retrieved_ids,
            )
        )
    return results


def summarize_retrieval(results: list[RetrievalResult]) -> dict:
    if not results:
        return {"hit_at_5": 0.0, "mrr": 0.0, "n": 0}
    hit_rate = sum(r.hit_at_5 for r in results) / len(results)
    mrr = sum(r.reciprocal_rank for r in results) / len(results)
    return {"hit_at_5": round(hit_rate, 3), "mrr": round(mrr, 3), "n": len(results)}
