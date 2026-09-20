# AGENTS.md — RAG Evaluation Harness (Project Root Rules)

This file defines standing instructions for any agent working in this workspace. Read this before making changes.

## Project Context

This project is a standalone evaluation harness for an existing RAG (retrieval-augmented generation) document Q&A system. It exists to close a specific gap for an AI Engineer job application: the target JD requires "evaluation datasets, quality metrics and regression tests for probabilistic systems," and my existing RAG pipeline (FastAPI, ChromaDB, MMR re-ranking, GPT-4o, hierarchical chunking at 512 tokens/100 overlap) has no formal evaluation layer.

**Goal:** Build an eval harness that plugs into the existing RAG pipeline, scores retrieval and generation quality separately, and can be re-run as a regression suite after any change to chunking, prompts, or models.

**Time budget:** 1-2 days of agent + human work. Keep scope tight — this is a focused proof project for a job interview, not a production eval platform. Do not over-engineer.

## Directory Standards

```
rag-eval-harness/
├── AGENTS.md                  (this file)
├── .agents/
│   └── skills/
│       └── rag-evaluation/
│           └── SKILL.md       (reusable eval methodology)
├── eval/
│   ├── test_set.json
│   ├── retrieval_eval.py
│   ├── generation_eval.py
│   ├── run_eval.py
│   └── results/                (generated CSVs land here)
├── requirements.txt
└── README.md
```

## Coding Standards

- Python 3.11+, full type hints on every function signature.
- Reuse the existing RAG pipeline's retrieval and generation functions — import them, never duplicate chunking/embedding/retrieval logic in this project.
- Keep dependencies minimal: `openai`, `chromadb` (already installed in the parent project), `pandas` for CSV output. No new heavy frameworks, no database, no async, no UI.
- Every function must be small and independently testable — an interviewer may read this code directly and ask "walk me through this function."
- Naming: snake_case for functions/variables, one file per responsibility (retrieval scoring, generation scoring, orchestration).

## Testing Requirements

- No formal unit test suite is required for this project (it IS the test suite for another system), but `run_eval.py` must run end-to-end without errors against the sample `test_set.json` before this project is considered done.
- Manually spot-check at least 3 LLM-as-judge scores against your own judgment to confirm the judge prompt is reliable before trusting its output at scale.

## Definition of Done

Running `python eval/run_eval.py` must:
1. Print Hit@5 and MRR retrieval scores to console.
2. Print % SUPPORTED, % CORRECT, and % REFUSAL_CORRECT generation scores.
3. Write a timestamped CSV to `eval/results/` with per-question breakdown.
4. Print a diff against the most recent prior run in `eval/results/`, if one exists.
5. `README.md` must include a problem statement, an ASCII architecture diagram, run instructions, a sample real output, and a "Known Limitations" section.

## Deprecation / Things Not To Do

- Do not add a web UI or dashboard — this is a CLI tool.
- Do not build a new RAG system inside this repo — this repo assumes an existing RAG system is importable.
- Do not use a full ML eval framework (e.g., RAGAS, TruLens) for this v1 — write it from scratch so every line is explainable in an interview. Note this as a future improvement in the README instead.
