import os

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.api.schemas.auth import AuthRequest, AuthUserResponse, LogoutResponse
from app.services.auth import (
    AUTH_COOKIE_NAME,
    AUTH_MAX_AGE_SECONDS,
    UserRecord,
    authenticate_user,
    create_auth_token,
    create_user,
    require_authenticated_user,
)


router = APIRouter()


def _set_auth_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=AUTH_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=os.getenv("COOKIE_SECURE", "false").lower() == "true",
        samesite="lax",
        path="/",
        max_age=AUTH_MAX_AGE_SECONDS,
    )


@router.post("/register", response_model=AuthUserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(request: AuthRequest) -> AuthUserResponse:
    user = create_user(request.email, request.password)
    return AuthUserResponse(id=user.id, email=user.email)


@router.post("/login", response_model=AuthUserResponse)
async def login_user(request: AuthRequest, response: Response) -> AuthUserResponse:
    user = authenticate_user(request.email, request.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    token = create_auth_token(user.id)
    _set_auth_cookie(response, token)
    return AuthUserResponse(id=user.id, email=user.email)


@router.get("/me", response_model=AuthUserResponse)
async def get_me(current_user: UserRecord = Depends(require_authenticated_user)) -> AuthUserResponse:
    return AuthUserResponse(id=current_user.id, email=current_user.email)


@router.post("/logout", response_model=LogoutResponse)
async def logout_user(response: Response) -> LogoutResponse:
    response.delete_cookie(
        key=AUTH_COOKIE_NAME,
        path="/",
        httponly=True,
        samesite="lax",
    )
    return LogoutResponse(ok=True)
