print("🔥 drug_name_extractor LOADED")

from email.charset import ALIASES
import re
import requests

OPENFDA_URL = "https://api.fda.gov/drug/drugsfda.json"

NON_DRUG_TERMS = {
    "tablet", "tablets", "capsule", "capsules",
    "mg", "ml", "syrup", "injection",
    "dose", "dosage", "oral",
    "medicine", "drug"
}


def normalize_ocr_text(text: str) -> str:
    """
    Clean common OCR noise
    """
    text = text.lower()

    # Remove isolated single letters (i, l, etc.)
    text = re.sub(r"\b[a-z]\b", " ", text)

    # Collapse whitespace
    text = re.sub(r"\s+", " ", text)

    print("CLEAN OCR TEXT:", text)
    return text.strip()


def extract_candidate_tokens(text: str) -> set[str]:
    """
    Extract word-like tokens AFTER normalization
    """
    return set(re.findall(r"\b[a-z]{4,}\b", text))


def extract_drug_names(text: str) -> list[str]:
    print("RAW OCR TEXT:", text)

    clean_text = normalize_ocr_text(text)
    candidates = extract_candidate_tokens(clean_text)

    validated_drugs = set()

    for token in candidates:
        if token in NON_DRUG_TERMS:
            continue

        params = {
    "search": (
    f'products.brand_name:{token} '
    f'OR products.active_ingredients.name:{token}'
),
    "limit": 1
}

        try:
            response = requests.get(
                OPENFDA_URL,
                params=params,
                timeout=3
            )

            if response.status_code == 200:
                data = response.json()
                if "results" in data:
                    validated_drugs.add(token)

        except requests.exceptions.RequestException:
            continue

    return list(validated_drugs)

def normalize_drug_name(name: str) -> str:
    """
    Normalize drug names for external data sources (PubChem, OpenFDA).
    """
    if not name:
        return ""

    return ALIASES.get(name.lower(), name.lower())