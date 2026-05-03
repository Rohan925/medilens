from pydantic import BaseModel, Field

from app.domain.enums import ConfidenceLevel, RequestMode
from app.domain.models import ChatMessage, Citation, MedicineSummary, RetrievedChunk
from app.domain.types import MetadataMap


class GraphState(BaseModel):
    mode: RequestMode = Field(..., description="Active workflow mode for the request.")

    raw_query: str | None = Field(
        default=None,
        description="Current user query text for search or chat flows.",
    )
    image_path: str | None = Field(
        default=None,
        description="Temporary image path for OCR workflows.",
    )
    history: list[ChatMessage] = Field(
        default_factory=list,
        description="Ephemeral chat history supplied by the frontend.",
    )
    medicine_name: str | None = Field(
        default=None,
        description="Medicine context coming directly from the request, if any.",
    )

    ocr_text: str | None = Field(
        default=None,
        description="Raw or cleaned OCR text extracted from an image.",
    )
    candidate_medicines: list[str] = Field(
        default_factory=list,
        description="Possible medicine names derived from OCR or query parsing.",
    )
    resolved_medicine: str | None = Field(
        default=None,
        description="Final resolved medicine name chosen by the resolver agent.",
    )
    confidence_score: float = Field(
        default=0.0,
        description="Numerical confidence score for medicine resolution or OCR output.",
    )
    confidence_level: ConfidenceLevel | None = Field(
        default=None,
        description="Qualitative confidence bucket derived from the score.",
    )

    openfda_data: MetadataMap = Field(
        default_factory=dict,
        description="Raw or lightly normalized OpenFDA payload.",
    )
    pubchem_data: MetadataMap = Field(
        default_factory=dict,
        description="Raw or lightly normalized PubChem payload.",
    )
    retrieved_chunks: list[RetrievedChunk] = Field(
        default_factory=list,
        description="Canonical evidence chunks shared across downstream agents.",
    )
    structured_summary: MedicineSummary | None = Field(
        default=None,
        description="Canonical internal medicine summary object.",
    )

    draft_answer: str | None = Field(
        default=None,
        description="Intermediate answer produced by generation-oriented agents.",
    )
    final_answer: str | None = Field(
        default=None,
        description="Final answer after safety checks and post-processing.",
    )
    citations: list[Citation] = Field(
        default_factory=list,
        description="Structured citations attached to the final answer or summary.",
    )

    warnings: list[str] = Field(
        default_factory=list,
        description="Non-fatal warnings gathered during graph execution.",
    )
    errors: list[str] = Field(
        default_factory=list,
        description="Errors collected during graph execution.",
    )
    is_strict_fallback: bool = Field(
        default=False,
        description="Whether the workflow ended in a conservative fallback state.",
    )
    metadata: MetadataMap = Field(
        default_factory=dict,
        description="Extra state used for orchestration, tracing, or temporary agent data.",
    )

    response: MetadataMap = Field(
        default_factory=dict,
        description="Final API response payload produced by the formatter agent.",
    )
