import logging
import re
from dataclasses import dataclass

from app.services.llm.openai_client import openai_client
from app.services.llm.prompts import build_medicine_normalization_prompt

logger = logging.getLogger("resolver")


@dataclass
class MedicineValidationResult:
    normalized_name: str | None


def normalize_candidate(value: str) -> str:
    text = re.sub(r"[^A-Za-z\s\-]", " ", value or "")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def llm_normalize_medicine_name(raw_input: str) -> str | None:
    if not openai_client.available or not raw_input.strip():
        logger.info(
            "Resolver LLM normalization skipped: available=%s raw_input_present=%s",
            openai_client.available,
            bool(raw_input.strip()),
        )
        return None

    logger.info("Resolver LLM normalization start: raw_input=%r", raw_input[:200])
    prompt = build_medicine_normalization_prompt(
        raw_input=raw_input,
        candidates=None,
    )
    output_text = openai_client.invoke_text(prompt)
    if not output_text:
        logger.info("Resolver LLM normalization returned no output")
        return None

    normalized = normalize_candidate(output_text.splitlines()[0].strip().strip("\"'"))
    if not normalized or normalized.upper() == "UNKNOWN":
        logger.info("Resolver LLM normalization returned UNKNOWN")
        return None

    logger.info("Resolver LLM normalization success: normalized=%r", normalized)
    return normalized.title()


def resolve_medicine_name(
    medicine_name: str | None = None,
    input_text: str | None = None,
) -> MedicineValidationResult:
    logger.info(
        "Resolver start: medicine_name=%r input_text=%r",
        medicine_name,
        (input_text or "")[:120],
    )

    llm_raw_input = (medicine_name or input_text or "").strip()
    llm_candidate = llm_normalize_medicine_name(llm_raw_input) if llm_raw_input else None
    if llm_candidate:
        return MedicineValidationResult(normalized_name=llm_candidate)

    fallback_candidate = normalize_candidate(medicine_name or input_text or "")
    if fallback_candidate:
        logger.info(
            "Resolver fallback normalization used: normalized_name=%r",
            fallback_candidate.title(),
        )
        return MedicineValidationResult(normalized_name=fallback_candidate.title())

    logger.info("Resolver unresolved")
    return MedicineValidationResult(normalized_name=None)
