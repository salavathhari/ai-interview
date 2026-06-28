"""
Field-level encryption using AES-256-GCM (authenticated encryption).

Usage in models:
    from app.core.encryption import EncryptedString
    class MyModel(Base):
        secret_field = Column(EncryptedString(1024))
"""

import os
import base64
import secrets
from typing import Optional

from sqlalchemy import String, TypeDecorator
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

# Master encryption key — derived from environment variable
_MASTER_KEY: Optional[bytes] = None
_SALT = b"ai-interview-platform-field-encryption-v1"


def _get_master_key() -> bytes:
    """Derive a 256-bit key from the FIELD_ENCRYPTION_KEY env var."""
    global _MASTER_KEY
    if _MASTER_KEY is not None:
        return _MASTER_KEY

    raw_key = os.getenv("FIELD_ENCRYPTION_KEY")
    if not raw_key:
        # Auto-generate for development — NOT for production
        raw_key = secrets.token_urlsafe(32)
        print("[ENCRYPTION WARNING] No FIELD_ENCRYPTION_KEY set. Generated ephemeral key. "
              "Data will NOT be decryptable after restart. Set FIELD_ENCRYPTION_KEY in .env for production.")

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=_SALT,
        iterations=480_000,
    )
    _MASTER_KEY = kdf.derive(raw_key.encode() if isinstance(raw_key, str) else raw_key)
    return _MASTER_KEY


class FieldEncryptor:
    """AES-256-GCM authenticated encryption for field values."""

    @staticmethod
    def encrypt(plaintext: str) -> str:
        """Encrypt a string. Returns base64-encoded nonce + ciphertext."""
        if not plaintext:
            return plaintext
        key = _get_master_key()
        nonce = os.urandom(12)  # 96-bit nonce for GCM
        aesgcm = AESGCM(key)
        ct = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
        # Store as base64(nonce || ciphertext)
        return base64.b64encode(nonce + ct).decode("ascii")

    @staticmethod
    def decrypt(ciphertext_b64: str) -> str:
        """Decrypt a base64-encoded nonce + ciphertext string."""
        if not ciphertext_b64:
            return ciphertext_b64
        key = _get_master_key()
        try:
            raw = base64.b64decode(ciphertext_b64)
            nonce = raw[:12]
            ct = raw[12:]
            aesgcm = AESGCM(key)
            return aesgcm.decrypt(nonce, ct, None).decode("utf-8")
        except Exception:
            # If decryption fails, the data is corrupted or was encrypted
            # with a different key. Return empty string rather than crashing.
            return ""

    @staticmethod
    def is_encrypted(value: str) -> bool:
        """Check if a value appears to be encrypted (base64 with GCM nonce prefix)."""
        if not value:
            return False
        try:
            raw = base64.b64decode(value)
            # GCM ciphertext: 12-byte nonce + at least 16-byte tag + ciphertext
            return len(raw) >= 28
        except Exception:
            return False


class EncryptedString(TypeDecorator):
    """SQLAlchemy TypeDecorator that transparently encrypts/decrypts string fields."""

    impl = String
    cache_ok = True

    def __init__(self, length=None, *args, **kwargs):
        super().__init__(length=length, *args, **kwargs)

    def process_bind_param(self, value, dialect):
        """Encrypt before storing in database."""
        if value is None:
            return None
        return FieldEncryptor.encrypt(value)

    def process_result_value(self, value, dialect):
        """Decrypt after reading from database."""
        if value is None:
            return None
        # Handle both encrypted and unencrypted data (migration path)
        if FieldEncryptor.is_encrypted(value):
            return FieldEncryptor.decrypt(value)
        # Legacy unencrypted data — return as-is
        return value


class EncryptedText(TypeDecorator):
    """SQLAlchemy TypeDecorator for Text columns with encryption."""

    impl = String
    cache_ok = True

    def process_bind_param(self, value, dialect):
        """Encrypt before storing in database."""
        if value is None:
            return None
        return FieldEncryptor.encrypt(value)

    def process_result_value(self, value, dialect):
        """Decrypt after reading from database."""
        if value is None:
            return None
        if FieldEncryptor.is_encrypted(value):
            return FieldEncryptor.decrypt(value)
        return value
