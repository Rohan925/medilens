import logging
import re

from app.graph.state import GraphState
from app.services.llm.openai_client import openai_client
from app.services.llm.prompts import build_chat_router_prompt

logger = logging.getLogger("node.chat_router")


def _latest_user_query(state: GraphState) -> str:
    if state.raw_query:
        return state.raw_query
    for message in reversed(state.history):
        if message.role.value == "user":
            return message.content
    return ""


def _history_text(state: GraphState, max_turns: int = 8) -> str:
    history = state.history[-max_turns:]
    lines: list[str] = []
    for message in history:
        lines.append(f"{message.role.value.capitalize()}: {message.content}")
    return "\n".join(lines)


def _parse_router_output(output: str) -> tuple[str, str | None]:
    route_match = re.search(r"ROUTE:\s*(ANSWER|RETRIEVE)", output, flags=re.IGNORECASE)
    medicine_match = re.search(r"MEDICINE:\s*(.*)", output, flags=re.IGNORECASE)

    route = route_match.group(1).upper() if route_match else "ANSWER"
    medicine = medicine_match.group(1).strip() if medicine_match else "NONE"
    if medicine.upper() == "NONE":
        return route, None
    return route, medicine


def chat_router_agent(state: GraphState) -> GraphState:
    logger.info("Node hit: chat_router_agent")
    query = _latest_user_query(state).strip()

    if not query:
        state.chat_route = "answer"
        state.final_answer = "What would you like help with?"
        return state

    prompt = build_chat_router_prompt(
        query=query,
        history_text=_history_text(state),
    )
    output = openai_client.invoke_text(prompt)
    if output:
        route, medicine_name = _parse_router_output(output)
        state.chat_route = "retrieve" if route == "RETRIEVE" else "answer"
        if medicine_name:
            state.medicine_name = medicine_name
        return state

    state.chat_route = "answer"
    return state
