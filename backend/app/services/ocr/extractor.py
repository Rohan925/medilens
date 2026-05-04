from dataclasses import dataclass
import logging
import re

from app.services.llm.openai_client import openai_client
from app.services.llm.prompts import build_ocr_extraction_prompt
from app.services.ocr.preprocess import normalize_image_path

logger = logging.getLogger("ocr.extractor")


@dataclass
class OCRExtractionResult:
    medicine_name: str | None
    raw_text: str | None = None
    confidence: float = 0.0
    error: str | None = None


def _parse_extraction_output(output: str) -> OCRExtractionResult:
    medicine_match = re.search(r"MEDICINE:\s*(.*)", output, flags=re.IGNORECASE)
    text_match = re.search(r"TEXT:\s*(.*)", output, flags=re.IGNORECASE)
    confidence_match = re.search(r"CONFIDENCE:\s*(HIGH|MEDIUM|LOW)", output, flags=re.IGNORECASE)

    medicine_name = medicine_match.group(1).strip() if medicine_match else "UNKNOWN"
    raw_text = text_match.group(1).strip() if text_match else None
    confidence_label = confidence_match.group(1).upper() if confidence_match else "LOW"

    confidence_map = {
        "HIGH": 90.0,
        "MEDIUM": 70.0,
        "LOW": 45.0,
    }

    if medicine_name.upper() == "UNKNOWN":
        return OCRExtractionResult(
            medicine_name=None,
            raw_text=None if raw_text in (None, "NONE") else raw_text,
            confidence=confidence_map.get(confidence_label, 0.0),
            error="Could not identify a medicine name from the image.",
        )

    return OCRExtractionResult(
        medicine_name=medicine_name,
        raw_text=None if raw_text in (None, "NONE") else raw_text,
        confidence=confidence_map.get(confidence_label, 0.0),
    )


def extract_medicine_from_image(image_path: str) -> OCRExtractionResult:
    normalized_path = normalize_image_path(image_path)
    prompt = build_ocr_extraction_prompt()
    output = openai_client.invoke_image_text(normalized_path, prompt)

    if not output:
        logger.warning("OCR extraction returned no output")
        return OCRExtractionResult(
            medicine_name=None,
            confidence=0.0,
            error="Image extraction did not return any OCR output.",
        )

    result = _parse_extraction_output(output)
    logger.info(
        "OCR extraction result: medicine=%r confidence=%.1f text=%r",
        result.medicine_name,
        result.confidence,
        result.raw_text,
    )
    return result
