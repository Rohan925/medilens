# backend/agents/generator_agent.py

from typing import Dict, Any, List

from core.llm_client import llm_client
from core.models import RetrievedChunk
from services.context_builder import build_rag_context


async def generator_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    GENERATOR AGENT (G in RAG)

    - Takes the user query and retrieved chunks.
    - Builds a RAG-style context string.
    - Calls the LLM client with (question + context).
    - Stores the draft answer in state["draft_answer"].
    """
    query: str = state.get("query", "")
    history_arr: list = state.get("history", [])
    chunks: List[RetrievedChunk] = state.get("retrieved_chunks", [])

    # Build RAG context from chunks
    context_text = build_rag_context(chunks)
    
    # Build Conversation History Transcript
    history_text = ""
    if history_arr and len(history_arr) > 1:
        history_text = "Conversation History:\n"
        for m in history_arr[:-1]:
            role_name = "User" if m["role"] == "user" else "Assistant"
            history_text += f"{role_name}: {m['content']}\n"
        history_text += "\n"

    # Extract metadata for the prompt
    metadata = state.get("drug_metadata", {})
    medicine_name = state.get("medicine_name") or "General Health Inquiry"
    category = metadata.get("pharm_class", "General Health")
    is_rx = metadata.get("is_prescription", "Unknown")
    uses_list = metadata.get("uses", [])
    uses_str = ", ".join(uses_list[:5]) if uses_list else "General indications"

    # Determine if this is a specific medicine query or a general symptom query
    if medicine_name == "General Health Inquiry":
        # SYMPTOM CHECKER PROMPT
        # SAFE OTC ALLOWLIST (Grounding)
        SAFE_OTC_MAP = {
            "fever": "Paracetamol (Acetaminophen) - Reduces fever and mild pain.",
            "headache": "Paracetamol or Ibuprofen - Pain relief.",
            "cold": "Steam inhalation, Warm fluids, Decongestants (e.g., Phenylephrine) if nose blocked.",
            "cough": "Warm water gargle, Honey, Dextromethorphan (for dry cough).",
            "vomiting": "Oral Rehydration Solution (ORS), Sip water slowly. Avoid solid food for a few hours. DO NOT use anti-emetics without doctor advice.",
            "diarrhea": "ORS (primary), Zinc supplements. Loperamide NOT recommended without doctor advice.",
            "acidity": "Antacids (e.g., Gelusil, Digene). Avoid spicy food.",
            "pain": "Paracetamol (safe), Ibuprofen (with food).",
        }

        # Check if query matches any safe key
        query_lower = query.lower()
        matched_advice = []
        for key, advice in SAFE_OTC_MAP.items():
            if key in query_lower:
                matched_advice.append(f"- {key.title()}: {advice}")
        
        # If matches found, use them. If not, fallback to "Consult Doctor".
        if matched_advice:
            grounded_context = "\n".join(matched_advice)
            prompt = (
                "You are a helpful and grounded medical assistant.\n\n"
                f"{history_text}"
                f"User Query: {query}\n\n"
                "INSTRUCTIONS:\n"
                "- Use ONLY the 'Approved Advice' below to answer.\n"
                "- Answer naturally in complete sentences.\n"
                "- Do not use technical labels like 'Medicines:' or 'Precautions:'.\n"
                "- Keep it brief and helpful.\n"
                "- ALWAYS end with this exact safety warning: 'Consult a doctor if symptoms persist or for infants/pregnancy.'\n\n"
                "Approved Advice:\n"
                f"{grounded_context}\n"
            )
        else:
            # BROAD FALLBACK: General Medical Assistant (for queries like "What is Metformin?")
            # Instead of rejecting, we answer safely using general knowledge.
            prompt = (
                "You are a helpful and safe medical assistant.\n\n"
                f"{history_text}"
                f"User Query: {query}\n\n"
                "INSTRUCTIONS:\n"
                "- Answer the user's health or medicine question safely.\n"
                "- If asking about a specific medicine, provide a brief summary of its common uses.\n"
                "- Do NOT provide specific dosage, prescriptions, or diagnosis.\n"
                "- Keep it brief (under 50 words) and helpful.\n"
                "- ALWAYS end with: 'Consult a doctor for professional advice.'\n"
            )
    else:
        # SPECIFIC MEDICINE PROMPT
        # SPECIFIC MEDICINE PROMPT
        prompt = (
            "You are a concise medical assistant.\n\n"
            "Rules:\n"
            "- Answer ONLY the specific question asked.\n"
            "- Strict 40-word limit.\n"
            "- No fluff, no pleasantries.\n"
            "- Do NOT add 'General Safety' or 'Precautions' sections unless asked.\n"
            "- If the answer is simple, keep it under 20 words.\n\n"
            "Medicine Information:\n"
            f"Name: {medicine_name}\n"
            f"Category: {category}\n"
            f"Prescription Required: {is_rx}\n"
            f"Uses: {uses_str}\n\n"
            f"{history_text}"
            "User Question:\n"
            f"{query}\n\n"
        )
    
    # For now, llm_client.generate_answer can just accept (question, chunks)
    # but we can overload it to accept a full prompt later.
    # Easiest: treat 'prompt' as the 'question' argument.
    answer = await llm_client.generate_answer(prompt, [])

    state["draft_answer"] = answer
    return state

