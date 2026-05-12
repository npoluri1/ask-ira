import hashlib
import os
import secrets
import time
from typing import Any

USER_DB: dict[str, dict] = {}
TOKEN_BLACKLIST: set[str] = set()

DEMO_USERS: dict[str, dict] = {
    "demo": {
        "user_id": "demo",
        "password_hash": hashlib.sha256("demo123".encode()).hexdigest(),
        "role": "user",
        "created_at": "2025-01-01T00:00:00Z",
    },
    "admin": {
        "user_id": "admin",
        "password_hash": hashlib.sha256("admin123".encode()).hexdigest(),
        "role": "admin",
        "created_at": "2025-01-01T00:00:00Z",
    },
}
USER_DB.update(DEMO_USERS)

_ALGORITHM = "HS256"
_ACCESS_TOKEN_EXPIRE = 3600
_REFRESH_TOKEN_EXPIRE = 86400 * 7

try:
    from jose import JWTError, jwt

    def _create_token(data: dict, secret: str, expires_in: int) -> str:
        payload = data.copy()
        payload["exp"] = int(time.time()) + expires_in
        payload["iat"] = int(time.time())
        payload["jti"] = secrets.token_hex(16)
        return jwt.encode(payload, secret, algorithm=_ALGORITHM)

    def _decode_token(token: str, secret: str) -> dict[str, Any] | None:
        try:
            payload = jwt.decode(token, secret, algorithms=[_ALGORITHM])
            if payload.get("jti") in TOKEN_BLACKLIST:
                return None
            return payload
        except JWTError:
            return None

    JWT_AVAILABLE = True
except ImportError:

    def _create_token(data: dict, secret: str, expires_in: int) -> str:
        return ""

    def _decode_token(token: str, secret: str) -> dict[str, Any] | None:
        return None

    JWT_AVAILABLE = False


def get_jwt_status() -> dict:
    return {
        "jwt_available": JWT_AVAILABLE,
        "algorithm": _ALGORITHM,
        "access_token_expire": _ACCESS_TOKEN_EXPIRE,
        "users_registered": len(USER_DB),
    }


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, password_hash: str) -> bool:
    return hash_password(password) == password_hash


def create_user(user_id: str, password: str, role: str = "user") -> dict:
    if user_id in USER_DB:
        raise ValueError(f"User '{user_id}' already exists")
    user = {
        "user_id": user_id,
        "password_hash": hash_password(password),
        "role": role,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    USER_DB[user_id] = user
    return {k: v for k, v in user.items() if k != "password_hash"}


def authenticate_user(user_id: str, password: str) -> dict | None:
    user = USER_DB.get(user_id)
    if not user:
        return None
    if not verify_password(password, user["password_hash"]):
        return None
    return {k: v for k, v in user.items() if k != "password_hash"}


def login(user_id: str, password: str, jwt_secret: str) -> dict | None:
    user = authenticate_user(user_id, password)
    if not user:
        return None
    if not JWT_AVAILABLE:
        return {"user": user, "access_token": None, "token_type": None}
    access_token = _create_token(
        {"sub": user_id, "role": user["role"]},
        jwt_secret,
        _ACCESS_TOKEN_EXPIRE,
    )
    refresh_token = _create_token(
        {"sub": user_id, "role": user["role"], "type": "refresh"},
        jwt_secret,
        _REFRESH_TOKEN_EXPIRE,
    )
    return {
        "user": user,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": _ACCESS_TOKEN_EXPIRE,
    }


def refresh_token(refresh_token_str: str, jwt_secret: str) -> dict | None:
    payload = _decode_token(refresh_token_str, jwt_secret)
    if not payload or payload.get("type") != "refresh":
        return None
    user_id = payload.get("sub")
    user = USER_DB.get(user_id)
    if not user:
        return None
    access_token = _create_token(
        {"sub": user_id, "role": user["role"]},
        jwt_secret,
        _ACCESS_TOKEN_EXPIRE,
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": _ACCESS_TOKEN_EXPIRE,
    }


def validate_token(token: str, jwt_secret: str) -> dict | None:
    payload = _decode_token(token, jwt_secret)
    if not payload:
        return None
    user_id = payload.get("sub")
    user = USER_DB.get(user_id)
    if not user:
        return None
    return {"user_id": user_id, "role": user["role"], "payload": payload}


def logout(token: str, jwt_secret: str) -> bool:
    payload = _decode_token(token, jwt_secret)
    if payload and payload.get("jti"):
        TOKEN_BLACKLIST.add(payload["jti"])
        return True
    return False
