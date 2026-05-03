from pydantic import BaseModel, Field

from .enums import ConfidenceLevel, MessageRole, SourceType
from .types import MetadataMap


class ChatMessage(BaseModel):
    role: MessageRole = Field(..., description="Role of the message author.")
    content: str = Field(..., description="Message text.")


class Citation(BaseModel):
    source: SourceType | str = Field(..., description="Source of the citation.")
    url: str | None = Field(default=None, description="Optional source URL.")
    label: str | None = Field(default=None, description="Optional display label.")


class RetrievedChunk(BaseModel):
    source: SourceType | str = Field(..., description="Origin of retrieved evidence.")
    text: str = Field(..., description="Normalized evidence text.")
    reference: str | None = Field(
        default=None,
        description="Optional reference, typically the medicine name.",
    )
    metadata: MetadataMap = Field(
        default_factory=dict,
        description="Additional structured metadata about the retrieved chunk.",
    )


class MedicineSummary(BaseModel):
    drug_name: str = Field(..., description="Resolved medicine name.")
    category: str = Field(default="Unknown", description="Medicine category.")
    uses: list[str] = Field(default_factory=list, description="Common uses.")
    warnings: list[str] = Field(default_factory=list, description="Key warnings.")
    prescription_status: str = Field(
        default="Unknown",
        description="Prescription status such as OTC or Prescription.",
    )
    mechanism: list[str] = Field(
        default_factory=list,
        description="Optional mechanism of action points.",
    )
    side_effects: list[str] = Field(
        default_factory=list,
        description="Optional side effects.",
    )
    summary_text: str | None = Field(
        default=None,
        description="Optional free-text summary.",
    )


class OCRResult(BaseModel):
    medicine: str = Field(..., description="Detected or resolved medicine name.")
    success: bool = Field(..., description="Whether OCR processing succeeded.")
    confidence: float = Field(
        default=0.0,
        description="Confidence score as a percentage.",
    )
    confidence_level: ConfidenceLevel | None = Field(
        default=None,
        description="Optional qualitative confidence bucket.",
    )
    summary: MedicineSummary | None = Field(
        default=None,
        description="Structured summary associated with the OCR result.",
    )
    citations: list[Citation] = Field(default_factory=list)
    is_strict_fallback: bool = Field(
        default=False,
        description="Whether the OCR result is a low-confidence fallback.",
    )
    error: str | None = Field(
        default=None,
        description="Error message when OCR processing fails.",
    )
