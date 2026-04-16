from typing import Dict, Any
from core.llm_client import generate_answer


async def fact_checker_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    answer = state.get("draft_answer", "")
    context = state.get("retrieved_chunks", [])

    context_text = " ".join([c.text for c in context])

    prompt = f"""
You are a medical fact-checker.

Answer:
{answer}

Context:
{context_text}

Check:
- Is answer grounded in context?
- Any unsafe advice?

Respond with:
VALID / PARTIAL / INVALID
"""

    result = await generate_answer(prompt)

    if "VALID" in result.upper():
        confidence = "high"
    elif "PARTIAL" in result.upper():
        confidence = "medium"
    else:
        confidence = "low"

    state["checked_answer"] = answer
    state["confidence"] = confidence
    return state