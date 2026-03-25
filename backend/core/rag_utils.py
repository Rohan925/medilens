# backend/core/rag_utils.py

from typing import List
from core.models import RetrievedChunk
from core.config import Config


def build_rag_context(chunks: List[RetrievedChunk]) -> str:
    """
    Build a single context string from retrieved chunks.

    Used by Generator Agent to ground LLM responses.
    """

    if not chunks:
        return ""

    context_parts = []

    for idx, chunk in enumerate(chunks, start=1):
        context_parts.append(
            f"[Source {idx} | {chunk.source}]\n{chunk.text.strip()}"
        )

    full_context = "\n\n".join(context_parts)
    return trim_context(full_context)


def trim_context(context: str) -> str:
    """
    Trim context to maximum allowed size.
    Prevents prompt overflow.
    """

    max_chars = Config.MAX_CONTEXT_CHARS

    if len(context) <= max_chars:
        return context

    return context[:max_chars] + "\n\n[Context truncated]"


def has_retrieved_data(chunks: List[RetrievedChunk]) -> bool:
    """
    Check whether valid retrieved data exists.
    Used by Generator / Fact Checker.
    """

    return bool(chunks and any(chunk.text for chunk in chunks))


def format_sources(chunks: List[RetrievedChunk]) -> List[str]:
    """
    Extract unique source labels for UI or logging.
    """

    sources = set()

    for chunk in chunks:
        if chunk.source:
            sources.add(chunk.source)

    return sorted(list(sources))
