import torch
import os
import re
from ml_cleaner.model import OCRCleaner
from ml_cleaner.tokenizer import encode, decode, char2idx

model = OCRCleaner(len(char2idx))
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "ocr_cleaner.pt")

model.load_state_dict(torch.load(MODEL_PATH, map_location="cpu"))

model.eval()
# backend/ml_cleaner/infer.py

def clean_text_ml(text: str) -> str:
    # TEMP: do not filter characters
    # just normalize case
    return text.lower()
