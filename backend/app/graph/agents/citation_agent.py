import logging

from app.domain.enums import SourceType
from app.domain.models import Citation
from app.graph.state import GraphState

logger = logging.getLogger("node.citation")


def citation_agent(state: GraphState) -> GraphState:
    logger.info("Node hit: citation_agent")
    citation_map: dict[str, Citation] = {}

    for chunk in state.retrieved_chunks:
        url: str | None = None
        label: str | None = None
        source = chunk.source

        if source == SourceType.OPENFDA or str(source) == SourceType.OPENFDA.value:
            url = state.openfda_data.get("url") if state.openfda_data else None
            label = f"DailyMed: {chunk.reference}" if chunk.reference else "FDA DailyMed"
            citation_source = "FDA DailyMed"
        elif source == SourceType.PUBCHEM or str(source) == SourceType.PUBCHEM.value:
            urls = state.pubchem_data.get("urls", []) if state.pubchem_data else []
            url = urls[0] if urls else None
            label = f"PubChem: {chunk.reference}" if chunk.reference else "PubChem"
            citation_source = "PubChem"
        else:
            citation_source = str(source)

        key = url or f"{citation_source}:{chunk.reference or chunk.text[:40]}"
        citation_map[key] = Citation(
            source=citation_source,
            url=url,
            label=label,
        )

    state.citations = list(citation_map.values())
    return state
