import logging

from app.graph.state import GraphState
from app.services.medicine.normalizer import build_medicine_summary

logger = logging.getLogger("node.summarizer")


def summarizer_agent(state: GraphState) -> GraphState:
    logger.info("Node hit: summarizer_agent")
    medicine_name = state.resolved_medicine or state.medicine_name or "Unknown Medicine"

    state.structured_summary = build_medicine_summary(
        medicine_name=medicine_name,
        openfda_data=state.openfda_data,
        pubchem_data=state.pubchem_data,
    )

    return state
