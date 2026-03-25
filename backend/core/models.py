
# backend/core/models.py

from pydantic import BaseModel, Field
from typing import List, Optional


class SearchQuery(BaseModel):
    """
    Input model for search / query requests
    """
    query: str
    max_results: int = 5


class AgentResponse(BaseModel):
    """
    Standard response returned to UI
    """
    answer: str
    sources: List[str] = Field(default_factory=list)


class DrugInfo(BaseModel):
    """
    Structured drug information
    """
    name: str
    description: Optional[str] = None


class RetrievedChunk(BaseModel):
    text: str
    source: str
    reference: str | None = None