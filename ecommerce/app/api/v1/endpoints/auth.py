from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from jose import JWTError

from app.db.mysql import get_db
from app.schemas.user import TokenResponse, RefreshTokenRequest, UserResponse, SocialRegister
from app.services.user_service import UserService
from app.core.security import create_access_token, create_refresh_token, decode_token
from app.core.exceptions import UnauthorizedError

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse, summary="Login with email & password")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """
    Authenticates a user and returns JWT access + refresh tokens.
    Use the **access_token** in `Authorization: Bearer <token>` header for all protected routes.
    """
    user = UserService.authenticate(db, email=form_data.username, password=form_data.password)
    access_token = create_access_token(subject=user.id)
    refresh_token = create_refresh_token(subject=user.id)
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/social-login", response_model=TokenResponse, summary="Login/Register via Social")
def social_login(data: SocialRegister, db: Session = Depends(get_db)):
    """Register or login a user via Google / Facebook OAuth."""
    user = UserService.social_register_or_login(db, data)
    return TokenResponse(
        access_token=create_access_token(subject=user.id),
        refresh_token=create_refresh_token(subject=user.id),
    )


@router.post("/refresh", response_model=TokenResponse, summary="Refresh access token")
def refresh_token(body: RefreshTokenRequest):
    """Exchange a valid refresh token for a new access token."""
    try:
        payload = decode_token(body.refresh_token)
        if payload.get("type") != "refresh":
            raise UnauthorizedError("Invalid token type")
        user_id = payload.get("sub")
    except JWTError:
        raise UnauthorizedError("Invalid or expired refresh token")

    return TokenResponse(
        access_token=create_access_token(subject=user_id),
        refresh_token=create_refresh_token(subject=user_id),
    )
