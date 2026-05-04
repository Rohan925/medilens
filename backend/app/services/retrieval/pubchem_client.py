from concurrent.futures import ThreadPoolExecutor
import logging

import requests

from app.domain.types import MetadataMap


logger = logging.getLogger("pubchem")

BASE_URL_PUG = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"


def _fetch_pubchem_properties(drug_name: str) -> tuple[str | None, str | None, str | None]:
    prop_url = (
        f"{BASE_URL_PUG}/compound/name/{drug_name}/property/"
        "MolecularFormula,MolecularWeight/JSON"
    )
    try:
        logger.info("PubChem properties request start: drug=%s url=%s", drug_name, prop_url)
        response = requests.get(prop_url, timeout=10)
        response.raise_for_status()
        data = response.json()
        properties = data.get("PropertyTable", {}).get("Properties", [])
        if not properties:
            return None, None, None
        return (
            properties[0].get("MolecularFormula"),
            properties[0].get("MolecularWeight"),
            prop_url,
        )
    except requests.RequestException as exc:
        logger.warning("PubChem properties request failed for %s: %s", drug_name, exc)
        return None, None, None
    except Exception as exc:
        logger.warning("PubChem properties parse failed for %s: %s", drug_name, exc)
        return None, None, None


def _fetch_pubchem_description(drug_name: str) -> tuple[str | None, str | None]:
    desc_url = f"{BASE_URL_PUG}/compound/name/{drug_name}/description/JSON"
    try:
        logger.info("PubChem description request start: drug=%s url=%s", drug_name, desc_url)
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
            return description, desc_url
        return None, desc_url if infos else None
    except requests.RequestException as exc:
        logger.warning("PubChem description request failed for %s: %s", drug_name, exc)
        return None, None
    except Exception as exc:
        logger.warning("PubChem description parse failed for %s: %s", drug_name, exc)
        return None, None


def fetch_pubchem_data(drug_name: str) -> MetadataMap | None:
    result: MetadataMap = {
        "drug_name": drug_name,
        "source": "PubChem",
        "molecular_formula": None,
        "molecular_weight": None,
        "description": None,
        "urls": [],
    }

    with ThreadPoolExecutor(max_workers=2) as executor:
        properties_future = executor.submit(_fetch_pubchem_properties, drug_name)
        description_future = executor.submit(_fetch_pubchem_description, drug_name)

        molecular_formula, molecular_weight, prop_url = properties_future.result()
        description, desc_url = description_future.result()

    result["molecular_formula"] = molecular_formula
    result["molecular_weight"] = molecular_weight
    result["description"] = description

    if prop_url:
        result["urls"].append(prop_url)
    if desc_url:
        result["urls"].append(desc_url)

    if not any(
        [
            result["molecular_formula"],
            result["molecular_weight"],
            result["description"],
        ]
    ):
        return None

    return result
