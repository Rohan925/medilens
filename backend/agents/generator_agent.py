from typing import Dict, Any, List

from langchain_core.prompts import PromptTemplate

from core.llm_client import generate_answer
from core.models import RetrievedChunk
from services.context_builder import build_rag_context


# ---------------- PROMPT TEMPLATE ----------------
GENERATOR_PROMPT = PromptTemplate.from_template("""
You are a medical assistant AI.

User Query:
{query}

Conversation History:
{history}

Available Medical Context:
{context}

INSTRUCTIONS:

1. Understand the user's intent:
   - symptom-related
   - medicine-related
   - general health

2. If context is provided:
   - Use it as the primary source
   - Do NOT contradict it

3. If context is missing:
   - Give a general safe answer
   - Do NOT hallucinate specific facts

4. Safety Rules:
   - NEVER provide dosage, prescription, or diagnosis
   - Avoid strong claims if unsure

5. Style:
   - Clear and concise
   - Natural explanation
   - No unnecessary technical jargon

6. End with:
   "Consult a healthcare professional for proper medical advice."

Answer:
""")


# ---------------- AGENT ----------------
async def generator_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    GENERATOR AGENT (LangChain Prompt Version)

    - Uses PromptTemplate
    - LLM decides how to respond
    - Works with/without context
    """

    query: str = state.get("query", "")
    history_arr: list = state.get("history", [])
    chunks: List[RetrievedChunk] = state.get("retrieved_chunks", [])

    # ---------------- BUILD CONTEXT ----------------
    context_text = build_rag_context(chunks)

    # ---------------- BUILD HISTORY ----------------
    history_text = ""
    if history_arr:
        for m in history_arr[-5:]:
            role = "User" if m["role"] == "user" else "Assistant"
            history_text += f"{role}: {m['content']}\n"

    # ---------------- FORMAT PROMPT ----------------
    prompt = GENERATOR_PROMPT.format(
        query=query,
        context=context_text,
        history=history_text
    )

    # ---------------- GENERATE ----------------
    answer = await generate_answer(prompt)

    # ---------------- SAFETY FALLBACK ----------------
    if not answer or not answer.strip():
        answer = (
            "I'm unable to provide a reliable answer. "
            "Consult a healthcare professional."
        )

    # ---------------- STORE OUTPUT ----------------
    state["draft_answer"] = answer
    return state