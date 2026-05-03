import logging

from app.graph.state import GraphState
from app.services.medicine.resolver import extract_candidate_medicines, resolve_medicine_name

logger = logging.getLogger("node.resolver")


def medicine_resolver_agent(state: GraphState) -> GraphState:
    logger.info("Node hit: medicine_resolver_agent")
    candidates: list[str] = []

    if state.candidate_medicines:
        candidates.extend(state.candidate_medicines)

    if state.ocr_text:
        candidates.extend(extract_candidate_medicines(state.ocr_text))

    if state.raw_query:
        candidates.extend(extract_candidate_medicines(state.raw_query))

    deduped_candidates: list[str] = []
    seen: set[str] = set()
    for candidate in candidates:
        key = candidate.strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        deduped_candidates.append(candidate)

    state.candidate_medicines = deduped_candidates

    validation = resolve_medicine_name(
        medicine_name=state.medicine_name,
        query=state.raw_query,
        ocr_text=state.ocr_text,
        candidates=state.candidate_medicines,
    )

    state.resolved_medicine = validation.normalized_name
    state.confidence_score = validation.confidence_score
    if validation.openfda_data:
        state.openfda_data = validation.openfda_data
    if validation.pubchem_data:
        state.pubchem_data = validation.pubchem_data

    if not validation.normalized_name:
        state.warnings.append("Medicine resolver could not identify a medicine name.")

    return state
