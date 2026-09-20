---
name: rag-evaluation
description: Methodology for evaluating RAG (retrieval-augmented generation) systems by separately scoring retrieval accuracy and generation groundedness, then tracking results as a regression suite.
---

# Skill: RAG Evaluation

Use this skill whenever asked to evaluate, test, or measure the quality of a retrieval-augmented generation system.

## When To Use This Skill

- The task mentions "evaluate," "test," "measure quality," or "regression test" in the context of a RAG, document Q&A, or retrieval system.
- The user has an existing RAG pipeline and wants to know if a change (new chunking, new prompt, new model) improved or hurt quality.

## Core Method

1. **Separate retrieval from generation.** Never score the final answer alone — first confirm the correct source chunk was retrieved, independently of whether the generated answer used it well. A wrong final answer could be a retrieval failure or a generation failure; conflating them hides the real problem.

2. **Build a small labeled test set first.** 15-25 questions is enough for a v1. Cover three categories:
   - Factual lookup (answer exists verbatim in one chunk)
   - Multi-document synthesis (answer requires combining multiple chunks)
   - Out-of-scope (no answer exists — correct behavior is refusal, not hallucination)

3. **Score retrieval with Hit@k and MRR.**
   - Hit@k: was the correct chunk in the top k retrieved results?
   - MRR (Mean Reciprocal Rank): rewards ranking the correct chunk higher, not just present.

4. **Score generation with an LLM-as-judge**, checking:
   - Groundedness: is every claim in the answer traceable to the retrieved source text?
   - Correctness: does the answer match the expected meaning?
   - Refusal accuracy: for out-of-scope questions, did the system correctly decline instead of hallucinating?
   Use a cheaper model as the judge (e.g., GPT-4o-mini or NVIDIA NIM Llama-3.1-8b) than the model being evaluated, to control cost.

5. **Track results as a regression suite.** Store every run's output with a timestamp. After any pipeline change (chunking size, prompt, model swap), re-run the same test set and diff the scores against the previous run. This turns "I think it's better" into "Hit@5 went from 0.82 to 0.89."

6. **Track cost and latency alongside quality.** A change that improves quality but doubles cost or latency needs to be a conscious tradeoff, not an accident — always report all three together.

## Output Format

When this skill is invoked, produce:
- A test set file (JSON or CSV)
- A retrieval scoring script
- A generation scoring script (with the LLM-as-judge prompt)
- A single runner script that ties it together and prints/saves a summary report
- A brief README explaining the methodology and how to interpret the numbers

## Anti-Patterns To Avoid

- Do not skip the out-of-scope/refusal test category — hallucination on unanswerable questions is one of the most common and dangerous RAG failure modes.
- Do not use the same model for generation and judging without at least spot-checking the judge's scores manually — self-grading bias is real.
- Do not build a heavyweight eval framework for a v1 proof project — a plain script with clear functions is more defensible in an interview than an opaque dependency.
