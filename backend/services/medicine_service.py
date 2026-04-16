from agents.coordinator_agent import coordinator_agent


async def get_medicine_data(medicine: str):

    initial_state = {
        "medicine_name": medicine,
        "mode": "summary"
    }

    final_state = await coordinator_agent(initial_state)

    structured = final_state.get("structured_summary") or {
        "drug_name": medicine.capitalize() if medicine else "Unknown Medicine",
        "category": "Unknown",
        "uses": [],
        "warnings": ["No verified medical data available."],
        "prescription_status": "Unknown",
    }

    return {
        "name": structured.get("drug_name"),
        "category": structured.get("category"),
        "uses": structured.get("uses", []),
        "warnings": structured.get("warnings", []),
        "prescription_status": structured.get("prescription_status"),
        "citations": final_state.get("citations", [])
    }
