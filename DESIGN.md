# DESIGN.md — RAG Evaluation Harness

## 1. Problem

The existing RAG document Q&A system (FastAPI + ChromaDB + MMR re-ranking + GPT-4o) has no way to answer "did this change make the system better or worse?" Right now, quality is judged by manual spot-checking, which doesn't scale and can't catch regressions. This design adds a measurement layer without touching the production RAG pipeline itself.

## 2. Goals

- Measure retrieval quality and generation quality **separately**, so a bad answer can be traced to the right root cause.
- Make evaluation **repeatable** — the same test set, run the same way, every time, so scores are comparable across runs.
- Keep it **cheap and fast** — a full eval run should cost pennies and finish in under a few minutes for a small test set.
- Make it **explainable in an interview** — every scoring function should be simple enough to read and defend line by line.

## 3. Non-Goals

- Not building a general-purpose eval framework (RAGAS/TruLens-equivalent). This is a focused v1.
- Not evaluating multi-turn conversations — single-question, single-answer only.
- Not building a UI or dashboard — CLI + CSV output only.
- Not covering latency/cost optimization itself — this harness *measures* latency and cost, it doesn't try to reduce them (that's project #5, the cost/latency dashboard).

## 4. Key Design Decisions

### 4.1 Why separate retrieval and generation scoring?
A wrong final answer has two possible root causes: the retriever didn't find the right chunk, or the generator had the right chunk but used it badly (or ignored it and hallucinated). Scoring only the final answer conflates these. By scoring Hit@5/MRR independently from groundedness/correctness, a failure can be traced to the correct stage before any fix is attempted.

### 4.2 Why LLM-as-judge instead of exact-match string comparison?
Exact-match scoring fails for RAG answers because there are many valid phrasings of a correct answer. An LLM judge can assess semantic correctness and groundedness (does every claim trace back to the source text) in a way string matching cannot. The tradeoff is judge reliability — mitigated by using a cheaper, separate model (GPT-4o-mini) than the one being evaluated, and manually spot-checking a subset of judge outputs before trusting the harness.

### 4.3 Why three question categories (factual / multi-document / out-of-scope)?
Each category stresses a different failure mode:
- **Factual** tests basic retrieval correctness.
- **Multi-document** tests whether the retriever pulls enough distinct context and whether the generator can synthesize across chunks.
- **Out-of-scope** tests the most dangerous failure mode — hallucinating an answer when none exists in the corpus — which factual/multi-doc questions can't reveal.

### 4.4 Why store results as timestamped files instead of a database?
This is a small, single-user proof project. A database adds setup overhead with no real benefit at this scale. Timestamped JSON/CSV files in `eval/results/` are sufficient to diff runs and are trivially portable (can be checked into git for a visible history of quality over time).

### 4.5 Why import from the existing RAG pipeline instead of reimplementing chunking/retrieval?
Duplicating the pipeline logic would mean the eval harness could silently drift out of sync with the real system, making its scores meaningless. Importing the real `retrieve()` and `generate_answer()` functions guarantees the harness is always testing the actual production code path.

## 5. Data Model

```
TestQuestion {
  id: str
  question: str
  expected_answer: str | null   # null = out-of-scope
  source_chunk_ids: list[str]   # empty list for out-of-scope
  category: "factual" | "multi_document" | "out_of_scope"
}

RetrievalResult {
  question_id: str
  hit_at_5: bool
  reciprocal_rank: float
  retrieved_ids: list[str]
}

GenerationResult {
  question_id: str
  generated_answer: str
  groundedness: "SUPPORTED" | "PARTIALLY_SUPPORTED" | "UNSUPPORTED"
  correctness: "CORRECT" | "PARTIALLY_CORRECT" | "INCORRECT"
  refusal_check: "REFUSAL_CORRECT" | "REFUSAL_MISSING" | null
  tokens_used: int
  latency_ms: float
}

RunSummary {
  hit_at_5: float
  mrr: float
  pct_supported: float
  pct_correct: float
  pct_refusal_correct: float | "N/A"
  avg_latency_ms: float
  timestamp: str
}
```

## 6. Metrics Definitions

| Metric | Formula | What it tells you |
|---|---|---|
| Hit@5 | correct chunk in top 5 retrieved / total questions | Is retrieval finding the right information at all? |
| MRR | avg(1 / rank of first correct chunk) | Is the correct chunk ranked near the top, not just present? |
| % Supported | groundedness=SUPPORTED / total | Is the model making claims it can actually back up? |
| % Correct | correctness=CORRECT / total | Does the answer match what a human would expect? |
| % Refusal Correct | refusal_check=REFUSAL_CORRECT / out-of-scope questions | Does the system avoid hallucinating on unanswerable questions? |

## 7. Failure Modes and Mitigations

| Failure Mode | Mitigation |
|---|---|
| Judge model is inconsistent or biased | Manually spot-check 3-5 judge scores per run against human judgment |
| Test set too small to be statistically meaningful | Documented as a known limitation; plan to grow to 50+ questions over time |
| Retrieval and generation drift out of sync with production pipeline | Import real pipeline functions directly, never reimplement |
| Cost of running eval grows with test set size | Use a cheap judge model (GPT-4o-mini); track and report cost per run |

## 8. Future Improvements (Out of Scope for v1)

- Grow the test set to 50+ questions with contributions from real user queries.
- Add a "diff viewer" that shows exactly which questions flipped from pass to fail between runs, not just aggregate percentages.
- Wire this into CI so evaluation runs automatically on every pipeline change (pull request check).
- Migrate to a maintained framework (RAGAS/TruLens) once the manual methodology is proven and the team wants less custom code to maintain.
