import json
import os

# ---------------------------
# Load medicines.json once
# ---------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "..", "data", "medicines.json")

with open(DATA_PATH, "r", encoding="utf-8") as f:
    MEDICINES = json.load(f)


# ---------------------------
# Validator function
# ---------------------------
def validate_medicine(text: str):
    """
    Checks if any known medicine exists in cleaned OCR text.
    Returns medicine name if found, else None.
    """
    text = text.lower()

    for med in MEDICINES.keys():
        if med in text:
            return {
                "name": med,
                "meta": MEDICINES[med]
            }

    return None
