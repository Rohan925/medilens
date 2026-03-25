import re

def clean_ocr_text(raw_text: str):
    text = raw_text.lower()

    # remove dosage like 500mg, 10ml etc
    text = re.sub(r"\d+\s?(mg|ml|g|mcg)", "", text)

    # remove non alphabets
    text = re.sub(r"[^a-z\s]", "", text)

    # remove common words
    remove_words = ["tablet", "tab", "capsule", "cap", "syrup"]
    for word in remove_words:
        text = text.replace(word, "")

    text = text.strip()
    return text
