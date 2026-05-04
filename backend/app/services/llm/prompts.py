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
    route: str | None = None,
    history_text: str = "",
    summary_text: str = "",
    evidence_text: str = "",
) -> str:
    return f"""You are a medical assistant AI.

Conversation mode:
{route or "generic"}

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
- If medicine context is provided, use it as the primary grounding source.
- If no medicine context is provided, answer as a general medical-information assistant.
- Do not hallucinate medicine facts that are not supported by the provided context.
- If the context is weak, say that clearly.
- Do not provide diagnosis.
- Do not invent dosage instructions.
- If the user refers to a medicine ambiguously and the medicine is unknown, ask a brief clarifying question.
- Keep the answer concise and useful.
- End with a brief medical safety reminder when appropriate.
"""


def build_chat_router_prompt(
    query: str,
    history_text: str = "",
) -> str:
    return f"""You route a medical chat request.

Conversation history:
{history_text or "None"}

Latest user query:
{query}

Task:
- Decide whether the assistant can answer directly from general knowledge and conversation history.
- Decide whether the latest user query needs fresh medicine retrieval from trusted sources.
- Treat general symptom or health questions as direct-answer questions.
- Treat a medicine-specific query as retrieval-needed only when the latest user is asking about a medicine/drug and the conversation history does not already provide enough medicine context.
- If the user is asking a follow-up about the same medicine already discussed in the history, prefer direct answer.

Return exactly this format:
ROUTE: ANSWER or RETRIEVE
MEDICINE: <medicine name or NONE>
"""


def build_search_interpretation_prompt(search_text: str) -> str:
    return f"""You extract medicine names from user search text.

Task:
- Read the input text.
- Identify the most likely medicine or drug name referenced.
- Correct obvious spelling mistakes.
- Normalize brand/generic names when the intended medicine is obvious.
- Return only the medicine name.
- If no medicine can be identified, return UNKNOWN.

Input:
{search_text}

Output rules:
- One line only.
- No explanation.
- If unclear, return UNKNOWN.
"""


def build_summary_enrichment_prompt(
    medicine_name: str,
    category: str,
    uses: list[str],
    warnings: list[str],
    prescription_status: str,
    evidence_text: str,
) -> str:
    return f"""You are enriching a structured medicine summary.

Medicine:
{medicine_name}

Current structured summary:
- Category: {category}
- Uses: {uses}
- Warnings: {warnings}
- Prescription status: {prescription_status}

Grounded evidence:
{evidence_text or "None"}

Task:
- Improve missing or low-quality fields.
- If grounded evidence exists, prefer it.
- If evidence is partial or empty, provide a cautious general fallback.
- Do not invent dosage instructions.
- Keep each use or warning short and standalone.

Return exactly this format:
CATEGORY: <text>
USES: item 1 | item 2 | item 3
WARNINGS: item 1 | item 2 | item 3
PRESCRIPTION_STATUS: <text>
"""


def build_ocr_extraction_prompt() -> str:
    return """You are reading a medicine package image.

Task:
- Identify the most likely medicine or drug name shown on the label.
- Ignore packaging noise such as batch numbers, expiry dates, manufacturer details, dosage strength, and marketing text.
- Also extract a short line of visible label text that helped you identify the medicine.
- If no medicine name can be identified confidently, return UNKNOWN.

Return exactly this format:
MEDICINE: <medicine name or UNKNOWN>
TEXT: <short visible label text or NONE>
CONFIDENCE: <HIGH or MEDIUM or LOW>
"""
