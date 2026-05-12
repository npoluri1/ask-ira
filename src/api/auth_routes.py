import hashlib
import secrets
import time

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from src.auth import TOKEN_BLACKLIST
from src.config.settings import get_settings

settings = get_settings()
SECRET_KEY = settings.jwt_secret or secrets.token_hex(32)
ALGORITHM = settings.jwt_algorithm
ACCESS_TOKEN_EXPIRE = settings.jwt_expire_minutes * 60
REFRESH_TOKEN_EXPIRE = 86400 * 7

router = APIRouter(prefix="/api/v1/auth")
security = HTTPBearer(auto_error=False)

users_db: dict[str, dict] = {}

_seed_pwd = hashlib.sha256("admin123".encode()).hexdigest()
users_db["admin"] = {"username": "admin", "password": _seed_pwd, "email": "admin@askira.com", "role": "admin", "created_at": time.time()}
users_db["demo"] = {"username": "demo", "password": hashlib.sha256("demo123".encode()).hexdigest(), "email": "demo@askira.com", "role": "user", "created_at": time.time()}


class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    password: str
    email: str = ""


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
    user: dict


def _create_token(data: dict, expires_in: int) -> str:
    import jwt as pyjwt
    payload = data.copy()
    payload["exp"] = int(time.time()) + expires_in
    payload["iat"] = int(time.time())
    payload["jti"] = secrets.token_hex(16)
    return pyjwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def _decode_token(token: str) -> dict | None:
    import jwt as pyjwt
    try:
        payload = pyjwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("jti") in TOKEN_BLACKLIST:
            return None
        return payload
    except Exception:
        return None


@router.post("/register")
async def register(body: RegisterRequest):
    if body.username in users_db:
        raise HTTPException(400, "Username already exists")
    if len(body.password) < 4:
        raise HTTPException(400, "Password must be at least 4 characters")
    pwd_hash = hashlib.sha256(body.password.encode()).hexdigest()
    users_db[body.username] = {
        "username": body.username,
        "password": pwd_hash,
        "email": body.email,
        "role": "user",
        "created_at": time.time(),
    }
    access_token = _create_token({"sub": body.username, "role": "user"}, ACCESS_TOKEN_EXPIRE)
    refresh_token = _create_token({"sub": body.username, "role": "user", "type": "refresh"}, REFRESH_TOKEN_EXPIRE)
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE,
        user={"username": body.username, "email": body.email, "role": "user"},
    )


@router.post("/login")
async def login(body: LoginRequest):
    user = users_db.get(body.username)
    if not user:
        raise HTTPException(401, "Invalid credentials")
    pwd_hash = hashlib.sha256(body.password.encode()).hexdigest()
    if user["password"] != pwd_hash:
        raise HTTPException(401, "Invalid credentials")
    access_token = _create_token({"sub": body.username, "role": user.get("role", "user")}, ACCESS_TOKEN_EXPIRE)
    refresh_token = _create_token({"sub": body.username, "role": user.get("role", "user"), "type": "refresh"}, REFRESH_TOKEN_EXPIRE)
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE,
        user={"username": body.username, "email": user.get("email", ""), "role": user.get("role", "user")},
    )


@router.post("/refresh")
async def refresh(body: dict | None = None, credentials: HTTPAuthorizationCredentials = Depends(security)):
    token_str = None
    if body and "refresh_token" in body:
        token_str = body["refresh_token"]
    elif credentials:
        token_str = credentials.credentials

    if not token_str:
        raise HTTPException(401, "Refresh token required")

    payload = _decode_token(token_str)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(401, "Invalid refresh token")
    username = payload.get("sub")
    user = users_db.get(username)
    if not user:
        raise HTTPException(401, "User not found")
    new_access = _create_token({"sub": username, "role": user.get("role", "user")}, ACCESS_TOKEN_EXPIRE)
    return {
        "access_token": new_access,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE,
    }


@router.post("/logout")
async def logout(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if not credentials:
        raise HTTPException(401, "Not authenticated")
    payload = _decode_token(credentials.credentials)
    if payload and payload.get("jti"):
        TOKEN_BLACKLIST.add(payload["jti"])
    return {"message": "Logged out successfully"}


@router.get("/status")
async def auth_status(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if not credentials:
        return {"authenticated": False}
    payload = _decode_token(credentials.credentials)
    if not payload:
        return {"authenticated": False}
    username = payload.get("sub")
    user = users_db.get(username)
    if not user:
        return {"authenticated": False}
    return {
        "authenticated": True,
        "user": {
            "username": username,
            "email": user.get("email", ""),
            "role": user.get("role", "user"),
            "created_at": user.get("created_at"),
        },
    }


@router.get("/profile")
async def profile(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if not credentials:
        raise HTTPException(401, "Not authenticated")
    payload = _decode_token(credentials.credentials)
    if not payload:
        raise HTTPException(401, "Invalid or expired token")
    username = payload.get("sub")
    user = users_db.get(username)
    if not user:
        raise HTTPException(401, "User not found")
    return {
        "username": user["username"],
        "email": user.get("email", ""),
        "role": user.get("role", "user"),
        "created_at": user.get("created_at"),
    }


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    if not credentials:
        raise HTTPException(401, "Not authenticated")
    payload = _decode_token(credentials.credentials)
    if not payload:
        raise HTTPException(401, "Invalid or expired token")
    user = users_db.get(payload.get("sub"))
    if not user:
        raise HTTPException(401, "User not found")
    return payload.get("sub", "unknown")
