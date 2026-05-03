from pydantic import BaseModel, Field


class ChatMessageRequest(BaseModel):
    role: str = Field(..., description="Chat role such as 'user' or 'assistant'.")
    content: str = Field(..., description="Message text content.")


class SearchRequest(BaseModel):
    medicine: str = Field(..., description="Medicine name entered by the user.")


class ChatRequest(BaseModel):
    medicine_name: str | None = Field(
        default=None,
        description="Optional medicine context already known by the frontend.",
    )
    history: list[ChatMessageRequest] = Field(
        default_factory=list,
        description="Ephemeral in-session message history from the frontend.",
    )


# OCR currently uses multipart/form-data with an UploadFile named `file`,
# so there is no JSON request body schema for that endpoint.
