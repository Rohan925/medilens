from enum import Enum


class RequestMode(str, Enum):
    SEARCH = "search"
    CHAT = "chat"
    OCR = "ocr"


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class SourceType(str, Enum):
    OPENFDA = "OpenFDA"
    PUBCHEM = "PubChem"
    OCR = "OCR"
    INTERNAL = "Internal"


class ConfidenceLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
