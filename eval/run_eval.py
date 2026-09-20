"""
Regression runner for the RAG evaluation harness.
Run with: python eval/run_eval.py
"""
from __future__ import annotations
import json
import glob
import os
import sys
from datetime import datetime

import pandas as pd

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Ensure eval directory and project root are in sys.path
EVAL_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(EVAL_DIR)
if EVAL_DIR not in sys.path:
    sys.path.insert(0, EVAL_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from retrieval_eval import evaluate_retrieval, summarize_retrieval
from generation_eval import evaluate_generation, summarize_generation

TEST_SET_PATH = os.path.join(EVAL_DIR, "test_set.json")
RESULTS_DIR = os.path.join(EVAL_DIR, "results")


def load_test_set() -> list[dict]:
    with open(TEST_SET_PATH, "r") as f:
        return json.load(f)


def get_previous_run() -> dict | None:
    os.makedirs(RESULTS_DIR, exist_ok=True)
    runs = sorted(glob.glob(os.path.join(RESULTS_DIR, "summary_*.json")))
    if not runs:
        return None
    with open(runs[-1], "r") as f:
        return json.load(f)


def print_diff(current: dict, previous: dict | None) -> None:
    if previous is None:
        print("\n(No previous run found -- this is the baseline.)")
        return
    print("\n--- Regression Diff vs Previous Run ---")
    for key in ["hit_at_5", "mrr", "pct_supported", "pct_correct"]:
        if key in current and key in previous:
            delta = current[key] - previous[key]
            arrow = "(+)" if delta > 0 else ("(-)" if delta < 0 else "(=)")
            print(f"{key}: {previous[key]} -> {current[key]}  {arrow}{abs(round(delta, 3))}")


def main() -> None:
    test_set = load_test_set()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    print(f"Running evaluation on {len(test_set)} test questions...")

    retrieval_results = evaluate_retrieval(test_set)
    retrieval_summary = summarize_retrieval(retrieval_results)
    retrieval_map = {r.question_id: r.retrieved_ids for r in retrieval_results}

    generation_results = evaluate_generation(test_set, retrieval_map)
    generation_summary = summarize_generation(generation_results)

    summary = {**retrieval_summary, **generation_summary, "timestamp": timestamp}

    print("\n--- Retrieval Quality ---")
    print(f"Hit@5: {retrieval_summary['hit_at_5']}   MRR: {retrieval_summary['mrr']}")

    print("\n--- Generation Quality ---")
    print(f"Supported: {generation_summary['pct_supported']*100:.1f}%")
    print(f"Correct: {generation_summary['pct_correct']*100:.1f}%")
    print(f"Refusal Correct (out-of-scope): {generation_summary['pct_refusal_correct']}")
    print(f"Avg Latency: {generation_summary['avg_latency_ms']} ms")

    previous = get_previous_run()
    print_diff(summary, previous)

    os.makedirs(RESULTS_DIR, exist_ok=True)
    pd.DataFrame([
        {"question_id": r.question_id, "hit_at_5": r.hit_at_5, "reciprocal_rank": r.reciprocal_rank}
        for r in retrieval_results
    ]).to_csv(os.path.join(RESULTS_DIR, f"retrieval_{timestamp}.csv"), index=False)

    pd.DataFrame([
        {
            "question_id": r.question_id,
            "generated_answer": r.generated_answer,
            "groundedness": r.groundedness,
            "correctness": r.correctness,
            "refusal_check": r.refusal_check,
            "latency_ms": r.latency_ms,
        }
        for r in generation_results
    ]).to_csv(os.path.join(RESULTS_DIR, f"generation_{timestamp}.csv"), index=False)

    with open(os.path.join(RESULTS_DIR, f"summary_{timestamp}.json"), "w") as f:
        json.dump(summary, f, indent=2)

    print(f"\nResults saved to {RESULTS_DIR}/ (timestamp: {timestamp})")


if __name__ == "__main__":
    main()
