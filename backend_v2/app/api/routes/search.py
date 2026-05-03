import asyncio

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
        raw_query=request.medicine,
        medicine_name=request.medicine,
    )

    final_state = await asyncio.to_thread(run_search_graph, state)
    return SearchResponse.model_validate(final_state.response)


"""
1. /search - medicine --> llm interpret using llm --> pub chem & open fda --> summarizer --> user
2. /chat - user symptoms (NL Queries) -> current query + if history --> llm interpretation -->
        call open fda or pub chem if there's a medicine prescribed by llm (for meta data collection)
    /search + /chat --> copy the context from /search and pass it to chat for follow up questions
3. /ocr - extract medicine name and route it /search graph
    /ocr_search + /chat - copy the context from /ocr and pass it to chat for follow up questions
"""