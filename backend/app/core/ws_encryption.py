"""
WebSocket E2E encryption using AES-256-GCM.

Each interview session gets a unique key, exchanged via the REST API
(the session creation endpoint returns the key). Both sides encrypt/
decrypt all messages in the WebSocket channel.

Protocol:
  - Client sends: {"type": "encrypted", "data": "<base64(nonce||ciphertext||tag)>"}
  - Server sends: {"type": "encrypted", "data": "<base64(nonce||ciphertext||tag)>"}
  - The inner plaintext is the original JSON message.
"""

import os
import json
import base64
from typing import Optional, Dict

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class SessionKeyManager:
    """Manages per-session AES-256-GCM keys."""

    def __init__(self):
        self._keys: Dict[int, bytes] = {}  # session_id -> AES key

    def generate_key(self, session_id: int) -> str:
        """Generate a new key for a session. Returns base64-encoded key."""
        key = AESGCM.generate_key(bit_length=256)
        self._keys[session_id] = key
        return base64.b64encode(key).decode("ascii")

    def get_key(self, session_id: int) -> Optional[bytes]:
        """Get the key for a session."""
        return self._keys.get(session_id)

    def remove_key(self, session_id: int):
        """Remove a session key (called when session ends)."""
        self._keys.pop(session_id, None)

    def has_key(self, session_id: int) -> bool:
        return session_id in self._keys


# Global instance
session_keys = SessionKeyManager()


def encrypt_message(session_id: int, message: dict) -> Optional[str]:
    """Encrypt a JSON message for WebSocket transmission. Returns base64-encoded ciphertext."""
    key = session_keys.get_key(session_id)
    if key is None:
        return None
    nonce = os.urandom(12)
    aesgcm = AESGCM(key)
    plaintext = json.dumps(message).encode("utf-8")
    ct = aesgcm.encrypt(nonce, plaintext, None)
    return base64.b64encode(nonce + ct).decode("ascii")


def decrypt_message(session_id: int, ciphertext_b64: str) -> Optional[dict]:
    """Decrypt a base64-encoded ciphertext from WebSocket. Returns parsed JSON dict."""
    key = session_keys.get_key(session_id)
    if key is None:
        return None
    try:
        raw = base64.b64decode(ciphertext_b64)
        nonce = raw[:12]
        ct = raw[12:]
        aesgcm = AESGCM(key)
        plaintext = aesgcm.decrypt(nonce, ct, None)
        return json.loads(plaintext.decode("utf-8"))
    except Exception:
        return None
