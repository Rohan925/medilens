import logging

import requests

from app.domain.types import MetadataMap


logger = logging.getLogger("pubchem")

BASE_URL_PUG = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"


def fetch_pubchem_data(drug_name: str) -> MetadataMap | None:
    result: MetadataMap = {
        "drug_name": drug_name,
        "source": "PubChem",
        "molecular_formula": None,
        "molecular_weight": None,
        "description": None,
        "urls": [],
    }

    try:
        prop_url = (
            f"{BASE_URL_PUG}/compound/name/{drug_name}/property/"
            "MolecularFormula,MolecularWeight/JSON"
        )
        response = requests.get(prop_url, timeout=10)
        response.raise_for_status()
        data = response.json()
        properties = data.get("PropertyTable", {}).get("Properties", [])
        if properties:
            result["molecular_formula"] = properties[0].get("MolecularFormula")
            result["molecular_weight"] = properties[0].get("MolecularWeight")
            result["urls"].append(prop_url)
    except requests.RequestException as exc:
        logger.warning("PubChem properties request failed for %s: %s", drug_name, exc)
    except Exception as exc:
        logger.warning("PubChem properties parse failed for %s: %s", drug_name, exc)

    try:
        desc_url = f"{BASE_URL_PUG}/compound/name/{drug_name}/description/JSON"
        response = requests.get(desc_url, timeout=10)
        response.raise_for_status()
        data = response.json()
        infos = data.get("InformationList", {}).get("Information", [])
        for info in infos:
            description = info.get("Description")
            if not description:
                continue
            if "Journal" in description or "doi.org" in description:
                continue
            result["description"] = description
            break
        if infos:
            result["urls"].append(desc_url)
    except requests.RequestException as exc:
        logger.warning("PubChem description request failed for %s: %s", drug_name, exc)
    except Exception as exc:
        logger.warning("PubChem description parse failed for %s: %s", drug_name, exc)

    if not any(
        [
            result["molecular_formula"],
            result["molecular_weight"],
            result["description"],
        ]
    ):
        return None

    return result
