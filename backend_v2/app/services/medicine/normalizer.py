import re
import logging

from app.domain.enums import SourceType
from app.domain.models import MedicineSummary, RetrievedChunk
from app.domain.types import MetadataMap

logger = logging.getLogger("normalizer")


def clean_text_list(items: list[str] | list[list[str]] | None, max_items: int = 5) -> list[str]:
    if not items:
        return []

    flattened: list[str] = []
    for item in items:
        if isinstance(item, list):
            flattened.extend(str(value) for value in item)
        else:
            flattened.append(str(item))

    cleaned: list[str] = []
    seen: set[str] = set()

    for item in flattened:
        text = re.sub(r"<[^>]+>", "", item)
        text = re.sub(r"\s+", " ", text).strip()
        if len(text) <= 2:
            continue

        text = text[0].upper() + text[1:] if text else text
        key = text.lower()
        if key in seen:
            continue
        seen.add(key)
        cleaned.append(text)

        if len(cleaned) >= max_items:
            break

    return cleaned


def clean_use_points(items: list[str] | list[list[str]] | None, max_items: int = 6) -> list[str]:
    if not items:
        return []

    text = " ".join(
        str(value)
        for item in items
        for value in (item if isinstance(item, list) else [item])
    )
    text = re.sub(r"[\r\n\t]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    text = text.replace("\u2022", " • ")
    text = re.sub(r"(?i)\buses?\b\s*", "", text)
    text = re.sub(r"(?i)\bfor [^.]*(?:label)\b", "", text)
    text = re.sub(r"\s+", " ", text).strip()

    points: list[str] = []

    if "due to:" in text.lower():
        suffix = re.split(r"(?i)due to:", text, maxsplit=1)[1]
        parts = re.split(r"•|,|\s+and\s+", suffix)
        for part in parts:
            cleaned = re.sub(r"^[^a-zA-Z]+", "", part).strip(" .")
            if len(cleaned) > 2:
                cleaned = cleaned[0].upper() + cleaned[1:]
                if cleaned.lower().startswith("temporarily"):
                    continue
                if cleaned not in points:
                    points.append(cleaned)
            if len(points) >= max_items:
                return points[:max_items]

    sentences = re.split(r"[•.!]|(?:\s+-\s+)", text)
    for sentence in sentences:
        cleaned = re.sub(r"<[^>]+>", "", sentence)
        cleaned = re.sub(r"\s+", " ", cleaned).strip(" .:-")
        if len(cleaned) < 12:
            continue
        lowered = cleaned.lower()
        if any(
            lowered.startswith(prefix)
            for prefix in ["label", "temporarily reduces fever", "temporarily relieves"]
        ):
            continue
        cleaned = cleaned[0].upper() + cleaned[1:]
        if cleaned not in points:
            points.append(cleaned)
        if len(points) >= max_items:
            break

    logger.info("Normalizer cleaned uses: %s", points[:max_items])
    return points[:max_items]


def clean_warning_points(items: list[str] | list[list[str]] | None, max_items: int = 5) -> list[str]:
    if not items:
        return []

    text = " ".join(
        str(value)
        for item in items
        for value in (item if isinstance(item, list) else [item])
    )
    text = re.sub(r"[\r\n\t]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(
        r"(?i)^(warnings?\s*(and cautions)?|boxed warning)\s*[:\-]?\s*",
        "",
        text,
    )

    sentences = re.split(r"(?<=[.!?])\s+|•", text)
    points: list[str] = []
    seen: set[str] = set()
    for sentence in sentences:
        cleaned = re.sub(r"\s+", " ", sentence).strip(" .:-")
        if len(cleaned) < 10:
            continue
        cleaned = cleaned[0].upper() + cleaned[1:]
        key = cleaned.lower()
        if key in seen:
            continue
        seen.add(key)
        points.append(cleaned)
        if len(points) >= max_items:
            break

    logger.info("Normalizer cleaned warnings: %s", points[:max_items])
    return points[:max_items]


def build_retrieved_chunks(
    medicine_name: str,
    openfda_data: MetadataMap | None = None,
    pubchem_data: MetadataMap | None = None,
) -> list[RetrievedChunk]:
    chunks: list[RetrievedChunk] = []

    if openfda_data:
        indications = clean_use_points(openfda_data.get("indications"), max_items=5)
        warnings = clean_warning_points(openfda_data.get("warnings"), max_items=5)
        dosage = clean_text_list(openfda_data.get("dosage"), max_items=3)

        text_parts: list[str] = []
        if indications:
            text_parts.append(f"Indications: {', '.join(indications)}.")
        if warnings:
            text_parts.append(f"Warnings: {', '.join(warnings)}.")
        if dosage:
            text_parts.append(f"Dosage: {', '.join(dosage)}.")

        if text_parts:
            chunks.append(
                RetrievedChunk(
                    source=SourceType.OPENFDA,
                    text=" ".join(text_parts),
                    reference=medicine_name,
                    metadata=dict(openfda_data),
                )
            )

    if pubchem_data:
        text_parts: list[str] = []
        description = pubchem_data.get("description")
        molecular_formula = pubchem_data.get("molecular_formula")
        molecular_weight = pubchem_data.get("molecular_weight")

        if description:
            text_parts.append(f"Description: {description}.")
        if molecular_formula:
            text_parts.append(f"Molecular Formula: {molecular_formula}.")
        if molecular_weight:
            text_parts.append(f"Molecular Weight: {molecular_weight}.")

        if text_parts:
            chunks.append(
                RetrievedChunk(
                    source=SourceType.PUBCHEM,
                    text=" ".join(text_parts),
                    reference=medicine_name,
                    metadata=dict(pubchem_data),
                )
            )

    return chunks


def build_medicine_summary(
    medicine_name: str,
    openfda_data: MetadataMap | None = None,
    pubchem_data: MetadataMap | None = None,
) -> MedicineSummary:
    if not openfda_data and not pubchem_data:
        return MedicineSummary(
            drug_name=medicine_name.capitalize() if medicine_name else "Unknown Medicine",
            category="Unknown",
            uses=[],
            warnings=["No verified medical data available."],
            prescription_status="Unknown",
        )

    uses = clean_use_points((openfda_data or {}).get("indications"), max_items=6)
    warnings = clean_warning_points((openfda_data or {}).get("warnings"), max_items=5)
    mechanism = clean_text_list((openfda_data or {}).get("mechanism_of_action"), max_items=3)

    is_prescription = (openfda_data or {}).get("is_prescription")
    if is_prescription is True:
        prescription_status = "Prescription Required"
    elif is_prescription is False:
        prescription_status = "Over-the-Counter (OTC)"
    else:
        prescription_status = "Unknown"

    category = (
        (openfda_data or {}).get("pharm_class")
        or (openfda_data or {}).get("product_type")
        or "General Health"
    )

    summary_text: str | None = None
    if pubchem_data and pubchem_data.get("description"):
        summary_text = str(pubchem_data["description"]).strip()

    return MedicineSummary(
        drug_name=medicine_name.capitalize() if medicine_name else "Unknown Medicine",
        category=category,
        uses=uses,
        warnings=warnings or ["No verified warnings available."],
        prescription_status=prescription_status,
        mechanism=mechanism,
        summary_text=summary_text,
    )
