from typing import Dict, Any, List
from core.models import RetrievedChunk


async def summariser_agent(state: Dict[str, Any]) -> Dict[str, Any]:

    metadata = state.get("drug_metadata", {})
    medicine_name = state.get("medicine_name") or "Unknown Medicine"  # Ensure string

    # If no metadata → safe fallback
    if not metadata:
        state["structured_summary"] = {
            "drug_name": medicine_name.capitalize(),
            "category": "Unknown",
            "uses": [],
            "warnings": ["No verified medical data available."],
            "prescription_status": "Unknown"
        }
        return state

    # --- Clean Uses via Strict LLM ---
    async def clean_uses(text_list):
        if not text_list:
            return []
            
        from core.llm_client import llm_client
        import re
        
        # Format raw FDA text by flattening and stripping HTML
        raw_text = " ".join([str(item) for item in text_list])
        raw_text = re.sub(r'<[^>]+>', '', raw_text) # strip HTML tags safely
        raw_text = re.sub(r'\s+', ' ', raw_text).strip()
        
        # Attempt extraction from LLM with validation retry
        max_attempts = 2
        for attempt in range(max_attempts):
            llm_response = await llm_client.extract_indications(raw_text)
            
            # Parse into a list
            bullets = [b.strip().lstrip('-').lstrip('*').strip() for b in llm_response.split('\n') if b.strip()]
            
            validated = []
            seen = set()
            
            blacklist = ["indications and usage", "indications", "is indicated for", "is a factor", "inhibitor", "mechanism", "header"]
            
            for b_idx in range(len(bullets)):
                b = bullets[b_idx]
                
                # Rule 2: Length validation
                if len(b) > 130: # Soft buffer on 120
                    continue
                    
                # Clean stray numbers/bullets from LLM formats like "1. " or "- "
                b = re.sub(r'^[\d\.\-\*]+\s*', '', b)
                
                # Rule 5: Deduplication
                b_lower = b.lower()
                
                # Rule 3/4: Reject headers or mechanism hallucinates
                if any(x in b_lower for x in blacklist):
                    continue
                    
                if b_lower not in seen and len(b) > 5:
                    validated.append(b)
                    seen.add(b_lower)
            
            # Rule 1: Limit to 6 items exactly
            validated = validated[:6]
            
            # Validation success check: ensure we got reasonable output
            # If not, try 1 more time
            if validated:
                return [v[0].upper() + v[1:] for v in validated]
            
        print("DEBUG LLM EXHAUSTED: Failed Validation, falling back to raw list")
        # Extreme fallback if LLM breaks entirely
        return ["Consult medical label for full indications."]

    # --- Clean Warnings ---
    def clean_warnings(text_list):
        if not text_list:
            return []

        cleaned = []
        for item in text_list:
            s = str(item).strip()
            # Only keep substantial warnings
            if len(s) > 10:
                # User requested NO EMOJIS
                cleaned.append(s.capitalize())

        return list(dict.fromkeys(cleaned))[:5]

    # Standardize Prescription Status
    rx_status = "Unknown"
    is_rx = metadata.get("is_prescription")
    if is_rx is True:
        rx_status = "Prescription Required"
    elif is_rx is False:
        rx_status = "Over-the-Counter (OTC)"

    structured_summary = {
        "drug_name": medicine_name.capitalize(),
        "category": metadata.get("pharm_class") or metadata.get("category") or "General Health",
        "uses": await clean_uses(metadata.get("indications", []) or metadata.get("uses", [])),
        "warnings": clean_warnings(metadata.get("warnings", [])),
        "prescription_status": rx_status
    }
    
    # Handle "No verified medical data" case if essential fields are empty
    if not structured_summary["uses"] and not structured_summary["warnings"]:
         structured_summary["warnings"] = ["No verified medical data available."]

    state["structured_summary"] = structured_summary
    return state