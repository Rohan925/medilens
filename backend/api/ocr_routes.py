from fastapi import APIRouter, UploadFile, File
from services.ocr_service import process_image
import shutil
import os
import uuid

router = APIRouter()

@router.post("/ocr")
async def ocr_endpoint(file: UploadFile = File(...)):
    print(f"DEBUG: /ocr endpoint received request for file: {file.filename}")
    filename = f"{uuid.uuid4()}_{file.filename}"
    temp_path = os.path.join("tmp", filename)

    os.makedirs("tmp", exist_ok=True)

    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # 🔥 IMPORTANT: await async function
    result = await process_image(temp_path)

    os.remove(temp_path)

    return result
