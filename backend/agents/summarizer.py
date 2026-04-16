from typing import Dict, Any, List
import re


def clean_text_list(text_list: List[str], max_items: int = 5) -> List[str]:
    """Basic cleaning without over-LLM dependency"""
    cleaned = []

    for item in text_list:
        s = str(item).strip()

        # Remove HTML
        s = re.sub(r'<[^>]+>', '', s)

        # Normalize whitespace
        s = re.sub(r'\s+', ' ', s).strip()

        if len(s) > 10:
            cleaned.append(s.capitalize())

    # Deduplicate + limit
    return list(dict.fromkeys(cleaned))[:max_items]


async def summariser_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    SUMMARISER AGENT (CLEAN VERSION)

    Responsibilities:
    - Convert raw metadata → structured summary
    - Keep deterministic (no heavy LLM logic)
    - Safe fallback handling
    """

    metadata = state.get("drug_metadata", {})
    medicine_name = state.get("medicine_name") or "Unknown Medicine"

    # ---------------- NO METADATA ----------------
    if not metadata:
        state["structured_summary"] = {
            "drug_name": medicine_name.capitalize(),
            "category": "Unknown",
            "uses": [],
            "warnings": ["No verified medical data available."],
            "prescription_status": "Unknown"
        }
        return state

    # ---------------- CLEAN DATA ----------------
    uses_raw = metadata.get("indications") or metadata.get("uses") or []
    warnings_raw = metadata.get("warnings") or []

    uses = clean_text_list(uses_raw, max_items=6)
    warnings = clean_text_list(warnings_raw, max_items=5)

    # ---------------- RX STATUS ----------------
    is_rx = metadata.get("is_prescription")

    if is_rx is True:
        rx_status = "Prescription Required"
    elif is_rx is False:
        rx_status = "Over-the-Counter (OTC)"
    else:
        rx_status = "Unknown"

    # ---------------- FINAL STRUCT ----------------
    structured_summary = {
        "drug_name": medicine_name.capitalize(),
        "category": metadata.get("pharm_class") or metadata.get("category") or "General Health",
        "uses": uses,
        "warnings": warnings or ["No verified warnings available."],
        "prescription_status": rx_status
    }

    state["structured_summary"] = structured_summary
    return state