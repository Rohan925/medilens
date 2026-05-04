import logging
from concurrent.futures import ThreadPoolExecutor

from app.graph.state import GraphState
from app.services.medicine.normalizer import build_retrieved_chunks
from app.services.medicine.resolver import extract_candidate_medicines, resolve_medicine_name
from app.services.retrieval.openfda_client import fetch_openfda_data
from app.services.retrieval.pubchem_client import fetch_pubchem_data

logger = logging.getLogger("node.medicine_resolver")


def _dedupe_candidates(candidates: list[str]) -> list[str]:
    deduped: list[str] = []
    seen: set[str] = set()
    for candidate in candidates:
        key = candidate.strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        deduped.append(candidate)
    return deduped


def medicine_resolver_agent(state: GraphState) -> GraphState:
    logger.info("Node hit: medicine_resolver_agent")
    candidates: list[str] = []

    if state.search_text:
        candidates.extend(extract_candidate_medicines(state.search_text))

    if state.raw_query and state.raw_query != state.search_text:
        candidates.extend(extract_candidate_medicines(state.raw_query))

    candidates = _dedupe_candidates(candidates)

    validation = resolve_medicine_name(
        medicine_name=state.medicine_name,
        query=state.raw_query,
        candidates=candidates,
        search_text=state.search_text,
    )

    state.resolved_medicine = validation.normalized_name
    medicine_name = validation.normalized_name

    openfda_data = validation.openfda_data or {}
    pubchem_data = validation.pubchem_data or {}

    if medicine_name:
        with ThreadPoolExecutor(max_workers=2) as executor:
            openfda_future = None
            pubchem_future = None

            if not openfda_data:
                openfda_future = executor.submit(fetch_openfda_data, medicine_name)
            if not pubchem_data:
                pubchem_future = executor.submit(fetch_pubchem_data, medicine_name)

            if openfda_future is not None:
                openfda_data = openfda_future.result() or {}
            if pubchem_future is not None:
                pubchem_data = pubchem_future.result() or {}

    state.openfda_data = openfda_data
    state.pubchem_data = pubchem_data
    state.retrieved_chunks = build_retrieved_chunks(
        medicine_name=medicine_name or state.medicine_name or "Unknown Medicine",
        openfda_data=openfda_data or None,
        pubchem_data=pubchem_data or None,
    )

    if not validation.normalized_name:
        state.warnings.append("Search agent could not identify a medicine name.")
    elif not state.retrieved_chunks:
        state.warnings.append(f"No retrieval evidence found for '{validation.normalized_name}'.")

    return state
