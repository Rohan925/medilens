from fastapi import APIRouter
from starlette.concurrency import run_in_threadpool

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
        input_text=request.query.strip(),
    )

    final_state = await run_in_threadpool(run_search_graph, state)
    return SearchResponse.model_validate(final_state.response)
