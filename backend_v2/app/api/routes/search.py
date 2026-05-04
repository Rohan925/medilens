from fastapi import APIRouter

from app.api.schemas.requests import SearchRequest
from app.api.schemas.responses import SearchResponse
from app.domain.enums import RequestMode
from app.graph.runners.search_graph import run_search_graph
from app.graph.state import GraphState


router = APIRouter()


@router.post("/search", response_model=SearchResponse)
async def search_medicine(request: SearchRequest) -> SearchResponse:
    state = GraphState(
        mode=RequestMode.SEARCH,
        search_text=request.query.strip(),
        raw_query=request.query.strip(),
    )

    final_state = run_search_graph(state)
    return SearchResponse.model_validate(final_state.response)
