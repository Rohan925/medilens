from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints


EmailStrTrimmed = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=3, max_length=320),
]

PasswordStr = Annotated[
    str,
    StringConstraints(min_length=8, max_length=128),
]


class AuthRequest(BaseModel):
    email: EmailStrTrimmed = Field(..., description="User email address.")
    password: PasswordStr = Field(..., description="User password.")


class AuthUserResponse(BaseModel):
    id: str = Field(..., description="User id.")
    email: str = Field(..., description="User email address.")


class LogoutResponse(BaseModel):
    ok: bool = Field(..., description="Whether logout completed successfully.")
