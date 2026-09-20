# CHANGELOG.md — RAG Evaluation Harness

This file tracks what changed in the system and why, at each stage. Use this format going forward: every change gets a **What Changed** line and a **Why It Changed** line, so the reasoning is never lost — this is exactly what an interviewer means when they ask "what tradeoffs did you consider."

## v0 → v1: Adding Evaluation to an Existing RAG System

**What changed:** The RAG document Q&A system (FastAPI + ChromaDB + MMR re-ranking + GPT-4o) previously had no automated way to measure quality — validation was manual spot-checking only.

**Why it changed:** The target job (Torinit AI Engineer) explicitly requires "evaluation datasets, quality metrics and regression tests for probabilistic systems" as a core responsibility. Manual spot-checking doesn't scale, can't be diffed across changes, and gives no defensible number to point to in an interview.

---

## Change 1: Separated Retrieval Scoring From Generation Scoring

**What changed:** Instead of scoring only the final answer, the harness scores whether the correct chunk was retrieved (Hit@5, MRR) completely separately from whether the generated answer used that chunk correctly (groundedness, correctness).

**Why it changed:** A wrong final answer has two very different possible causes — bad retrieval or bad generation — and they need different fixes. Scoring only the final answer hides which one actually broke. Splitting them means a failure can be traced to the right stage before touching any code.

---

## Change 2: Added a Three-Category Test Set (Factual / Multi-Document / Out-of-Scope)

**What changed:** The test set isn't just random questions — it's deliberately split into factual lookup, multi-document synthesis, and out-of-scope questions.

**Why it changed:** Each category stresses a different failure mode. Factual questions test basic retrieval. Multi-document questions test whether the system pulls enough context and synthesizes across chunks. Out-of-scope questions test the most dangerous failure mode of all — hallucinating an answer instead of admitting the corpus has no answer — which the other two categories can't reveal at all. Without this category, a system that hallucinates confidently on unanswerable questions would score perfectly on the other tests and look fine.

---

## Change 3: Chose LLM-as-Judge Over Exact-Match String Comparison

**What changed:** Generation quality is scored by a second LLM (GPT-4o-mini) reading the source text, the question, and the generated answer — not by comparing strings for an exact match.

**Why it changed:** RAG answers can be phrased many valid ways, so exact-match scoring would mark correct answers as failures just because the wording differs. An LLM judge can assess whether the *meaning* is correct and whether every claim traces back to the source. The tradeoff is that the judge itself can be wrong or inconsistent — mitigated by using a cheaper, different model than the one being evaluated (avoiding self-grading bias) and manually spot-checking a sample of judge scores before trusting the harness at scale.

---

## Change 4: Stored Results as Timestamped Files Instead of a Database

**What changed:** Each run writes `retrieval_{timestamp}.csv`, `generation_{timestamp}.csv`, and `summary_{timestamp}.json` to a local `results/` folder, instead of writing to a database.

**Why it changed:** This is a single-user proof project, not a multi-user production service — a database would add setup and maintenance overhead with no real benefit at this scale. Flat timestamped files are simple, portable, diffable, and can be checked into git to show a visible quality history over time. This decision would likely change (to a real database) if the harness were adopted by a team running it continuously in CI.

---

## Change 5: Imported the Real RAG Pipeline Instead of Reimplementing It

**What changed:** `retrieval_eval.py` and `generation_eval.py` import `retrieve()` and `generate_answer()` directly from the existing RAG project rather than rewriting chunking/embedding/retrieval logic inside the eval harness.

**Why it changed:** If the harness reimplemented the pipeline logic separately, the two versions could silently drift apart — the harness would end up testing code that isn't actually running in production, making every score meaningless. Importing the real functions guarantees the eval harness always tests the exact code path that's live.

---

## Change 6: Added a Regression Diff Against the Previous Run

**What changed:** `run_eval.py` automatically loads the most recent prior `summary_*.json` and prints a diff (e.g., `hit_at_5: 0.75 → 0.86 (▲0.11)`) alongside the current run's results.

**Why it changed:** A single run's numbers are only useful in comparison to something. Without a diff, "Hit@5 is 0.86" doesn't tell you if a recent change helped or hurt. Automating the comparison turns every run into a regression check by default, which is the actual JD requirement ("regression tests for probabilistic systems"), not just a one-off quality snapshot.

---

## How to Use This File Going Forward

Every time you change chunking size, the prompt, the model, or the retrieval logic in the underlying RAG system, add a new entry here in the same format: what changed, why it changed, and (once you've run the eval) what the before/after numbers were. This file becomes your evidence trail for the interview question "how did you improve the system, and what would you do differently now."
