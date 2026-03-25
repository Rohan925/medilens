# backend/services/context_builder.py

from typing import List

from core.models import RetrievedChunk
from core.config import Config


def build_context(drug_name: str, drug_data: dict) -> str:
    """
    Builds readable context for LLM + frontend from drug data
    """

    if not drug_data:
        return f"No detailed data found for {drug_name}."

    parts = [f"Medicine name: {drug_name.capitalize()}"]

    if "purpose" in drug_data:
        parts.append(f"Purpose: {drug_data['purpose']}")

    if "indications" in drug_data:
        parts.append(f"Uses: {drug_data['indications']}")

    if "warnings" in drug_data:
        parts.append(f"Warnings: {drug_data['warnings']}")

    if "dosage" in drug_data:
        parts.append(f"Dosage: {drug_data['dosage']}")

    return "\n".join(parts)

def _trim_context(context: str) -> str:
    """
    Trim context to a safe maximum length.
    Prevents prompt overflow.
    """

    max_chars = Config.MAX_CONTEXT_CHARS

    if len(context) <= max_chars:
        return context

    return context[:max_chars] + "\n\n[Context truncated]"


def build_rag_context(chunks: List[RetrievedChunk]) -> str:
    """
    Constructs a single context string from retrieved chunks.
    """
    if not chunks:
        return ""

    context_parts = []
    for i, chunk in enumerate(chunks, 1):
        context_parts.append(f"Source {i} ({chunk.source}):\n{chunk.text}")
    
    full_context = "\n\n".join(context_parts)
    return _trim_context(full_context)
