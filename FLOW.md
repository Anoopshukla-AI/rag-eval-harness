# FLOW.md — RAG Evaluation Harness

## 1. End-to-End Execution Flow

```
┌─────────────────────┐
│  eval/test_set.json │  (20 labeled questions: factual / multi-doc / out-of-scope)
└──────────┬───────────┘
           │
           ▼
┌──────────────────────────────┐
│  run_eval.py (orchestrator)  │
└──────────┬────────────────────┘
           │
           ├─────────────────────────────┐
           ▼                             ▼
┌───────────────────────┐    ┌────────────────────────────┐
│  retrieval_eval.py     │    │  generation_eval.py         │
│                         │    │                              │
│  1. For each question   │    │  1. For each question        │
│     (skip out-of-scope):│    │     - Get retrieved chunks   │
│  2. Call retrieve()     │    │       (from retrieval step)  │
│     from existing RAG   │    │     - Call generate_answer() │
│     pipeline             │    │       from existing RAG      │
│  3. Compare retrieved    │    │       pipeline                │
│     chunk IDs vs.        │    │     - Time the call (latency)│
│     source_chunk_ids     │    │     - Send question+source+  │
│  4. Compute Hit@5,       │    │       answer to LLM judge    │
│     Reciprocal Rank      │    │       (GPT-4o-mini)          │
└──────────┬───────────────┘    │     - Parse groundedness,    │
           │                    │       correctness, refusal   │
           │                    │       check from judge JSON  │
           │                    └──────────┬────────────────────┘
           │                               │
           ▼                               ▼
┌────────────────────────────────────────────────────┐
│  run_eval.py aggregates both result sets:            │
│  - Compute summary stats (Hit@5, MRR, % Supported,   │
│    % Correct, % Refusal Correct, Avg Latency)         │
│  - Load most recent previous summary_*.json           │
│  - Print diff (▲/▼ per metric)                         │
│  - Write retrieval_{ts}.csv, generation_{ts}.csv,      │
│    summary_{ts}.json to eval/results/                 │
└────────────────────────────────────────────────────┘
           │
           ▼
┌────────────────────────────┐
│  Console output + CSV files │  ← what you show in the interview
└────────────────────────────┘
```

## 2. Per-Question Flow (Single Question Walkthrough)

```
Question: "Compare the leave policy for contractors vs full-time employees."
Category: multi_document

Step 1 — Retrieval
   query → embed → ChromaDB search → MMR re-rank → top-5 chunk IDs
   retrieved_ids = ["chunk_042", "chunk_017", "chunk_099", "chunk_003", "chunk_055"]

Step 2 — Retrieval Scoring
   source_chunk_ids = ["chunk_042", "chunk_017"]
   hit_at_5 = True   (both correct chunks are in top 5)
   reciprocal_rank = 1.0   (chunk_042 is rank 1)

Step 3 — Generation
   generate_answer(question, retrieved_ids) → GPT-4o
   → "Contractors get 12 days of leave per year with no carry-forward,
      while full-time employees get 18 days with up to 5 days carry-forward."

Step 4 — Generation Scoring (LLM-as-judge, GPT-4o-mini)
   judge_prompt(question, retrieved_text, generated_answer, expected_answer)
   → {"groundedness": "SUPPORTED", "correctness": "CORRECT", "refusal_check": null}

Step 5 — Record Result
   GenerationResult(
     question_id="q04", groundedness="SUPPORTED",
     correctness="CORRECT", latency_ms=1380.2
   )
```

## 3. Regression Check Flow (Comparing Two Runs)

```
Run A (baseline, before change)          Run B (after chunking size change)
────────────────────────────             ────────────────────────────
Hit@5: 0.75                              Hit@5: 0.86
MRR:   0.68                              MRR:   0.79
                    │                              │
                    └──────────────┬───────────────┘
                                   ▼
                   run_eval.py loads Run A's summary_*.json
                   as "previous", compares to Run B's fresh scores
                                   ▼
                   Console prints:
                   "hit_at_5: 0.75 → 0.86  (▲0.11)"
                   "mrr: 0.68 → 0.79  (▲0.11)"
                                   ▼
                   Conclusion: the chunking change improved retrieval —
                   safe to keep. If scores had dropped, the change
                   would be reverted before shipping.
```

## 4. Decision Points in the Flow

| Point | Decision | Why |
|---|---|---|
| After retrieval, before generation | Skip generation scoring only if you want faster/cheaper partial runs (retrieval-only debugging) | Lets you isolate a retrieval bug without spending on generation calls |
| Choosing judge model | GPT-4o-mini, not the same model being evaluated | Avoids self-grading bias and keeps eval cost low |
| Out-of-scope questions | Excluded from retrieval scoring, included in generation scoring (refusal check only) | Retrieval "correctly" finds nothing for these — the model's decision to refuse is what's being tested, not retrieval |
| No previous run found | Treated as baseline, no diff printed | First run establishes the reference point for all future comparisons |

## 5. How to Read This If You're an Interviewer (or Practicing Explaining It)

"A question comes in, gets retrieved and scored for Hit@5/MRR, then gets generated and scored by a second, cheaper LLM acting as a judge for groundedness and correctness. Everything gets saved with a timestamp, so the next run automatically diffs against this one — that's what makes it a regression suite instead of a one-off test."
