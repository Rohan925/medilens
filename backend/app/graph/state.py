from pydantic import BaseModel, Field

from app.domain.enums import RequestMode
from app.domain.models import ChatMessage, Citation, MedicineSummary, RetrievedChunk
from app.domain.types import MetadataMap


class GraphState(BaseModel):
    mode: RequestMode = Field(..., description="Active workflow mode.")

    image_path: str | None = Field(
        default=None,
        description="Temporary filesystem path for OCR image processing.",
    )
    search_text: str | None = Field(
        default=None,
        description="Original free-text search input.",
    )
    raw_query: str | None = Field(
        default=None,
        description="Current user query text.",
    )
    ocr_text: str | None = Field(
        default=None,
        description="Visible medicine-label text extracted from an uploaded image.",
    )
    ocr_confidence: float = Field(
        default=0.0,
        description="OCR confidence as a percentage.",
    )
    error_message: str | None = Field(
        default=None,
        description="OCR or workflow error message when the request cannot be completed.",
    )
    history: list[ChatMessage] = Field(
        default_factory=list,
        description="Ephemeral chat history.",
    )
    medicine_name: str | None = Field(
        default=None,
        description="Medicine context supplied directly by the caller.",
    )
    resolved_medicine: str | None = Field(
        default=None,
        description="Final medicine name chosen by the resolver.",
    )

    openfda_data: MetadataMap = Field(
        default_factory=dict,
        description="OpenFDA payload.",
    )
    pubchem_data: MetadataMap = Field(
        default_factory=dict,
        description="PubChem payload.",
    )
    retrieved_chunks: list[RetrievedChunk] = Field(
        default_factory=list,
        description="Evidence chunks used for prompts and citations.",
    )
    structured_summary: MedicineSummary | None = Field(
        default=None,
        description="Structured medicine summary for downstream formatting.",
    )
    final_answer: str | None = Field(
        default=None,
        description="Final chat answer.",
    )
    chat_route: str | None = Field(
        default=None,
        description="Routing decision for chat flows.",
    )
    citations: list[Citation] = Field(
        default_factory=list,
        description="Structured citations.",
    )

    warnings: list[str] = Field(
        default_factory=list,
        description="Non-fatal warnings gathered during graph execution.",
    )

    response: MetadataMap = Field(
        default_factory=dict,
        description="Final API response payload.",
    )
