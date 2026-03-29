from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.mysql import get_db
from app.models.user import User
from app.schemas.user import (
    UserRegister, UserResponse, UserProfileUpdate,
    PasswordResetRequest, PasswordReset, PasswordChange,
)
from app.services.user_service import UserService
from app.core.security import (
    create_password_reset_token, verify_password_reset_token,
)
from app.core.exceptions import BadRequestError
from app.api.v1.deps import get_current_user

router = APIRouter(prefix="/users", tags=["User Management"])


# ── Registration ─────────────────────────────────────────────────────────────

@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
def register(data: UserRegister, db: Session = Depends(get_db)):
    """Creates a new user account with email and password."""
    return UserService.register(db, data)


# ── Profile ───────────────────────────────────────────────────────────────────

@router.get("/me", response_model=UserResponse, summary="Get current user profile")
def get_profile(current_user: User = Depends(get_current_user)):
    """Returns the authenticated user's profile details."""
    return current_user


@router.patch("/me", response_model=UserResponse, summary="Update current user profile")
def update_profile(
    data: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Allows the authenticated user to update their profile (name, phone, address)."""
    return UserService.update_profile(db, current_user.id, data)


# ── Password ──────────────────────────────────────────────────────────────────

@router.post("/me/change-password", summary="Change password (authenticated)")
def change_password(
    data: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Changes password for an authenticated user after verifying the current password."""
    UserService.change_password(
        db, current_user.id, data.current_password, data.new_password
    )
    return {"message": "Password changed successfully"}


@router.post("/forgot-password", summary="Request password reset link")
def forgot_password(data: PasswordResetRequest, db: Session = Depends(get_db)):
    """
    Generates a secure password-reset token for the given email.
    In production, this token would be emailed to the user.
    """
    user = UserService.get_by_email(db, data.email)
    # Always return success to avoid user enumeration attacks
    token = None
    if user:
        token = create_password_reset_token(data.email)
    return {
        "message": "If this email is registered, a reset link has been sent.",
        # ⚠ In production, remove the token from the response and send it via email
        "debug_token": token,
    }


@router.post("/reset-password", summary="Reset password using token")
def reset_password(data: PasswordReset, db: Session = Depends(get_db)):
    """Resets the user's password using the token received via email."""
    email = verify_password_reset_token(data.token)
    if not email:
        raise BadRequestError("Invalid or expired password reset token")
    UserService.reset_password(db, email, data.new_password)
    return {"message": "Password reset successfully. You can now log in."}
