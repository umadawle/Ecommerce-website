from sqlalchemy.orm import Session
from typing import Optional
from app.models.user import User
from app.schemas.user import UserRegister, SocialRegister, UserProfileUpdate
from app.core.security import hash_password, verify_password
from app.core.exceptions import ConflictError, NotFoundError, UnauthorizedError, BadRequestError


class UserService:

    @staticmethod
    def get_by_id(db: Session, user_id: int) -> User:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise NotFoundError("User not found")
        return user

    @staticmethod
    def get_by_email(db: Session, email: str) -> Optional[User]:
        return db.query(User).filter(User.email == email).first()

    # ── Registration ────────────────────────────────────────────────────────

    @staticmethod
    def register(db: Session, data: UserRegister) -> User:
        existing = db.query(User).filter(User.email == data.email).first()
        if existing:
            raise ConflictError("Email already registered")
        user = User(
            email=data.email,
            hashed_password=hash_password(data.password),
            full_name=data.full_name,
            phone=data.phone,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def social_register_or_login(db: Session, data: SocialRegister) -> User:
        # Try by social_id first
        user = (
            db.query(User)
            .filter(
                User.social_provider == data.social_provider,
                User.social_id == data.social_id,
            )
            .first()
        )
        if user:
            return user
        # Try by email (link accounts)
        user = db.query(User).filter(User.email == data.email).first()
        if user:
            user.social_provider = data.social_provider
            user.social_id = data.social_id
            db.commit()
            db.refresh(user)
            return user
        # New user
        user = User(
            email=data.email,
            hashed_password=hash_password("social_auth_no_password"),
            full_name=data.full_name,
            social_provider=data.social_provider,
            social_id=data.social_id,
            is_verified=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    # ── Login ───────────────────────────────────────────────────────────────

    @staticmethod
    def authenticate(db: Session, email: str, password: str) -> User:
        user = db.query(User).filter(User.email == email).first()
        if not user or not verify_password(password, user.hashed_password):
            raise UnauthorizedError("Invalid email or password")
        if not user.is_active:
            raise UnauthorizedError("Account is deactivated")
        return user

    # ── Profile ─────────────────────────────────────────────────────────────

    @staticmethod
    def update_profile(db: Session, user_id: int, data: UserProfileUpdate) -> User:
        user = UserService.get_by_id(db, user_id)
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)
        db.commit()
        db.refresh(user)
        return user

    # ── Password ─────────────────────────────────────────────────────────────

    @staticmethod
    def change_password(
        db: Session, user_id: int, current_password: str, new_password: str
    ) -> User:
        user = UserService.get_by_id(db, user_id)
        if not verify_password(current_password, user.hashed_password):
            raise UnauthorizedError("Current password is incorrect")
        user.hashed_password = hash_password(new_password)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def reset_password(db: Session, email: str, new_password: str) -> User:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise NotFoundError("No account found with this email")
        user.hashed_password = hash_password(new_password)
        db.commit()
        db.refresh(user)
        return user
