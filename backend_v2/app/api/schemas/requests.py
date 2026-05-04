from pydantic import BaseModel, Field


class ChatMessageRequest(BaseModel):
    role: str = Field(..., description="Chat role such as 'user' or 'assistant'.")
    content: str = Field(..., description="Message text content.")


class SearchRequest(BaseModel):
    query: str = Field(
        ...,
        description="Free-text search query that may contain a medicine name.",
    )


class ChatRequest(BaseModel):
    query: str = Field(..., description="Latest user message for this chat turn.")
    history: list[ChatMessageRequest] = Field(
        default_factory=list,
        description="Prior in-session messages, excluding the latest query.",
    )


# OCR currently uses multipart/form-data with an UploadFile named `file`,
# so there is no JSON request body schema for that endpoint.
