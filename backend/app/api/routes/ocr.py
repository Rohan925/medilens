import os
from tempfile import NamedTemporaryFile

from fastapi import APIRouter, File, UploadFile

from app.api.schemas.responses import OcrResponse
from app.domain.enums import RequestMode
from app.graph.runners.ocr_graph import run_ocr_graph
from app.graph.state import GraphState

router = APIRouter()


@router.post("/ocr", response_model=OcrResponse)
async def ocr_image(file: UploadFile = File(...)) -> OcrResponse:
    suffix = os.path.splitext(file.filename or "upload.jpg")[1] or ".jpg"
    temp_path: str | None = None

    try:
        with NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            temp_path = temp_file.name
            temp_file.write(await file.read())

        state = GraphState(
            mode=RequestMode.OCR,
            image_path=temp_path,
        )
        final_state = run_ocr_graph(state)
        return OcrResponse.model_validate(final_state.response)
    finally:
        if temp_path and os.path.exists(temp_path):
            os.unlink(temp_path)
