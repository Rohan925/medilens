from typing import Dict, Any, List
import re

from core.models import RetrievedChunk
from services.retrieval.openfda_service import fetch_openfda_data
from services.retrieval.pubchem_service import fetch_pubchem_data


def extract_possible_medicine(query: str) -> str:
    """
    Very lightweight medicine extractor
    (no LLM needed yet)
    """
    words = query.lower().split()

    # simple heuristic: assume longest meaningful word
    candidates = [w for w in words if len(w) > 4]

    return candidates[0] if candidates else ""


async def retriever_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    INTELLIGENT RETRIEVER

    - Decides what to retrieve based on query
    - Extracts medicine if not provided
    - Calls APIs selectively
    """

    query = state.get("query", "")
    chunks: List[RetrievedChunk] = []

    # ---------------- STEP 1: DETERMINE MEDICINE ----------------
    medicine_name = state.get("medicine_name")

    if not medicine_name:
        medicine_name = extract_possible_medicine(query)

    if not medicine_name:
        # Likely symptom/general query → no retrieval needed
        state["retrieved_chunks"] = []
        return state

    # ---------------- STEP 2: DECIDE API USAGE ----------------
    # simple intent detection
    query_lower = query.lower()

    need_pubchem = any(k in query_lower for k in ["formula", "structure", "weight"])
    need_fda = True  # default for medical queries

    # ---------------- STEP 3: PUBCHEM ----------------
    if need_pubchem:
        pubchem_data = fetch_pubchem_data(medicine_name)

        if pubchem_data:
            text_content = (
                f"Description: {pubchem_data.get('description', '')}. "
                f"Molecular Formula: {pubchem_data.get('molecular_formula', '')}. "
                f"Molecular Weight: {pubchem_data.get('molecular_weight', '')}."
            )

            chunks.append(RetrievedChunk(
                source="PubChem",
                text=text_content,
                reference=medicine_name
            ))

    # ---------------- STEP 4: OPENFDA ----------------
    if need_fda:
        fda_data = fetch_openfda_data(medicine_name)

        if fda_data:
            indications = fda_data.get("indications", [])
            warnings = fda_data.get("warnings", [])
            dosage = fda_data.get("dosage", [])

            text_content = (
                f"Indications: {', '.join(indications[:5])}. "
                f"Warnings: {', '.join(warnings[:5])}. "
                f"Dosage: {', '.join(dosage[:3])}."
            )

            chunks.append(RetrievedChunk(
                source="OpenFDA",
                text=text_content,
                reference=medicine_name
            ))

            state["drug_metadata"] = {
                "is_prescription": fda_data.get("is_prescription"),
                "pharm_class": fda_data.get("pharm_class"),
                "category": fda_data.get("product_type"),
                "prescription_status": (
                    "OTC" if not fda_data.get("is_prescription") else "Prescription"
                ),
                "uses": indications,
                "warnings": warnings,
            }

    # ---------------- STEP 5: FALLBACK ----------------
    if not chunks:
        state["retrieved_chunks"] = []
        return state

    state["retrieved_chunks"] = chunks
    return state