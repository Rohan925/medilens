# services/summarizer.py
from core.llm_client import llm_client

def summarize_text(text: str) -> str:
    if not text:
        return ""
    return llm_client.summarize(text)
