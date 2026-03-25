import requests
import logging

BASE_URL_PUG = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"

def fetch_pubchem_data(drug_name: str):
    """
    Fetches molecular properties and description from PubChem.
    """
    result = {
        "source": "PubChem",
        "molecular_formula": None,
        "molecular_weight": None,
        "description": None,
        "urls": []
    }

    # 1. Fetch Properties (Formula, Weight)
    try:
        prop_url = f"{BASE_URL_PUG}/compound/name/{drug_name}/property/MolecularFormula,MolecularWeight/JSON"
        response = requests.get(prop_url, timeout=30)
        if response.status_code == 200:
            data = response.json()
            if "PropertyTable" in data and "Properties" in data["PropertyTable"]:
                properties = data["PropertyTable"]["Properties"][0]
                result["molecular_formula"] = properties.get("MolecularFormula")
                result["molecular_weight"] = properties.get("MolecularWeight")
                result["urls"].append(prop_url)
    except Exception as e:
        logging.error(f"Error fetching PubChem properties for {drug_name}: {e}")

    # 2. Fetch Description
    try:
        desc_url = f"{BASE_URL_PUG}/compound/name/{drug_name}/description/JSON"
        response = requests.get(desc_url, timeout=30)
        if response.status_code == 200:
            data = response.json()
            if "InformationList" in data and "Information" in data["InformationList"]:
                # Get the first description
                infos = data["InformationList"]["Information"]
                for info in infos:
                    if "Description" in info:
                        desc = info["Description"]
                        # Remove boilerplate
                        if "Journal" in desc or "doi.org" in desc:
                            continue
                        result["description"] = desc
                        break
                result["urls"].append(desc_url)
    except Exception as e:
        logging.error(f"Error fetching PubChem description for {drug_name}: {e}")

    # Return None if we found nothing useful
    if not any([result["molecular_formula"], result["molecular_weight"], result["description"]]):
        return None

    return result
