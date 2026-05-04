import logging
from concurrent.futures import ThreadPoolExecutor

from app.graph.state import GraphState
from app.services.medicine.normalizer import build_retrieved_chunks
from app.services.medicine.resolver import resolve_medicine_name
from app.services.retrieval.openfda_client import fetch_openfda_data
from app.services.retrieval.pubchem_client import fetch_pubchem_data

logger = logging.getLogger("node.medicine_resolver")


def medicine_resolver_agent(state: GraphState) -> GraphState:
    logger.info("Node hit: medicine_resolver_agent")
    validation = resolve_medicine_name(
        medicine_name=state.medicine_name,
        input_text=state.input_text,
    )

    state.resolved_medicine = validation.normalized_name
    medicine_name = validation.normalized_name

    openfda_data: dict = {}
    pubchem_data: dict = {}

    if medicine_name:
        with ThreadPoolExecutor(max_workers=2) as executor:
            openfda_future = executor.submit(fetch_openfda_data, medicine_name)
            pubchem_future = executor.submit(fetch_pubchem_data, medicine_name)
            openfda_data = openfda_future.result() or {}
            pubchem_data = pubchem_future.result() or {}

    state.openfda_data = openfda_data
    state.pubchem_data = pubchem_data
    state.retrieved_chunks = build_retrieved_chunks(
        medicine_name=medicine_name or state.medicine_name or "Unknown Medicine",
        openfda_data=openfda_data or None,
        pubchem_data=pubchem_data or None,
    )

    if not validation.normalized_name:
        state.warnings.append("Resolver could not identify a medicine name.")
    elif not state.retrieved_chunks:
        state.warnings.append(f"No retrieval evidence found for '{validation.normalized_name}'.")

    return state
