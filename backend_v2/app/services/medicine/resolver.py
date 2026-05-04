import re
from dataclasses import dataclass
import logging

from app.services.llm.openai_client import openai_client
from app.services.llm.prompts import (
    build_medicine_normalization_prompt,
    build_search_interpretation_prompt,
)
from app.services.retrieval.openfda_client import fetch_openfda_data
from app.services.retrieval.pubchem_client import fetch_pubchem_data
from app.domain.types import MetadataMap

logger = logging.getLogger("resolver")


STOPWORDS = {
    "tablet",
    "tablets",
    "capsule",
    "capsules",
    "syrup",
    "suspension",
    "injection",
    "cream",
    "gel",
    "ointment",
    "drops",
    "solution",
    "pain",
    "relief",
    "extra",
    "strength",
    "mg",
    "ml",
    "g",
    "mcg",
    "batch",
    "expiry",
    "mfg",
    "dosage",
    "physician",
    "children",
    "contains",
    "coated",
    "usp",
    "ip",
    "bp",
}


@dataclass
class MedicineValidationResult:
    normalized_name: str | None
    openfda_data: MetadataMap | None = None
    pubchem_data: MetadataMap | None = None


def normalize_candidate(value: str) -> str:
    text = re.sub(r"[^A-Za-z\s\-]", " ", value or "")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def validate_medicine_name(candidate: str) -> MedicineValidationResult | None:
    normalized = normalize_candidate(candidate)
    if not normalized:
        return None

    logger.info("Resolver validation start: candidate=%r", normalized)
    openfda_data = fetch_openfda_data(normalized)
    if openfda_data:
        logger.info("Resolver validation success via OpenFDA: candidate=%r", normalized)
        return MedicineValidationResult(
            normalized_name=normalized,
            openfda_data=openfda_data,
        )

    pubchem_data = fetch_pubchem_data(normalized)
    if pubchem_data:
        logger.info("Resolver validation success via PubChem: candidate=%r", normalized)
        return MedicineValidationResult(
            normalized_name=normalized,
            pubchem_data=pubchem_data,
        )

    logger.info("Resolver validation failed: candidate=%r", normalized)
    return None


def llm_normalize_medicine_name(
    raw_input: str,
    candidates: list[str] | None = None,
) -> str | None:
    if not openai_client.available or not raw_input.strip():
        logger.info("Resolver LLM normalization skipped: available=%s raw_input_present=%s", openai_client.available, bool(raw_input.strip()))
        return None

    logger.info("Resolver LLM normalization start: raw_input=%r candidates=%s", raw_input[:200], candidates or [])
    prompt = build_medicine_normalization_prompt(
        raw_input=raw_input,
        candidates=candidates,
    )
    output_text = openai_client.invoke_text(prompt)
    if not output_text:
        logger.info("Resolver LLM normalization returned no output")
        return None

    normalized = output_text.splitlines()[0].strip().strip("\"'")
    if normalized.upper() == "UNKNOWN":
        logger.info("Resolver LLM normalization returned UNKNOWN")
        return None

    logger.info("Resolver LLM normalization success: normalized=%r", normalized)
    return normalized


def llm_interpret_search_text(search_text: str) -> str | None:
    if not openai_client.available or not search_text.strip():
        logger.info(
            "Resolver search interpretation skipped: available=%s search_text_present=%s",
            openai_client.available,
            bool(search_text.strip()),
        )
        return None

    logger.info("Resolver search interpretation start: search_text=%r", search_text[:200])
    prompt = build_search_interpretation_prompt(search_text)
    output_text = openai_client.invoke_text(prompt)
    if not output_text:
        logger.info("Resolver search interpretation returned no output")
        return None

    normalized = output_text.splitlines()[0].strip().strip("\"'")
    if normalized.upper() == "UNKNOWN":
        logger.info("Resolver search interpretation returned UNKNOWN")
        return None

    logger.info("Resolver search interpretation success: normalized=%r", normalized)
    return normalized


def extract_candidate_medicines(text: str, max_candidates: int = 5) -> list[str]:
    normalized = normalize_candidate(text).lower()
    if not normalized:
        return []

    words = normalized.split()
    candidates: list[str] = []
    seen: set[str] = set()

    for word in sorted(words, key=len, reverse=True):
        if len(word) <= 3:
            continue
        if word in STOPWORDS:
            continue
        if word in seen:
            continue
        seen.add(word)
        candidates.append(word.title())
        if len(candidates) >= max_candidates:
            break

    return candidates


def resolve_medicine_name(
    medicine_name: str | None = None,
    query: str | None = None,
    candidates: list[str] | None = None,
    search_text: str | None = None,
) -> MedicineValidationResult:
    logger.info(
        "Resolver start: medicine_name=%r query=%r search_text=%r",
        medicine_name,
        (query or "")[:120],
        (search_text or "")[:120],
    )
    if medicine_name:
        resolved = normalize_candidate(medicine_name)
        validation = validate_medicine_name(resolved) if resolved else None
        if validation:
            validation.normalized_name = resolved.title()
            logger.info("Resolver direct hit: normalized_name=%r", validation.normalized_name)
            return validation

    candidate_pool: list[str] = []
    if candidates:
        candidate_pool.extend(candidates)
    if query:
        candidate_pool.extend(extract_candidate_medicines(query))
    if search_text:
        candidate_pool.extend(extract_candidate_medicines(search_text))

    seen: set[str] = set()
    for candidate in candidate_pool:
        normalized = normalize_candidate(candidate)
        if not normalized:
            continue
        lowered = normalized.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        validation = validate_medicine_name(normalized)
        if validation:
            validation.normalized_name = normalized.title()
            logger.info("Resolver candidate hit: normalized_name=%r", validation.normalized_name)
            return validation

    interpreted_search_name = llm_interpret_search_text(search_text or "")
    if interpreted_search_name:
        validation = validate_medicine_name(interpreted_search_name)
        if validation:
            validation.normalized_name = normalize_candidate(interpreted_search_name).title()
            logger.info("Resolver search-text LLM hit: normalized_name=%r", validation.normalized_name)
            return validation

    llm_raw_input_parts = [part for part in [medicine_name, query, search_text] if part]
    llm_raw_input = "\n".join(llm_raw_input_parts).strip()

    if llm_raw_input:
        llm_candidate = llm_normalize_medicine_name(
            raw_input=llm_raw_input,
            candidates=candidate_pool,
        )
        validation = validate_medicine_name(llm_candidate) if llm_candidate else None
        if validation:
            validation.normalized_name = normalize_candidate(llm_candidate).title()
            logger.info("Resolver LLM hit: normalized_name=%r", validation.normalized_name)
            return validation

    logger.info("Resolver unresolved")
    return MedicineValidationResult(
        normalized_name=None,
    )
