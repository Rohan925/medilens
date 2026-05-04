from pydantic import BaseModel, Field


class CitationResponse(BaseModel):
    source: str = Field(..., description="Human-readable source name.")
    url: str | None = Field(default=None, description="Optional source URL.")
    label: str | None = Field(
        default=None,
        description="Optional source label shown in richer UIs.",
    )


class MedicineSummaryResponse(BaseModel):
    category: str = Field(..., description="High-level medicine category.")
    uses: list[str] = Field(default_factory=list, description="Common uses.")
    warnings: list[str] = Field(default_factory=list, description="Key warnings.")
    prescription_status: str | None = Field(
        default=None,
        description="Prescription status such as OTC or Prescription.",
    )
    mechanism: list[str] = Field(
        default_factory=list,
        description="Optional mechanism details for richer summary views.",
    )
    side_effects: list[str] = Field(
        default_factory=list,
        description="Optional side effects list for OCR result variants.",
    )
    text: str | None = Field(
        default=None,
        description="Optional fallback free-text summary.",
    )


class SearchResponse(BaseModel):
    name: str | None = Field(default=None, description="Resolved medicine name.")
    category: str = Field(..., description="High-level medicine category.")
    uses: list[str] = Field(default_factory=list, description="Common uses.")
    warnings: list[str] = Field(default_factory=list, description="Key warnings.")
    prescription_status: str | None = Field(default=None)
    mechanism: list[str] = Field(default_factory=list)
    citations: list[CitationResponse] = Field(default_factory=list)


class OcrResponse(BaseModel):
    medicine: str = Field(..., description="Detected or resolved medicine name.")
    success: bool = Field(..., description="Whether OCR resolution was successful.")
    confidence: float = Field(..., description="Confidence score as a percentage.")
    summary: MedicineSummaryResponse | None = Field(
        default=None,
        description="Structured medicine summary for the OCR result page.",
    )
    citations: list[CitationResponse] = Field(default_factory=list)
    is_strict_fallback: bool = Field(
        default=False,
        description="Whether the OCR path fell back to a low-confidence response.",
    )
    error: str | None = Field(
        default=None,
        description="Error message when OCR processing fails or cannot resolve a medicine.",
    )


class ChatResponse(BaseModel):
    response: str = Field(..., description="Assistant response text for the chat UI.")


class ErrorResponse(BaseModel):
    detail: str = Field(..., description="Error detail message.")
