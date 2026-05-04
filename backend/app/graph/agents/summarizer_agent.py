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

    state.structured_summary = build_medicine_summary(
        medicine_name=medicine_name,
        openfda_data=state.openfda_data,
        pubchem_data=state.pubchem_data,
    )

    summary = state.structured_summary
    has_quality_category = bool(summary and summary.category not in {"Unknown", "General Health"})
    has_substantive_details = bool(
        summary
        and (
            # summary.uses or
            summary.warnings
            or summary.mechanism
            or summary.summary_text
        )
    )
    needs_enrichment = not (has_quality_category and has_substantive_details)

    if needs_enrichment:
        logger.info("Summarizer using LLM enrichment fallback")
        evidence_text = "\n\n".join(chunk.text for chunk in state.retrieved_chunks)
        prompt = build_summary_enrichment_prompt(
            medicine_name=summary.drug_name,
            category=summary.category,
            uses=summary.uses,
            warnings=summary.warnings,
            prescription_status=summary.prescription_status,
            evidence_text=evidence_text,
        )
        output = openai_client.invoke_text(prompt)
        if output:
            category = _extract_section(output, "CATEGORY")
            uses = _parse_pipe_list(_extract_section(output, "USES"))
            warnings = _parse_pipe_list(_extract_section(output, "WARNINGS"))
            prescription_status = _extract_section(output, "PRESCRIPTION_STATUS")

            if category:
                summary.category = category
            if uses:
                summary.uses = uses[:6]
            if warnings:
                summary.warnings = warnings[:5]
            if prescription_status:
                summary.prescription_status = prescription_status

    return state
