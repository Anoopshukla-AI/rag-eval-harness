"""
rag_pipeline/__init__.py

This package is a MINIMAL STANDALONE STAND-IN so the evaluation harness
runs end-to-end without errors. It is NOT your production RAG system.

TWO WAYS TO FIX THE ModuleNotFoundError, PICK ONE:

OPTION A (recommended) — Point the harness at your REAL RAG project:
    1. Find where your actual RAG project defines retrieval and generation
       (e.g., in your "RAG Document Q&A System" repo, likely something like
       `app/retriever.py` or `main.py`).
    2. In eval/retrieval_eval.py and eval/generation_eval.py, change the import lines:
           from rag_pipeline.retriever import retrieve
           from rag_pipeline.generator import generate_answer
       to point at your real module, e.g.:
           from app.retriever import retrieve_top_chunks as retrieve
           from app.generator import answer_question as generate_answer
    3. Delete this stub `rag_pipeline/` folder entirely once your real imports work.

OPTION B (use this stub to test the harness itself first):
    1. Keep this folder as-is.
    2. Run `python rag_pipeline/ingest.py` once to build a small sample
       ChromaDB collection from `rag_pipeline/sample_docs/`.
    3. Run `python eval/run_eval.py` — it will now work against this
       stub pipeline so you can confirm the EVAL HARNESS logic itself
       is correct, before wiring it to your real system.
"""
