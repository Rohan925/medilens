import logging

from app.graph.state import GraphState
from app.services.medicine.normalizer import build_retrieved_chunks
from app.services.medicine.resolver import extract_possible_medicine
from app.services.retrieval.openfda_client import fetch_openfda_data
from app.services.retrieval.pubchem_client import fetch_pubchem_data

logger = logging.getLogger("node.retriever")


def retriever_agent(state: GraphState) -> GraphState:
    logger.info("Node hit: retriever_agent")
    medicine_name = state.resolved_medicine or state.medicine_name

    if not medicine_name and state.raw_query:
        medicine_name = extract_possible_medicine(state.raw_query)

    if not medicine_name:
        state.warnings.append("No medicine could be determined for retrieval.")
        state.retrieved_chunks = []
        return state

    state.resolved_medicine = medicine_name

    query_lower = (state.raw_query or "").lower()
    need_pubchem = any(keyword in query_lower for keyword in ["formula", "structure", "weight"])
    need_openfda = True

    openfda_data = state.openfda_data or {}
    pubchem_data = state.pubchem_data or {}

    if need_openfda and not openfda_data:
        openfda_data = fetch_openfda_data(medicine_name) or {}
    if need_pubchem and not pubchem_data:
        pubchem_data = fetch_pubchem_data(medicine_name) or {}

    state.openfda_data = openfda_data
    state.pubchem_data = pubchem_data
    state.retrieved_chunks = build_retrieved_chunks(
        medicine_name=medicine_name,
        openfda_data=openfda_data or None,
        pubchem_data=pubchem_data or None,
    )

    if not state.retrieved_chunks:
        state.warnings.append(f"No retrieval evidence found for '{medicine_name}'.")

    return state
