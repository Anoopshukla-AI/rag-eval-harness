"""
rag_pipeline/generator.py

Generator: takes a question and retrieved chunk IDs, builds a grounded prompt,
and calls the configured LLM for the final answer.
"""
from __future__ import annotations
import os
import sys

from dotenv import load_dotenv
from openai import OpenAI
from rag_pipeline.retriever import get_chunk_text

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

NVIDIA_KEY = os.environ.get("NVIDIA_API_KEY")
OPENAI_KEY = os.environ.get("OPENAI_API_KEY")
NVIDIA_BASE_URL = os.environ.get("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")
GENERATOR_MODEL = os.environ.get("GENERATOR_MODEL", "meta/llama-3.2-11b-vision-instruct" if NVIDIA_KEY else "gpt-4o")

if NVIDIA_KEY:
    client = OpenAI(base_url=NVIDIA_BASE_URL, api_key=NVIDIA_KEY, timeout=45.0)
else:
    client = OpenAI(api_key=OPENAI_KEY, timeout=45.0)

SYSTEM_PROMPT = """You answer questions using ONLY the provided source text.
If the source text does not contain the answer, respond exactly with:
"I don't have information about that in the available documents."
Do not use outside knowledge. Do not guess."""


def generate_answer(question: str, retrieved_chunk_ids: list[str]) -> str:
    if not retrieved_chunk_ids:
        return "I don't have information about that in the available documents."

    source_text = "\n\n".join(get_chunk_text(cid) for cid in retrieved_chunk_ids)

    response = client.chat.completions.create(
        model=GENERATOR_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Source text:\n{source_text}\n\nQuestion: {question}"},
        ],
        temperature=0,
    )
    return response.choices[0].message.content
