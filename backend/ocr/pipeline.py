# backend/ocr/pipeline.py
from ocr.cleaner import rule_clean
from ml_cleaner.infer import clean_text_ml
from ocr.validator import validate_medicine

def process_ocr_text(raw_text: str):
    text = rule_clean(raw_text)
    text = clean_text_ml(text)
    text = rule_clean(text)

    medicine = validate_medicine(text)

    if not medicine:
        return {
            "success": False,
            "cleaned_text": text,
            "confidence": 0.0,
            "error": "Low OCR confidence"
        }

    return {
        "success": True,
        "cleaned_text": text,
        "medicine": medicine,
        "confidence": 1.0
    }
