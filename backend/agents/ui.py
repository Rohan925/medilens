# backend/ui.py

from fastapi import APIRouter
from pydantic import BaseModel

from agents.coordinator_agent import coordinator_agent

router = APIRouter()


class QueryRequest(BaseModel):
    query: str


class QueryResponse(BaseModel):
    answer: str
    summary: str | None = None
    citations: list = []


@router.post("/query", response_model=QueryResponse)
async def handle_query(request: QueryRequest):
    """
    UI ENTRYPOINT

    - Receives user query from frontend
    - Passes it to coordinator agent
    - Returns final response
    """

    initial_state = {
        "query": request.query
    }

    final_state = await coordinator_agent(initial_state)

    return QueryResponse(
        answer=final_state.get("final_answer", ""),
        summary=final_state.get("summary"),
        citations=final_state.get("citations", [])
    )
