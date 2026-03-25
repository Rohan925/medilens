
# backend/integrations/pubchem_client.py

from typing import List
import requests

from core.models import RetrievedChunk


PUBCHEM_BASE_URL = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"


def fetch_pubchem_compound_info(compound_name: str) -> List[RetrievedChunk]:
    """
    Fetch compound information from PubChem.

    Returns normalized RetrievedChunk objects.
    """

    chunks: List[RetrievedChunk] = []

    # Step 1: Get CID for compound name
    cid_url = f"{PUBCHEM_BASE_URL}/compound/name/{compound_name}/cids/JSON"

    try:
        cid_response = requests.get(cid_url, timeout=10)
    except requests.RequestException:
        return []

    if cid_response.status_code != 200:
        return []

    cid_data = cid_response.json()
    cids = cid_data.get("IdentifierList", {}).get("CID", [])

    if not cids:
        return []

    cid = cids[0]  # use first CID

    # Step 2: Fetch compound description
    desc_url = (
        f"{PUBCHEM_BASE_URL}/compound/cid/{cid}/description/JSON"
    )

    try:
        desc_response = requests.get(desc_url, timeout=10)
    except requests.RequestException:
        return []

    if desc_response.status_code != 200:
        return []

    desc_data = desc_response.json()
    descriptions = desc_data.get("InformationList", {}).get("Information", [])

    for info in descriptions:
        description_text = info.get("Description")

        if not description_text:
            continue

        chunks.append(
            RetrievedChunk(
                text=description_text.strip(),
                source="pubchem",
                reference=f"CID:{cid}"
            )
        )

    return chunks
