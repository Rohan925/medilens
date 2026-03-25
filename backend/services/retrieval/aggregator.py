from services.retrieval.openfda_service import fetch_openfda_data
from services.retrieval.pubchem_service import fetch_pubchem_data

def fetch_complete_medical_data(drug_name: str):
    fda_data = fetch_openfda_data(drug_name)
    pubchem_data = fetch_pubchem_data(drug_name)

    return {
        "drug_name": drug_name,
        "openfda": fda_data,
        "pubchem": pubchem_data
    }
