

from typing import List
import requests

from core.config import Config
from core.models import RetrievedChunk


DRUGBANK_BASE_URL = "https://api.drugbank.com/v1"


def fetch_drugbank_drug_info(drug_name: str) -> List[RetrievedChunk]:
    """
    Fetch drug information from DrugBank.

    Returns a list of RetrievedChunk objects.
    """

    # If API key is not configured, fail safely
    if not Config.DRUGBANK_API_KEY:
        return []

    headers = {
        "Authorization": f"Bearer {Config.DRUGBANK_API_KEY}"
    }

    params = {
        "name": drug_name
    }

    try:
        response = requests.get(
            f"{DRUGBANK_BASE_URL}/drugs",
            headers=headers,
            params=params,
            timeout=10
        )
    except requests.RequestException:
        return []

    if response.status_code != 200:
        return []

    data = response.json()
    results = data.get("data", [])

    chunks: List[RetrievedChunk] = []

    for item in results:
        description = item.get("description")
        indications = item.get("indication")

        text_parts = []

        if description:
            text_parts.append(description)

        if indications:
            text_parts.append(indications)

        if not text_parts:
            continue

        chunks.append(
            RetrievedChunk(
                text=" ".join(text_parts),
                source="drugbank",
                reference=item.get("name", drug_name)
            )
        )

    return chunks
