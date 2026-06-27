import re
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, UserResponse, UserSignupResponse
from app.auth.utils import (
    get_password_hash, verify_password, create_access_token, create_refresh_token,
    blacklist_token, get_current_user, decode_access_token, SECRET_KEY, ALGORITHM,
)
from jose import JWTError, jwt
from app.core.rate_limit import limiter

router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)

PASSWORD_MIN_LENGTH = 8


def _validate_password(password: str):
    if len(password) < PASSWORD_MIN_LENGTH:
        raise HTTPException(status_code=400, detail=f"Password must be at least {PASSWORD_MIN_LENGTH} characters")
    if not re.search(r"[A-Z]", password):
        raise HTTPException(status_code=400, detail="Password must contain at least one uppercase letter")
    if not re.search(r"[a-z]", password):
        raise HTTPException(status_code=400, detail="Password must contain at least one lowercase letter")
    if not re.search(r"[0-9]", password):
        raise HTTPException(status_code=400, detail="Password must contain at least one digit")


@router.post("/signup", response_model=UserSignupResponse)
@limiter.limit("5/minute")
def signup(request: Request, user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    _validate_password(user.password)

    hashed_password = get_password_hash(user.password)
    new_user = User(
        email=user.email,
        name=user.name,
        hashed_password=hashed_password,
        is_recruiter=(user.role == "recruiter")
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    access_token = create_access_token(data={"sub": new_user.email, "user_id": new_user.id})
    refresh_token = create_refresh_token(data={"sub": new_user.email, "user_id": new_user.id})
    return {
        "user": new_user,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.post("/login")
@limiter.limit("10/minute")
def login(request: Request, user: UserLogin, db: Session = Depends(get_db)):
    if len(user.password.encode('utf-8')) > 72:
        raise HTTPException(status_code=400, detail="Password too long")

    db_user = db.query(User).filter(User.email == user.email).first()
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    if not db_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )

    access_token = create_access_token(data={"sub": db_user.email, "user_id": db_user.id})
    refresh_token = create_refresh_token(data={"sub": db_user.email, "user_id": db_user.id})
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "email": db_user.email,
            "name": db_user.name,
            "is_admin": db_user.is_admin,
            "is_recruiter": db_user.is_recruiter
        }
    }


@router.post("/refresh")
@limiter.limit("20/minute")
def refresh_token(request: Request, refresh_token: str, db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid refresh token",
    )
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        token_type = payload.get("type")
        jti = payload.get("jti")
        if email is None or token_type != "refresh":
            raise credentials_exception
        if jti and _is_token_blacklisted(jti, db):
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.email == email).first()
    if user is None or not user.is_active:
        raise credentials_exception

    new_access = create_access_token(data={"sub": user.email, "user_id": user.id})
    new_refresh = create_refresh_token(data={"sub": user.email, "user_id": user.id})
    return {
        "access_token": new_access,
        "refresh_token": new_refresh,
        "token_type": "bearer",
    }


@router.post("/logout")
def logout(token: str = Depends(get_current_user), db: Session = Depends(get_db)):
    blacklist_token(token, db, reason="logout")
    return {"message": "Successfully logged out"}


# Re-export for internal use
def _is_token_blacklisted(jti: str, db: Session) -> bool:
    from app.models.token_blacklist import TokenBlacklist
    return db.query(TokenBlacklist).filter(TokenBlacklist.jti == jti).first() is not None
