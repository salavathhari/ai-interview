import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext

# Secret key to sign JWT — read from environment, auto-generate if missing
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not SECRET_KEY:
    SECRET_KEY = secrets.token_urlsafe(64)
    print("[AUTH WARNING] No JWT_SECRET_KEY set in environment. Generated ephemeral key. Tokens will not survive restarts.")

ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
_VALID_JWT_ALGORITHMS = {"HS256", "HS384", "HS512"}
if ALGORITHM not in _VALID_JWT_ALGORITHMS:
    print(f"[AUTH WARNING] Invalid JWT_ALGORITHM '{ALGORITHM}' — falling back to HS256")
    ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = min(int(os.getenv("JWT_EXPIRE_MINUTES", "480")), 1440)  # Cap at 24 hours
REFRESH_TOKEN_EXPIRE_DAYS = min(int(os.getenv("JWT_REFRESH_EXPIRE_DAYS", "7")), 90)  # Cap at 90 days

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# Use bcrypt_sha256 to avoid bcrypt's 72-byte input limitation and compatibility
# issues in some environments. This wraps the password with SHA-256 before
# passing to bcrypt, allowing longer passwords safely.
# Use Argon2 for hashing to avoid bcrypt limitations and compatibility issues
# Argon2 is widely recommended and has no 72-byte input limit.
pwd_context = CryptContext(schemes=["argon2", "bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    import uuid
    to_encode.update({"exp": expire, "iat": now, "jti": str(uuid.uuid4()), "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict):
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    expire = now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    import uuid
    to_encode.update({"exp": expire, "iat": now, "jti": str(uuid.uuid4()), "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

_blacklist_cleanup_counter = 0

def _is_token_blacklisted(jti: str, db: Session) -> bool:
    from app.models.token_blacklist import TokenBlacklist
    result = db.query(TokenBlacklist).filter(TokenBlacklist.jti == jti).first() is not None
    # Periodically clean up expired blacklist entries to prevent unbounded growth
    global _blacklist_cleanup_counter
    _blacklist_cleanup_counter += 1
    if _blacklist_cleanup_counter >= 100:
        _blacklist_cleanup_counter = 0
        try:
            from datetime import datetime, timezone
            now = datetime.now(timezone.utc)
            db.query(TokenBlacklist).filter(TokenBlacklist.expires_at < now).delete()
            db.commit()
        except Exception:
            db.rollback()
    return result


def blacklist_token(token: str, db: Session, reason: str = "logout"):
    from app.models.token_blacklist import TokenBlacklist
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM], options={"verify_exp": False})
        jti = payload.get("jti")
        user_id = payload.get("user_id")
        exp = payload.get("exp")
        if jti and user_id:
            from datetime import datetime, timezone
            expires_at = datetime.fromtimestamp(exp, tz=timezone.utc) if exp else datetime.now(timezone.utc)
            db_token = TokenBlacklist(
                jti=jti,
                token_type=payload.get("type", "access"),
                user_id=user_id,
                expires_at=expires_at,
                reason=reason,
            )
            db.add(db_token)
            db.commit()
            return True
    except JWTError:
        pass
    return False


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        jti: str = payload.get("jti")
        if email is None:
            raise credentials_exception
        if jti and _is_token_blacklisted(jti, db):
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )
    return user

def decode_access_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


# ---------------------------------------------------------------------------
# Cookie helpers for secure token storage
# ---------------------------------------------------------------------------

ACCESS_TOKEN_COOKIE_NAME = "access_token"
REFRESH_TOKEN_COOKIE_NAME = "refresh_token"
CSRF_COOKIE_NAME = "csrf_token"

# Access token: short-lived, readable by JS (sent via Authorization header)
ACCESS_TOKEN_MAX_AGE = ACCESS_TOKEN_EXPIRE_MINUTES * 60  # seconds

# Refresh token: long-lived, httpOnly (not readable by JS)
REFRESH_TOKEN_MAX_AGE = REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60  # seconds


def _is_production() -> bool:
    import os
    return os.getenv("ENVIRONMENT", "development").lower() == "production"


def set_access_cookie(response, token: str):
    """Set the access token as a cookie (not httpOnly — frontend reads it for WS)."""
    response.set_cookie(
        key=ACCESS_TOKEN_COOKIE_NAME,
        value=token,
        max_age=ACCESS_TOKEN_MAX_AGE,
        httponly=False,
        secure=_is_production(),
        samesite="lax",
        path="/",
    )


def set_refresh_cookie(response, token: str):
    """Set the refresh token as an httpOnly cookie (JS cannot read it)."""
    response.set_cookie(
        key=REFRESH_TOKEN_COOKIE_NAME,
        value=token,
        max_age=REFRESH_TOKEN_MAX_AGE,
        httponly=True,
        secure=_is_production(),
        samesite="lax",
        path="/",
    )


def set_csrf_cookie(response, csrf_token: str):
    """Set a CSRF token as a non-httpOnly cookie (frontend reads it for double-submit)."""
    response.set_cookie(
        key=CSRF_COOKIE_NAME,
        value=csrf_token,
        max_age=ACCESS_TOKEN_MAX_AGE,
        httponly=False,
        secure=_is_production(),
        samesite="strict",
        path="/",
    )


def clear_auth_cookies(response):
    """Clear all auth-related cookies (used on logout)."""
    for name in (ACCESS_TOKEN_COOKIE_NAME, REFRESH_TOKEN_COOKIE_NAME, CSRF_COOKIE_NAME):
        response.delete_cookie(key=name, path="/")


def generate_csrf_token() -> str:
    """Generate a random CSRF token."""
    return secrets.token_urlsafe(32)
