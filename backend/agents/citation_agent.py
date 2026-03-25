# backend/agents/citation_agent.py

from typing import Dict, Any, List
from core.models import RetrievedChunk


async def citation_agent(state: Dict[str, Any]) -> Dict[str, Any]:

    retrieved_chunks: List[RetrievedChunk] = state.get("retrieved_chunks", [])
    mode = state.get("mode", "chat")

    # Deduplication map: url -> citation_obj
    citation_map = {}

    for chunk in retrieved_chunks:
        if not chunk.reference:
            continue

        ref_lower = chunk.reference.lower()
        
        if chunk.source == "OpenFDA":
            url = f"https://dailymed.nlm.nih.gov/dailymed/search.cfm?query={chunk.reference}"
            citation_map[url] = {
                "source": "FDA DailyMed",
                "title": f"DailyMed: {chunk.reference}",
                "url": url
            }

        elif chunk.source == "PubChem":
            url = f"https://pubchem.ncbi.nlm.nih.gov/compound/{chunk.reference}"
            citation_map[url] = {
                "source": "PubChem",
                "title": f"PubChem: {chunk.reference}",
                "url": url
            }

    # Helper: If we already have citations in state (from other agents), preserve them
    existing_citations = state.get("citations", [])
    for c in existing_citations:
        if c.get("url"):
            citation_map[c["url"]] = c

    citations = list(citation_map.values())
    state["citations"] = citations

    # For chat mode append to answer (if not already appended)
    if mode == "chat":
        # Check draft_answer or checked_answer
        answer_key = "checked_answer" if state.get("checked_answer") else "draft_answer"
        current_answer = state.get(answer_key, "")
        
        if current_answer and citations:
            # Avoid re-appending if it looks like it's already there
            if "Sources:" not in current_answer:
                citation_text = "\n".join(
                    f"- [{c['source']}]({c['url']})"
                    for c in citations
                )
                state["final_answer"] = (
                    f"{current_answer}\n\n**Sources:**\n{citation_text}"
                )
            else:
                 state["final_answer"] = current_answer

    return state
