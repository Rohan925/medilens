from pathlib import Path


def normalize_image_path(image_path: str) -> str:
    """
    Normalize the temporary OCR image path before it is sent to the model.
    This keeps the OCR pipeline extensible if light preprocessing is needed later.
    """
    return str(Path(image_path).resolve())
