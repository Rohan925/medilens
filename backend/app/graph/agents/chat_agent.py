import logging

from app.graph.state import GraphState
from app.services.llm.openai_client import openai_client
from app.services.llm.prompts import build_chat_answer_prompt

logger = logging.getLogger("node.chat")


def _build_history_text(state: GraphState, max_turns: int = 6) -> str:
    history = state.history[-max_turns:]
    lines: list[str] = []
    for message in history:
        role = message.role.value.capitalize()
        lines.append(f"{role}: {message.content}")
    return "\n".join(lines)


def _build_summary_text(state: GraphState) -> str:
    summary = state.structured_summary
    if not summary:
        return ""

    parts = [
        f"Drug name: {summary.drug_name}",
        f"Category: {summary.category}",
        f"Uses: {', '.join(summary.uses) if summary.uses else 'None'}",
        f"Warnings: {', '.join(summary.warnings) if summary.warnings else 'None'}",
        f"Prescription status: {summary.prescription_status}",
    ]
    if summary.summary_text:
        parts.append(f"Description: {summary.summary_text}")
    return "\n".join(parts)


def _build_evidence_text(state: GraphState) -> str:
    if not state.retrieved_chunks:
        return ""
    return "\n\n".join(
        f"Source: {chunk.source}\nContent: {chunk.text}"
        for chunk in state.retrieved_chunks
    )


def chat_agent(state: GraphState) -> GraphState:
    logger.info("Node hit: chat_agent")

    latest_user_message = state.input_text or ""
    if not latest_user_message:
        for message in reversed(state.history):
            if message.role.value == "user":
                latest_user_message = message.content
                break

    if not latest_user_message:
        state.final_answer = "I couldn't find a user question to answer."
        state.warnings.append("Chat agent received no user message.")
        return state

    prompt = build_chat_answer_prompt(
        user_query=latest_user_message,
        medicine_name=state.resolved_medicine or state.medicine_name,
        route=state.chat_route,
        history_text=_build_history_text(state),
        summary_text=_build_summary_text(state),
        evidence_text=_build_evidence_text(state),
    )

    answer = openai_client.invoke_text(prompt)
    if not answer:
        answer = (
            "I couldn't generate a grounded response right now. "
            "Please consult a healthcare professional for medical advice."
        )
        state.warnings.append("Chat agent fell back due to empty LLM output.")

    state.final_answer = answer
    return state
