import logging
import re

import requests

from app.domain.types import MetadataMap


logger = logging.getLogger("openfda")

BASE_URL = "https://api.fda.gov/drug/label.json"

SYNONYMS = {
    "paracetamol": "acetaminophen",
    "tylenol": "acetaminophen",
    "advil": "ibuprofen",
    "motrin": "ibuprofen",
    "aleve": "naproxen",
    "aspirin": "aspirin",
}


def _flatten_text_list(text_list: list[str] | list[list[str]] | None) -> list[str]:
    if not text_list:
        return []

    flat_list: list[str] = []
    for item in text_list:
        if isinstance(item, list):
            flat_list.extend(str(value) for value in item)
        else:
            flat_list.append(str(item))
    return flat_list


def _format_warning_points(text_list: list[str] | list[list[str]] | None, max_items: int = 5) -> list[str]:
    flat_list = _flatten_text_list(text_list)
    if not flat_list:
        return []

    keywords = [
        "liver",
        "bleeding",
        "heart",
        "stroke",
        "allergy",
        "damage",
        "stomach",
        "alcohol",
        "fatal",
        "risk",
        "interaction",
        "pregnant",
    ]
    text = " ".join(flat_list)
    text = re.sub(r"[\r\n\t]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(
        r"^(?:warnings\s+and\s+cautions|warnings|boxed warning)\s*[:\-]?\s*",
        "",
        text,
        flags=re.IGNORECASE,
    )
    sentences = re.split(r"[.!\•]|(?:\s+-\s+)", text)

    warnings: list[str] = []
    for sentence in sentences:
        cleaned = sentence.strip()
        if not cleaned or len(cleaned) < 15:
            continue

        lowered = cleaned.lower()
        if any(keyword in lowered for keyword in keywords):
            cleaned = cleaned[0].upper() + cleaned[1:]
            if cleaned not in warnings:
                warnings.append(cleaned)

    if not warnings:
        for sentence in sentences:
            cleaned = sentence.strip()
            if len(cleaned) >= 15:
                cleaned = cleaned[0].upper() + cleaned[1:]
                if cleaned not in warnings:
                    warnings.append(cleaned)

    return warnings[:max_items]


def resolve_search_name(drug_name: str) -> str:
    return SYNONYMS.get(drug_name.lower(), drug_name)


def fetch_openfda_data(drug_name: str) -> MetadataMap | None:
    search_name = resolve_search_name(drug_name)
    queries = [
        f'openfda.brand_name.exact:"{search_name.upper()}"',
        f'openfda.generic_name.exact:"{search_name.upper()}"',
        f'openfda.substance_name.exact:"{search_name.upper()}"',
    ]

    try:
        result: MetadataMap | None = None
        for query in queries:
            response = requests.get(
                BASE_URL,
                params={"search": query, "limit": 1},
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()
            if "results" in data:
                result = data["results"][0]
                break

        if not result:
            return None

        openfda = result.get("openfda", {})
        product_types = openfda.get("product_type", [])
        product_type = "Unknown"
        is_prescription = True

        if product_types:
            product_type = str(product_types[0]).upper()
            if "OTC" in product_type:
                is_prescription = False
            elif "PRESCRIPTION" in product_type:
                is_prescription = True

        raw_class = ""
        if openfda.get("pharm_class_epc"):
            raw_class = openfda["pharm_class_epc"][0]
        elif openfda.get("pharm_class_cs"):
            raw_class = openfda["pharm_class_cs"][0]

        if raw_class:
            pharm_class = re.sub(r"\s*\[.*?\]", "", raw_class).strip()
        elif product_type != "Unknown":
            pharm_class = product_type.title().replace("Human ", "")
        else:
            pharm_class = "Unclassified"

        raw_uses = result.get("indications_and_usage", []) or result.get("purpose", [])
        raw_warnings = (
            result.get("warnings", [])
            or result.get("warnings_and_cautions", [])
            or result.get("boxed_warning", [])
        )

        return {
            "drug_name": drug_name,
            "search_name": search_name,
            "indications": raw_uses,
            "warnings": _format_warning_points(raw_warnings, max_items=5),
            "dosage": result.get("dosage_and_administration", []),
            "mechanism_of_action": result.get("mechanism_of_action", []),
            "active_ingredient": result.get("active_ingredient", []),
            "purpose": result.get("purpose", []),
            "source": "OpenFDA",
            "url": f"https://dailymed.nlm.nih.gov/dailymed/search.cfm?query={search_name}",
            "product_type": product_type,
            "is_prescription": is_prescription,
            "pharm_class": pharm_class,
            "set_id": openfda.get("spl_set_id", [None])[0],
        }
    except requests.RequestException as exc:
        logger.warning("OpenFDA request failed for %s: %s", drug_name, exc)
        return None
    except Exception as exc:
        logger.warning("OpenFDA parse failed for %s: %s", drug_name, exc)
        return None
