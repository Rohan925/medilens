import logging

from app.graph.state import GraphState
from app.services.ocr.extractor import extract_medicine_from_image

logger = logging.getLogger("node.ocr")


def ocr_agent(state: GraphState) -> GraphState:
    logger.info("Node hit: ocr_agent")

    if not state.image_path:
        state.error_message = "No image file was provided for OCR."
        state.warnings.append(state.error_message)
        return state

    extraction = extract_medicine_from_image(state.image_path)
    state.ocr_confidence = extraction.confidence
    state.ocr_text = extraction.raw_text

    if extraction.medicine_name:
        state.medicine_name = extraction.medicine_name
        return state

    state.error_message = extraction.error or "Could not identify a medicine name from the image."
    state.warnings.append(state.error_message)
    return state
