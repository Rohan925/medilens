def build_medicine_normalization_prompt(
    raw_input: str,
    candidates: list[str] | None = None,
) -> str:
    candidate_text = ", ".join(candidates or [])

    return f"""You normalize medicine names.

Task:
- Convert the input into the most likely standard medicine name.
- Fix common spelling mistakes.
- Map brand names to the most likely generic/common medicine name when obvious.
- Return only the medicine name.
- If you are not reasonably confident the input refers to a medicine, return UNKNOWN.

Input:
{raw_input}

Candidate hints:
{candidate_text or "None"}

Output rules:
- Return one line only.
- No explanation.
- No punctuation around the answer.
- If uncertain, return UNKNOWN.
"""


def build_chat_answer_prompt(
    user_query: str,
    medicine_name: str | None = None,
    history_text: str = "",
    summary_text: str = "",
    evidence_text: str = "",
) -> str:
    return f"""You are a medical assistant AI.

Medicine context:
{medicine_name or "Unknown"}

Conversation history:
{history_text or "None"}

Structured summary:
{summary_text or "None"}

Retrieved evidence:
{evidence_text or "None"}

Latest user question:
{user_query}

Instructions:
- Answer the latest user question directly and clearly.
- Use the provided medical context as the primary grounding source.
- Do not hallucinate medicine facts that are not supported by the provided context.
- If the context is weak, say that clearly.
- Do not provide diagnosis.
- Do not invent dosage instructions.
- Keep the answer concise and useful.
- End with a brief medical safety reminder when appropriate.
"""
