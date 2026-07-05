import base64
import hashlib
import json
from datetime import UTC, datetime, timedelta
from typing import Any

from cryptography.fernet import Fernet
from jose import JWTError, jwt
from passlib.context import CryptContext

from nexus_api.config import get_settings


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
settings = get_settings()
ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, hashed_password: str | None) -> bool:
    if not hashed_password:
        return False
    return pwd_context.verify(password, hashed_password)


def create_access_token(subject: str, extra: dict[str, Any] | None = None) -> str:
    expire = datetime.now(UTC) + timedelta(minutes=settings.access_token_minutes)
    payload: dict[str, Any] = {"sub": subject, "exp": expire, "type": "access"}
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
    except JWTError as exc:
        raise ValueError("Invalid token") from exc
    if payload.get("type") != "access":
        raise ValueError("Invalid token type")
    return payload


def _fernet_key() -> bytes:
    if settings.encryption_key:
        return settings.encryption_key.encode()
    digest = hashlib.sha256(settings.secret_key.encode()).digest()
    return base64.urlsafe_b64encode(digest)


class Encryptor:
    def __init__(self) -> None:
        self._fernet = Fernet(_fernet_key())

    def encrypt_json(self, value: dict[str, Any]) -> str:
        serialized = json.dumps(value, separators=(",", ":"), sort_keys=True).encode()
        return self._fernet.encrypt(serialized).decode()

    def decrypt_json(self, value: str) -> dict[str, Any]:
        decrypted = self._fernet.decrypt(value.encode()).decode()
        return json.loads(decrypted)

