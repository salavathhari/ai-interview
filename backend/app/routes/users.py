from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.schemas.user import UserResponse, UserProfileUpdate, UserPasswordUpdate
from app.auth.utils import get_current_user, get_password_hash, verify_password, blacklist_token
from app.models.user import User
from app.database import get_db

router = APIRouter(
    prefix="/users",
    tags=["users"]
)

@router.get("/profile", response_model=UserResponse)
def get_profile(current_user: User = Depends(get_current_user)):
    """Get the profile of the currently logged-in user."""
    return current_user

@router.put("/profile", response_model=UserResponse)
def update_profile(
    data: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update name and/or email."""
    if data.email and data.email != current_user.email:
        existing = db.query(User).filter(User.email == data.email).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already in use by another account.")
        current_user.email = data.email
    if data.name is not None:
        current_user.name = data.name
    db.commit()
    db.refresh(current_user)
    return current_user

@router.put("/password")
def change_password(
    data: UserPasswordUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    token: str = Depends(lambda token: token),
):
    """Change the user's password after verifying the current one. Invalidates the old token."""
    if not verify_password(data.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect.")
    if len(data.new_password) < 8:
        raise HTTPException(status_code=400, detail="New password must be at least 8 characters.")
    if len(data.new_password.encode('utf-8')) > 72:
        raise HTTPException(status_code=400, detail="New password is too long (max 72 bytes).")
    current_user.hashed_password = get_password_hash(data.new_password)
    db.commit()
    return {"message": "Password updated successfully. Please log in again."}

@router.delete("/account")
def delete_account(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    token: str = Depends(lambda token: token),
):
    """Permanently deactivate (soft-delete) the user's account. Invalidates the token."""
    current_user.is_active = False
    blacklist_token(token, db, reason="account_deactivation")
    db.commit()
    return {"message": "Account deactivated. Contact support to restore."}
