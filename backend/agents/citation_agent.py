from typing import Dict, Any, List
from core.models import RetrievedChunk


async def citation_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Citation Agent

    Responsibilities:
    - Extract unique citations from retrieved chunks
    - Merge with existing citations
    - Attach sources to final_answer (uniformly, no mode logic)
    """

    retrieved_chunks: List[RetrievedChunk] = state.get("retrieved_chunks", [])

    # ---------------- BUILD CITATION MAP ----------------
    citation_map = {}

    for chunk in retrieved_chunks:
        if not chunk.reference:
            continue

        if chunk.source == "OpenFDA":
            url = f"https://dailymed.nlm.nih.gov/dailymed/search.cfm?query={chunk.reference}"
            citation_map[url] = {
                "source": "FDA DailyMed",
                "title": f"DailyMed: {chunk.reference}",
                "url": url,
            }

        elif chunk.source == "PubChem":
            url = f"https://pubchem.ncbi.nlm.nih.gov/compound/{chunk.reference}"
            citation_map[url] = {
                "source": "PubChem",
                "title": f"PubChem: {chunk.reference}",
                "url": url,
            }

    # ---------------- MERGE EXISTING CITATIONS ----------------
    existing_citations = state.get("citations", [])
    for c in existing_citations:
        if c.get("url"):
            citation_map[c["url"]] = c

    citations = list(citation_map.values())
    state["citations"] = citations

    # ---------------- ATTACH TO ANSWER ----------------
    answer = (
        state.get("checked_answer")
        or state.get("draft_answer")
        or ""
    )

    if answer and citations:
        # Prevent duplicate appending
        if "Sources:" not in answer:
            citation_text = "\n".join(
                f"- [{c['source']}]({c['url']})"
                for c in citations
            )
            answer = f"{answer}\n\n**Sources:**\n{citation_text}"

    # Always set final_answer (important)
    state["final_answer"] = answer

    return state