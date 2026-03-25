# backend/agents/fact_checker_agent.py
from typing import Dict, Any, List
import re
from core.models import RetrievedChunk

UNSAFE_PATTERNS = [
    r"\b\d+\s?(mg|ml|g)\b",       # dosage amounts
    r"\bonce daily\b",
    r"\btwice daily\b",
    r"\bthree times\b",
    r"\bper day\b",
    r"\bfor \d+ days\b"
]


def _contains_unsafe_medical_advice(text: str) -> bool:
    text = text.lower()
    return any(re.search(pattern, text) for pattern in UNSAFE_PATTERNS)


async def fact_checker_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    FACT-CHECKER AGENT

    Verifies that:
    - Generated answer is grounded in retrieved context
    - No unsafe dosage or treatment instructions are present
    """

    draft_answer: str = state.get("draft_answer", "")
    retrieved_chunks: List[RetrievedChunk] = state.get("retrieved_chunks", [])

    if not draft_answer or not retrieved_chunks:
        state["checked_answer"] = (
            "Unable to verify the response due to missing trusted information. "
            "Please consult a healthcare professional."
        )
        state["fact_check_flags"] = ["missing_context"]
        return state

    # Combine all trusted source text
    trusted_text = " ".join(chunk.text.lower() for chunk in retrieved_chunks)

    flags = []

    # 1️⃣ Unsafe medical advice check
    if _contains_unsafe_medical_advice(draft_answer):
        flags.append("unsafe_medical_advice")

    # 2️⃣ Grounding check (basic but effective)
    answer_sentences = re.split(r"[.!?]", draft_answer)

    verified_sentences = []
    for sentence in answer_sentences:
        sentence = sentence.strip()
        if not sentence:
            continue

        # Keep sentence only if at least part appears in trusted content
        # Stricter check: require at least 2 significant words to match
        sig_words = [w for w in sentence.lower().split() if len(w) > 3]
        if not sig_words:
             verified_sentences.append(sentence) # Keep very short sentences (likely connectors)
             continue

        matches = sum(1 for w in sig_words if w in trusted_text)
        if matches >= min(2, len(sig_words)):
            verified_sentences.append(sentence)
        else:
            # Flag this sentence as unverified/hallucinated
            flags.append(f"hallucination_suspect: {sentence[:30]}...")

    if not verified_sentences:
        state["checked_answer"] = (
            "The generated response could not be verified against trusted medical sources. "
            "Please consult a healthcare professional."
        )
        flags.append("unverified_content")
    else:
        checked = ". ".join(verified_sentences)

        if flags:
            checked += (
                "\n\nNote: This information is based on retrieved medical sources "
                "and does not replace professional medical advice."
            )

        state["checked_answer"] = checked

    state["fact_check_flags"] = flags
    return state