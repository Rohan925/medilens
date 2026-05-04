import logging

from app.domain.enums import RequestMode
from app.graph.state import GraphState

logger = logging.getLogger("node.formatter")


def response_formatter_agent(state: GraphState) -> GraphState:
    logger.info("Node hit: response_formatter_agent")
    summary = state.structured_summary

    if state.mode == RequestMode.SEARCH:
        state.response = {
            "name": summary.drug_name if summary else state.resolved_medicine,
            "category": summary.category if summary else "Unknown",
            "uses": summary.uses if summary else [],
            "warnings": summary.warnings if summary else [],
            "prescription_status": summary.prescription_status if summary else "Unknown",
            "mechanism": summary.mechanism if summary else [],
            "citations": [citation.model_dump() for citation in state.citations],
        }
        return state

    if state.mode == RequestMode.CHAT:
        state.response = {
            "response": state.final_answer or "I'm sorry, I couldn't generate a response.",
        }
        return state

    if state.mode == RequestMode.OCR:
        medicine_name = (
            state.resolved_medicine
            or state.medicine_name
            or "Unknown"
        )
        state.response = {
            "medicine": medicine_name,
            "success": bool(state.resolved_medicine or state.medicine_name),
            "confidence": state.ocr_confidence,
            "summary": {
                "category": summary.category if summary else "Unknown",
                "uses": summary.uses if summary else [],
                "warnings": summary.warnings if summary else [],
                "prescription_status": summary.prescription_status if summary else "Unknown",
                "mechanism": summary.mechanism if summary else [],
                "side_effects": summary.side_effects if summary else [],
                "text": summary.summary_text if summary else None,
            }
            if summary
            else None,
            "citations": [citation.model_dump() for citation in state.citations],
            "is_strict_fallback": not bool(state.resolved_medicine or state.medicine_name),
            "error": state.error_message,
        }
        return state

    state.response = {}
    return state
