from fastapi import APIRouter, Depends
from starlette.concurrency import run_in_threadpool

from app.api.schemas.requests import ChatRequest
from app.api.schemas.responses import ChatResponse
from app.domain.enums import MessageRole, RequestMode
from app.domain.models import ChatMessage
from app.graph.runners.chat_graph import run_chat_graph
from app.graph.state import GraphState
from app.services.auth import require_authenticated_user


router = APIRouter()


@router.post("/chat", response_model=ChatResponse, dependencies=[Depends(require_authenticated_user)])
async def chat_with_medicine(request: ChatRequest) -> ChatResponse:
    history: list[ChatMessage] = []
    for message in request.history:
        try:
            role = MessageRole(message.role)
        except ValueError:
            role = MessageRole.USER
        history.append(
            ChatMessage(
                role=role,
                content=message.content,
            )
        )

    state = GraphState(
        mode=RequestMode.CHAT,
        input_text=request.query.strip(),
        history=history,
    )

    final_state = await run_in_threadpool(run_chat_graph, state)
    return ChatResponse.model_validate(final_state.response)
