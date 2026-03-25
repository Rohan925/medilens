# backend/ocr/ocr_engine.py

import pytesseract
from PIL import Image
import cv2
import numpy as np


def run_ocr(image_path: str) -> str:
    """
    Runs OCR on an image and returns raw extracted text.
    """

    # Load image
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError("Invalid image path")

    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Basic thresholding to improve OCR
    gray = cv2.threshold(
        gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )[1]

    # Convert OpenCV image to PIL
    pil_image = Image.fromarray(gray)

    # Run Tesseract OCR
    text = pytesseract.image_to_string(
    pil_image,
    config="--psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789mgMG."
)

    return text.strip()
