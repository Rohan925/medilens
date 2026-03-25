# backend/integrations/openfda_client.py

from typing import List
import requests

from core.config import Config
from core.models import RetrievedChunk


def _query_openfda(search_query: str) -> list:
    """
    Internal helper to query OpenFDA safely.
    """
    params = {
        "search": search_query,
        "limit": Config.TOP_K_RESULTS,
    }

    try:
        response = requests.get(
            Config.OPENFDA_BASE_URL,
            params=params,
            headers={
                "User-Agent": "MediLens/1.0 (academic-project)"
            },
            timeout=10,
        )
    except requests.RequestException:
        return []

    if response.status_code != 200:
        return []

    data = response.json()
    return data.get("results", [])

import requests

def fetch_drug_data(medicine_name: str) -> dict:
    url = (
        "https://api.fda.gov/drug/label.json"
        f"?search=openfda.generic_name:\"{medicine_name}\"&limit=1"
    )

    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()

        if "results" not in data or not data["results"]:
            return {}

        return data["results"][0]

    except requests.exceptions.RequestException as e:
        print(f"OpenFDA error: {e}")
        return {}   # ✅ IMPORTANT: return empty dict, NOT crash
