import re
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, UserResponse, UserSignupResponse
from app.auth.utils import (
    get_password_hash, verify_password, create_access_token, create_refresh_token,
    blacklist_token, get_current_user, decode_access_token, SECRET_KEY, ALGORITHM,
    set_access_cookie, set_refresh_cookie, set_csrf_cookie, clear_auth_cookies,
    generate_csrf_token, REFRESH_TOKEN_COOKIE_NAME,
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
def signup(request: Request, user: UserCreate, response: Response, db: Session = Depends(get_db)):
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

    # Set tokens as cookies for security (#6)
    set_access_cookie(response, access_token)
    set_refresh_cookie(response, refresh_token)
    csrf_token = generate_csrf_token()
    set_csrf_cookie(response, csrf_token)

    return {
        "user": new_user,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.post("/login")
@limiter.limit("10/minute")
def login(request: Request, response: Response, user: UserLogin, db: Session = Depends(get_db)):
    if len(user.password) > 1024:
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

    # Set tokens as cookies for security (#6)
    set_access_cookie(response, access_token)
    set_refresh_cookie(response, refresh_token)
    csrf_token = generate_csrf_token()
    set_csrf_cookie(response, csrf_token)

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
async def refresh_token(request: Request, response: Response, refresh_token: str = None, db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid refresh token",
    )

    # #5: Read refresh token from cookie first, then fall back to request body
    token_to_use = refresh_token
    if not token_to_use:
        token_to_use = request.cookies.get(REFRESH_TOKEN_COOKIE_NAME)
    if not token_to_use:
        # Try reading from JSON body
        try:
            body = await request.body()
            if body:
                import json
                data = json.loads(body)
                token_to_use = data.get("refresh_token")
        except Exception:
            pass
    if not token_to_use:
        raise credentials_exception

    try:
        payload = jwt.decode(token_to_use, SECRET_KEY, algorithms=[ALGORITHM])
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

    # Set new cookies (#6)
    set_access_cookie(response, new_access)
    set_refresh_cookie(response, new_refresh)
    csrf_token = generate_csrf_token()
    set_csrf_cookie(response, csrf_token)

    return {
        "access_token": new_access,
        "refresh_token": new_refresh,
        "token_type": "bearer",
    }


@router.post("/logout")
def logout(response: Response, token: str = Depends(get_current_user), db: Session = Depends(get_db)):
    blacklist_token(token, db, reason="logout")
    # Clear auth cookies on logout (#6)
    clear_auth_cookies(response)
    return {"message": "Successfully logged out"}


# Re-export for internal use
def _is_token_blacklisted(jti: str, db: Session) -> bool:
    from app.models.token_blacklist import TokenBlacklist
    return db.query(TokenBlacklist).filter(TokenBlacklist.jti == jti).first() is not None
