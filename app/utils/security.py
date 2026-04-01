from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import hashlib
import secrets
from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.JWT_EXPIRATION_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError:
        return None


def generate_vote_hash(
    eleicao_id: int,
    cooperado_id: int,
    timestamp: datetime,
    salt: Optional[str] = None
) -> str:
    if salt is None:
        salt = secrets.token_hex(16)

    data = f"{eleicao_id}:{cooperado_id}:{timestamp.isoformat()}:{salt}"
    return hashlib.sha256(data.encode()).hexdigest()


def generate_audit_hash(previous_hash: str, data: str) -> str:
    combined = f"{previous_hash}:{data}"
    return hashlib.sha256(combined.encode()).hexdigest()


def generate_token(length: int = 32) -> str:
    return secrets.token_urlsafe(length)
