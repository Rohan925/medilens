# services/search_history.py

_search_history = []

def save_search(medicine: str, summary: str):
    _search_history.append({
        "medicine": medicine,
        "summary": summary
    })

def get_last_summary():
    if not _search_history:
        return None
    return _search_history[-1]["summary"]
