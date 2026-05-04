from fastapi import APIRouter, Depends
from starlette.concurrency import run_in_threadpool

from app.api.schemas.requests import SearchRequest
from app.api.schemas.responses import SearchResponse
from app.domain.enums import RequestMode
from app.graph.runners.search_graph import run_search_graph
from app.graph.state import GraphState
from app.services.auth import require_authenticated_user


router = APIRouter()


@router.post("/search", response_model=SearchResponse, dependencies=[Depends(require_authenticated_user)])
async def search_medicine(request: SearchRequest) -> SearchResponse:
    state = GraphState(
        mode=RequestMode.SEARCH,
        input_text=request.query.strip(),
    )

    final_state = await run_in_threadpool(run_search_graph, state)
    return SearchResponse.model_validate(final_state.response)
