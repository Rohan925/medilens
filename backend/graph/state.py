# backend/graph/state.py

from typing import TypedDict, List, Optional

from core.models import RetrievedChunk

class GraphState(TypedDict, total=False):
    """
    Shared state passed through the multi-agent graph.

    Each agent reads from and writes to this state.
    """
    retrieved_chunks: List[RetrievedChunk]
    generated_answer: str
    checked_answer: str
    is_verified: bool
    citations: List[str]
    summary: Optional[str]
    final_answer: str
