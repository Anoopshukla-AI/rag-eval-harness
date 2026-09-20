# RAG Evaluation Harness

## Problem Statement

RAG systems fail silently. A retrieval bug and a generation bug both produce a "wrong answer," but they need completely different fixes — and without measurement, most teams just say "it seems to work" and ship anyway. This project adds a lightweight evaluation layer on top of an existing production RAG document Q&A system, so retrieval quality and generation quality can be measured separately, tracked over time, and checked for regressions before any prompt, chunking, or model change ships.

## Architecture

```
 test_set.json (labeled questions: factual / multi-doc / out-of-scope)
        │
        ▼
 retrieval_eval.py  ──►  Hit@5, MRR   (is the right chunk being found?)
        │
        ▼
 generation_eval.py ──►  LLM-as-judge (GPT-4o-mini / NVIDIA NIM Llama 3.1)
        │                 groundedness / correctness / refusal accuracy
        ▼
 run_eval.py  ──►  console summary + CSV per-question breakdown
                     + diff against the previous run (regression check)
```

## Directory Structure

```
rag-eval-harness/
├── AGENTS.md                  (project root rules & definition of done)
├── CHANGELOG.md               (tradeoff record for interview discussions)
├── DESIGN.md                  (design choices and rationales)
├── FLOW.md                    (end-to-end execution flow)
├── .agents/
│   └── skills/
│       └── rag-evaluation/
│           └── SKILL.md       (reusable eval methodology)
├── eval/
│   ├── test_set.json          (labeled evaluation dataset)
│   ├── retrieval_eval.py      (Hit@k, MRR computation)
│   ├── generation_eval.py     (LLM-as-judge scoring)
│   ├── run_eval.py            (orchestrator + regression diff engine)
│   └── results/               (timestamped run outputs & CSVs)
├── requirements.txt
└── README.md
```

## How to Run

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure API keys in .env (OpenAI or NVIDIA NIM)
# NVIDIA_API_KEY=nvapi-...
# or OPENAI_API_KEY=sk-...

# 3. Run evaluation
python eval/run_eval.py
```

## Real Sample Output

```
Running evaluation on 8 test questions...
  [1/8] Generating & judging question q01...
  [2/8] Generating & judging question q02...
  [3/8] Generating & judging question q03...
  [4/8] Generating & judging question q04...
  [5/8] Generating & judging question q05...
  [6/8] Generating & judging question q06...
  [7/8] Generating & judging question q07...
  [8/8] Generating & judging question q08...

--- Retrieval Quality ---
Hit@5: 1.0   MRR: 0.9

--- Generation Quality ---
Supported: 87.5%
Correct: 62.5%
Refusal Correct (out-of-scope): 1.0
Avg Latency: 1703.4 ms

--- Regression Diff vs Previous Run ---
hit_at_5: 1.0 -> 1.0  (=)0.0
mrr: 0.9 -> 0.9  (=)0.0
pct_supported: 0.875 -> 0.875  (=)0.0
pct_correct: 0.625 -> 0.625  (=)0.0

Results saved to eval/results/ (timestamp: 20260921_015808)
```

## Known Limitations

- 8-20 questions is a small sample — good enough to catch obvious regressions, not statistically rigorous. A production version would need a larger, continuously-growing test set.
- LLM-as-judge scoring can itself be inconsistent. I manually spot-checked a subset of judge scores against my own reading of the source text to confirm the judge prompt was reliable before trusting it at scale.
- Token/cost tracking is stubbed in `generation_eval.py` (`tokens_used: int`) — wire this to the actual `response.usage` object from the OpenAI / NIM client to get real cost numbers.
- This is a v1 built from scratch for interview transparency. A production version would likely adopt a framework like RAGAS or TruLens once the manual methodology is validated.

## Why This Design

I chose to separate retrieval and generation scoring deliberately — most "RAG doesn't work" complaints are actually retrieval failures wearing a generation costume. By measuring Hit@5/MRR independently, I can tell immediately whether a bad answer came from bad retrieval or bad generation, and fix the right thing instead of guessing.
