import logging
import re

from app.graph.state import GraphState
from app.services.medicine.normalizer import build_medicine_summary
from app.services.llm.openai_client import openai_client
from app.services.llm.prompts import build_summary_enrichment_prompt

logger = logging.getLogger("node.summarizer")


def _parse_pipe_list(raw_text: str) -> list[str]:
    parts = [part.strip() for part in raw_text.split("|")]
    return [part for part in parts if part]


def _extract_section(text: str, label: str) -> str:
    pattern = rf"{label}:\s*(.*)"
    match = re.search(pattern, text, flags=re.IGNORECASE)
    return match.group(1).strip() if match else ""


def summarizer_agent(state: GraphState) -> GraphState:
    logger.info("Node hit: summarizer_agent")
    medicine_name = state.resolved_medicine or state.medicine_name or "Unknown Medicine"
    has_openfda_data = bool(state.openfda_data)
    has_pubchem_data = bool(state.pubchem_data)

    state.structured_summary = build_medicine_summary(
        medicine_name=medicine_name,
        openfda_data=state.openfda_data,
        pubchem_data=state.pubchem_data,
    )

    needs_enrichment = (
        not has_openfda_data
        or not has_pubchem_data
        or not state.structured_summary.uses
        or not state.structured_summary.warnings
    )

    if needs_enrichment:
        logger.info("Summarizer using LLM enrichment fallback")
        evidence_text = "\n\n".join(chunk.text for chunk in state.retrieved_chunks)
        prompt = build_summary_enrichment_prompt(
            medicine_name=state.structured_summary.drug_name,
            category=state.structured_summary.category,
            uses=state.structured_summary.uses,
            warnings=state.structured_summary.warnings,
            prescription_status=state.structured_summary.prescription_status,
            evidence_text=evidence_text,
        )
        output = openai_client.invoke_text(prompt)
        if output:
            category = _extract_section(output, "CATEGORY")
            uses = _parse_pipe_list(_extract_section(output, "USES"))
            warnings = _parse_pipe_list(_extract_section(output, "WARNINGS"))
            prescription_status = _extract_section(output, "PRESCRIPTION_STATUS")

            if category:
                state.structured_summary.category = category
            if uses:
                state.structured_summary.uses = uses[:6]
            if warnings:
                state.structured_summary.warnings = warnings[:5]
            if prescription_status:
                state.structured_summary.prescription_status = prescription_status

    return state
