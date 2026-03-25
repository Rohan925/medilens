import requests

BASE_URL = "https://api.fda.gov/drug/label.json"

def fetch_openfda_data(drug_name: str):
    try:
        # Prioritize Exact Matches to avoid "Metformin" matching "Zituvimet" (Metformin + Sitagliptin)
        # We REMOVED the broad fallback `openfda.generic_name:"{drug_name}"` because it returns combination drugs.
        queries = [
            f'openfda.brand_name.exact:"{drug_name.upper()}"',
            f'openfda.generic_name.exact:"{drug_name.upper()}"',
            f'openfda.substance_name.exact:"{drug_name.upper()}"' # New Safe Fallback (Active Ingredient)
        ]
        
        for q in queries:
            params = {
                "search": q,
                "limit": 1
            }
    
            print(f"DEBUG: Querying OpenFDA: {q}") # Added debug logging
            response = requests.get(BASE_URL, params=params)
            data = response.json()
    
            if "results" in data:
                # Found a match!
                result = data["results"][0]
                return {
                    "indications": result.get("indications_and_usage", []),
                    "warnings": result.get("warnings", []),
                    "dosage": result.get("dosage_and_administration", []),
                    "source": "OpenFDA",
                    "url": response.url
                }
        
        return None

    except Exception:
        return None
        return None
