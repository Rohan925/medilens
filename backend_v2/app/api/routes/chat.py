import asyncio

from fastapi import APIRouter

from app.api.schemas.requests import ChatRequest
from app.api.schemas.responses import ChatResponse
from app.domain.enums import MessageRole, RequestMode
from app.domain.models import ChatMessage
from app.graph.runners.chat_graph import run_chat_graph
from app.graph.state import GraphState


router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
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

    latest_user_query = ""
    for message in reversed(history):
        if message.role == MessageRole.USER:
            latest_user_query = message.content
            break

    state = GraphState(
        mode=RequestMode.CHAT,
        raw_query=latest_user_query,
        medicine_name=request.medicine_name,
        history=history,
    )

    final_state = await asyncio.to_thread(run_chat_graph, state)
    return ChatResponse.model_validate(final_state.response)
