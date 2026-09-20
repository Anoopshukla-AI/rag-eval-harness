"""
Generation evaluation using an LLM-as-judge.
Scores groundedness, correctness, and refusal accuracy for RAG-generated answers.
Supports NVIDIA NIM and OpenAI endpoints.
"""
from __future__ import annotations
import json
import time
import os
import sys
from dataclasses import dataclass

from dotenv import load_dotenv

# Ensure parent and eval directories are in sys.path
EVAL_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(EVAL_DIR)
if EVAL_DIR not in sys.path:
    sys.path.insert(0, EVAL_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

from rag_pipeline.generator import generate_answer  # type: ignore
from rag_pipeline.retriever import get_chunk_text  # type: ignore
from openai import OpenAI

# Detect NVIDIA NIM or OpenAI credentials
NVIDIA_KEY = os.environ.get("NVIDIA_API_KEY")
OPENAI_KEY = os.environ.get("OPENAI_API_KEY")
NVIDIA_BASE_URL = os.environ.get("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")

if NVIDIA_KEY:
    client = OpenAI(base_url=NVIDIA_BASE_URL, api_key=NVIDIA_KEY, timeout=45.0)
    JUDGE_MODEL = os.environ.get("JUDGE_MODEL", "meta/llama-3.2-11b-vision-instruct")
else:
    client = OpenAI(api_key=OPENAI_KEY, timeout=45.0)
    JUDGE_MODEL = os.environ.get("JUDGE_MODEL", "gpt-4o-mini")

JUDGE_PROMPT = """You are evaluating a RAG system's answer.

Source text: {retrieved_text}
Question: {question}
Generated answer: {generated_answer}
Expected answer: {expected_answer}

Score the generated answer on:
1. Groundedness: Is every claim in the answer directly supported by the source text? (SUPPORTED / PARTIALLY_SUPPORTED / UNSUPPORTED)
2. Correctness: Does it convey the same meaning as the expected answer? (CORRECT / PARTIALLY_CORRECT / INCORRECT)

For out-of-scope questions (expected_answer is null), the correct behavior is refusal.
Score refusal_check as REFUSAL_CORRECT if the model declined appropriately,
REFUSAL_MISSING if it hallucinated an answer instead, or null if not applicable.

Respond ONLY with valid JSON in this exact shape:
{{"groundedness": "...", "correctness": "...", "refusal_check": "..." }}
"""


@dataclass
class GenerationResult:
    question_id: str
    generated_answer: str
    groundedness: str
    correctness: str
    refusal_check: str | None
    tokens_used: int
    latency_ms: float


def judge_answer(question: str, retrieved_text: str, generated_answer: str, expected_answer: str | None) -> dict:
    prompt = JUDGE_PROMPT.format(
        retrieved_text=retrieved_text,
        question=question,
        generated_answer=generated_answer,
        expected_answer=expected_answer or "N/A (out-of-scope question)",
    )
    response = client.chat.completions.create(
        model=JUDGE_MODEL,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=0,
    )
    return json.loads(response.choices[0].message.content)


def evaluate_generation(test_set: list[dict], retrieval_map: dict[str, list[str]]) -> list[GenerationResult]:
    results: list[GenerationResult] = []
    for i, item in enumerate(test_set, 1):
        print(f"  [{i}/{len(test_set)}] Generating & judging question {item['id']}...", flush=True)
        retrieved_ids = retrieval_map.get(item["id"], [])
        retrieved_text = "\n".join(get_chunk_text(cid) for cid in retrieved_ids)

        start = time.time()
        answer = generate_answer(item["question"], retrieved_ids)
        latency_ms = (time.time() - start) * 1000

        judge_result = judge_answer(
            question=item["question"],
            retrieved_text=retrieved_text,
            generated_answer=answer,
            expected_answer=item["expected_answer"],
        )

        refusal = judge_result.get("refusal_check")
        if refusal in ("null", "None", "", None):
            refusal = None

        results.append(
            GenerationResult(
                question_id=item["id"],
                generated_answer=answer,
                groundedness=judge_result.get("groundedness", "UNKNOWN"),
                correctness=judge_result.get("correctness", "UNKNOWN"),
                refusal_check=refusal,
                tokens_used=0,
                latency_ms=round(latency_ms, 1),
            )
        )
    return results


def summarize_generation(results: list[GenerationResult]) -> dict:
    n = len(results) or 1
    pct_supported = sum(r.groundedness == "SUPPORTED" for r in results) / n
    pct_correct = sum(r.correctness == "CORRECT" for r in results) / n
    refusal_items = [r for r in results if r.refusal_check is not None]
    pct_refusal_correct = (
        sum(r.refusal_check == "REFUSAL_CORRECT" for r in refusal_items) / len(refusal_items)
        if refusal_items else None
    )
    avg_latency = sum(r.latency_ms for r in results) / n
    return {
        "pct_supported": round(pct_supported, 3),
        "pct_correct": round(pct_correct, 3),
        "pct_refusal_correct": round(pct_refusal_correct, 3) if pct_refusal_correct is not None else "N/A",
        "avg_latency_ms": round(avg_latency, 1),
    }
