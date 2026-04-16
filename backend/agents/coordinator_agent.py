from typing import Dict, Any

from agents.retriever_agent import retriever_agent
from agents.summarizer import summariser_agent
from agents.generator_agent import generator_agent
from agents.fact_checker_agent import fact_checker_agent
from agents.citation_agent import citation_agent


async def coordinator_agent(initial_state: Dict[str, Any]) -> Dict[str, Any]:
    """
    CENTRAL BRAIN

    Responsibilities:
    - Decide execution flow
    - Call agents conditionally
    - Handle fallbacks
    - Ensure consistent final output
    """

    # Always copy to avoid mutation bugs
    state = initial_state.copy()

    # ---------------- STEP 1: RETRIEVE ----------------
    state = await retriever_agent(state)

    has_data = bool(state.get("retrieved_chunks"))

    # ---------------- STEP 2: SUMMARIZATION ----------------
    # Always build a structured summary so downstream services never
    # crash when external retrieval or model calls are unavailable.
    state = await summariser_agent(state)

    # ---------------- STEP 3: GENERATE ----------------
    state = await generator_agent(state)

    # ---------------- STEP 4: FACT CHECK ----------------
    state = await fact_checker_agent(state)

    # Decide best answer
    answer = (
        state.get("checked_answer")
        or state.get("draft_answer")
        or ""
    )

    # ---------------- STEP 5: CITATION ----------------
    state["draft_answer"] = answer
    state = await citation_agent(state)

    final_answer = state.get("final_answer") or answer

    # ---------------- STEP 6: SAFETY FALLBACK ----------------
    if not final_answer.strip():
        final_answer = (
            "I couldn't find reliable medical information for your query. "
            "Please consult a healthcare professional."
        )

    # ---------------- FINAL OUTPUT ----------------
    return {
        "final_answer": final_answer,
        "citations": state.get("citations", []),
        "structured_summary": state.get("structured_summary"),
        "fact_check_flags": state.get("fact_check_flags", []),
    }
