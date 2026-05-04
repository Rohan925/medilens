import os
from tempfile import NamedTemporaryFile

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from starlette.concurrency import run_in_threadpool

from app.api.schemas.responses import OcrResponse
from app.domain.enums import RequestMode
from app.graph.runners.ocr_graph import run_ocr_graph
from app.graph.state import GraphState
from app.services.auth import require_authenticated_user

router = APIRouter()

ALLOWED_IMAGE_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
}
ALLOWED_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
}
MAX_UPLOAD_BYTES = 5 * 1024 * 1024
CHUNK_SIZE = 1024 * 1024


@router.post("/ocr", response_model=OcrResponse, dependencies=[Depends(require_authenticated_user)])
async def ocr_image(file: UploadFile = File(...)) -> OcrResponse:
    suffix = os.path.splitext(file.filename or "upload.jpg")[1].lower() or ".jpg"
    temp_path: str | None = None

    try:
        if file.content_type not in ALLOWED_IMAGE_TYPES:
            raise HTTPException(
                status_code=400,
                detail="Unsupported file type. Upload a JPEG, PNG, or WebP image.",
            )

        if suffix not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail="Unsupported file extension. Use .jpg, .jpeg, .png, or .webp.",
            )

        with NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            temp_path = temp_file.name
            total_bytes = 0
            while True:
                chunk = await file.read(CHUNK_SIZE)
                if not chunk:
                    break

                total_bytes += len(chunk)
                if total_bytes > MAX_UPLOAD_BYTES:
                    raise HTTPException(
                        status_code=413,
                        detail="Image upload is too large. Maximum size is 5 MB.",
                    )

                temp_file.write(chunk)

        state = GraphState(
            mode=RequestMode.OCR,
            image_path=temp_path,
        )
        final_state = await run_in_threadpool(run_ocr_graph, state)
        return OcrResponse.model_validate(final_state.response)
    finally:
        await file.close()
        if temp_path and os.path.exists(temp_path):
            os.unlink(temp_path)
