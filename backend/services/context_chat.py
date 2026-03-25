# services/context_chat.py
from services.search_history import get_last_summary

def build_chat_context(user_message: str):
    summary = get_last_summary()

    if not summary:
        return None, "No medicine summary available yet."

    return summary, user_message
