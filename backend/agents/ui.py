from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional

from agents.coordinator_agent import coordinator_agent

router = APIRouter()


class QueryRequest(BaseModel):
    query: str


class QueryResponse(BaseModel):
    answer: str
    summary: Optional[dict] = None
    citations: List[dict] = []


@router.post("/query", response_model=QueryResponse)
async def handle_query(request: QueryRequest):
    """
    UI ENTRYPOINT

    - Receives user query
    - Sends to coordinator
    - Returns structured response
    """

    # ---------------- INITIAL STATE ----------------
    initial_state = {
        "query": request.query,
        "history": [],
        "medicine_name": None
    }

    try:
        final_state = await coordinator_agent(initial_state)

        return QueryResponse(
            answer=final_state.get("final_answer", ""),
            summary=final_state.get("structured_summary"),
            citations=final_state.get("citations", [])
        )

    except Exception as e:
        # Safe fallback
        return QueryResponse(
            answer="Something went wrong while processing your request. Please try again.",
            summary=None,
            citations=[]
        )