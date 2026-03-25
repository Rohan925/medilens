from typing import Dict, Any, List
from core.models import RetrievedChunk
from services.retrieval.openfda_service import fetch_openfda_data
from services.retrieval.pubchem_service import fetch_pubchem_data


async def retriever_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    medicine_name = (state.get("medicine_name") or "").lower()
    chunks: List[RetrievedChunk] = []

    if not medicine_name:
        state["retrieved_chunks"] = []
        return state

    # --- PubChem ---
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

    # --- OpenFDA ---
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

        # Structured metadata for ready-to-use summary
        state["drug_metadata"] = {
            "is_prescription": fda_data.get("is_prescription"), # Essential for summarizer
            "pharm_class": fda_data.get("pharm_class"),
            "category": fda_data.get("product_type"),
            "prescription_status": (
                "Over-the-Counter (OTC)"
                if not fda_data.get("is_prescription")
                else "Prescription Required"
            ),
            "uses": indications,
            "warnings": warnings,
        }
    
    # --- FALLBACK: If OpenFDA failed but PubChem succeeded ---
    elif pubchem_data and not state.get("drug_metadata"):
        # Use PubChem description to fill the gap
        desc = pubchem_data.get("description", "")
        # Clean up description for "Uses"
        # Just take the first 2 sentences to keep it brief
        parts = desc.split('. ')
        short_desc = ". ".join(parts[:2]) + "." if parts else "No description available."
        
        state["drug_metadata"] = {
            "is_prescription": None, # Unknown
            "pharm_class": "General Information",
            "category": "Unclassified",
            "prescription_status": "Unknown",
            "uses": [short_desc],
            "warnings": ["Consult a doctor for detailed safety information."],
        }

    state["retrieved_chunks"] = chunks
    return state
