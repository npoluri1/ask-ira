import hashlib
import hmac
import json
import secrets
import time
from typing import Any

from src.auth import USER_DB, TOKEN_BLACKLIST, _create_token, _decode_token, hash_password, validate_token
from src.config.settings import get_settings

settings = get_settings()
JWT_SECRET = settings.jwt_secret or "default-secret-change-me-in-production"
SESSIONS_DB: dict[str, dict] = {}
DEVICE_FINGERPRINTS: dict[str, str] = {}
MFA_CODES: dict[str, dict] = {}

# ============================================================
# STEP-UP AUTHENTICATION
# ============================================================
RISK_LEVELS = {"low": 1000, "medium": 10000, "high": 100000, "critical": float("inf")}


def _check_user_exists(user_id: str) -> bool:
    return user_id in USER_DB


async def authorize_action(user_id: str, action: str, amount: float = 0) -> dict:
    user = USER_DB.get(user_id)
    if not user:
        return {"authorized": False, "reason": "User not found", "required_auth": "login"}

    role = user.get("role", "user")
    if action == "payment" and role == "user":
        if amount < RISK_LEVELS["low"]:
            return {"authorized": True, "method": "jwt", "level": "low"}
        elif amount < RISK_LEVELS["medium"]:
            return {"authorized": True, "method": "sms_otp", "level": "medium", "challenge": "sms_otp"}
        elif amount < RISK_LEVELS["high"]:
            return {"authorized": False, "method": "webauthn", "level": "high", "challenge": "webauthn", "reason": "WebAuthn challenge required"}
        else:
            return {"authorized": False, "method": "human_approval", "level": "critical", "challenge": "human_workflow", "reason": "Human approval workflow required"}

    if action == "admin" and role != "admin":
        return {"authorized": False, "reason": "Admin access required", "required_auth": "admin_login"}

    return {"authorized": True, "method": "jwt", "level": "low"}


# ============================================================
# SESSION BINDING (Device fingerprint)
# ============================================================
def create_session(user_id: str, device_fingerprint: str, ip_address: str) -> dict:
    session_id = secrets.token_hex(32)
    session = {
        "session_id": session_id,
        "user_id": user_id,
        "device_fingerprint": hashlib.sha256(device_fingerprint.encode()).hexdigest(),
        "ip_address": ip_address,
        "created_at": time.time(),
        "last_activity": time.time(),
        "expires_at": time.time() + 3600,
        "is_valid": True,
    }
    SESSIONS_DB[session_id] = session
    key = f"{user_id}:{session['device_fingerprint']}"
    DEVICE_FINGERPRINTS[key] = session_id
    return session


def validate_session(session_id: str, device_fingerprint: str, ip_address: str) -> dict:
    session = SESSIONS_DB.get(session_id)
    if not session:
        return {"valid": False, "reason": "Session not found"}
    if not session["is_valid"]:
        return {"valid": False, "reason": "Session revoked"}
    if time.time() > session["expires_at"]:
        return {"valid": False, "reason": "Session expired"}

    stored_fp = session["device_fingerprint"]
    current_fp = hashlib.sha256(device_fingerprint.encode()).hexdigest()
    if stored_fp != current_fp:
        return {"valid": False, "reason": "Device fingerprint mismatch (possible session hijacking)"}

    session["last_activity"] = time.time()
    return {"valid": True, "user_id": session["user_id"]}


def revoke_session(session_id: str) -> bool:
    if session_id in SESSIONS_DB:
        SESSIONS_DB[session_id]["is_valid"] = False
        return True
    return False


def revoke_all_user_sessions(user_id: str) -> int:
    count = 0
    for s in SESSIONS_DB.values():
        if s["user_id"] == user_id and s["is_valid"]:
            s["is_valid"] = False
            count += 1
    return count


# ============================================================
# MFA (Multi-Factor Authentication)
# ============================================================
def generate_mfa_code(user_id: str, method: str = "sms") -> dict:
    code = str(secrets.randbelow(900000) + 100000)
    MFA_CODES[f"{user_id}:{method}"] = {
        "code": hashlib.sha256(code.encode()).hexdigest(),
        "expires_at": time.time() + 300,
        "method": method,
        "attempts": 0,
    }
    return {
        "mfa_id": f"mfa_{user_id}_{int(time.time())}",
        "delivered_via": method,
        "expires_in": 300,
        "code_preview": f"****{code[-3:]}",
    }


def verify_mfa_code(user_id: str, code: str, method: str = "sms") -> dict:
    stored = MFA_CODES.get(f"{user_id}:{method}")
    if not stored:
        return {"valid": False, "reason": "No MFA code found"}
    if time.time() > stored["expires_at"]:
        return {"valid": False, "reason": "MFA code expired"}
    stored["attempts"] += 1
    if stored["attempts"] > 5:
        return {"valid": False, "reason": "Too many attempts"}
    code_hash = hashlib.sha256(code.encode()).hexdigest()
    if code_hash != stored["code"]:
        return {"valid": False, "reason": "Invalid code"}
    del MFA_CODES[f"{user_id}:{method}"]
    return {"valid": True, "user_id": user_id}


# ============================================================
# RBAC (Role-Based Access Control)
# ============================================================
RBAC_POLICIES: dict[str, dict] = {
    "user": {
        "permissions": [
            "accounts:read:own", "accounts:create:own", "accounts:close:own",
            "transfers:create:own", "transfers:read:own",
            "payments:create:own", "payments:read:own",
            "portfolio:read:own", "trades:create:own", "trades:read:own",
            "insurance:read:own", "insurance:create:own",
            "crypto:read:own", "crypto:send:own",
        ],
        "limits": {"daily_payment": 10000, "daily_trade": 50000, "daily_withdrawal": 5000},
    },
    "viewer": {
        "permissions": [
            "accounts:read:own", "transfers:read:own",
            "payments:read:own", "portfolio:read:own",
            "insurance:read:own", "crypto:read:own",
        ],
        "limits": {},
    },
    "treasurer": {
        "permissions": [
            "payments:create:up_to_10k", "payments:read:all",
            "accounts:read:all", "transfers:create:up_to_10k",
            "treasury:read", "reports:read",
        ],
        "limits": {"daily_payment": 10000, "daily_transfer": 10000},
    },
    "approver": {
        "permissions": [
            "payments:approve", "payments:read:all",
            "transfers:approve", "trades:approve",
            "audit:read",
        ],
        "limits": {},
    },
    "compliance_officer": {
        "permissions": [
            "transactions:read:all", "users:read:all",
            "audit:read", "sar:file", "sar:read",
            "compliance:read", "kyc:review", "kyc:approve",
        ],
        "limits": {},
    },
    "admin": {
        "permissions": ["*"],
        "limits": {},
    },
    "regulator": {
        "permissions": [
            "audit:read", "transactions:read:all",
            "reports:generate", "compliance:read",
        ],
        "limits": {},
    },
}


def check_permission(user_id: str, permission: str) -> dict:
    user = USER_DB.get(user_id)
    if not user:
        return {"authorized": False, "reason": "User not found"}

    role = user.get("role", "user")
    policy = RBAC_POLICIES.get(role, RBAC_POLICIES["user"])
    permissions = policy.get("permissions", [])

    if "*" in permissions:
        return {"authorized": True, "role": role}

    if permission in permissions:
        return {"authorized": True, "role": role}

    for p in permissions:
        if p.endswith(":*"):
            prefix = p[:-2]
            if permission.startswith(prefix):
                return {"authorized": True, "role": role}
        if p.endswith(":own"):
            prefix = p[:-4]
            if permission.startswith(prefix):
                return {"authorized": True, "role": role}

    return {"authorized": False, "reason": f"Permission '{permission}' not granted to role '{role}'"}


def get_user_limits(user_id: str) -> dict:
    user = USER_DB.get(user_id)
    role = user.get("role", "user") if user else "user"
    return RBAC_POLICIES.get(role, RBAC_POLICIES["user"]).get("limits", {})


def get_role_permissions(role: str) -> list[str]:
    return RBAC_POLICIES.get(role, {}).get("permissions", [])


# ============================================================
# API KEY MANAGEMENT
# ============================================================
API_KEYS_DB: dict[str, dict] = {}


def generate_api_key(user_id: str, name: str, permissions: list[str] | None = None) -> dict:
    key = f"ira_{secrets.token_urlsafe(32)}"
    key_id = hashlib.sha256(key.encode()).hexdigest()[:16]
    API_KEYS_DB[key_id] = {
        "key_id": key_id,
        "user_id": user_id,
        "name": name,
        "key_hash": hashlib.sha256(key.encode()).hexdigest(),
        "permissions": permissions or ["accounts:read:own"],
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "last_used": None,
        "is_active": True,
    }
    return {"key_id": key_id, "api_key": key, "name": name}


def validate_api_key(api_key: str) -> dict | None:
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    for k, v in API_KEYS_DB.items():
        if v["key_hash"] == key_hash and v["is_active"]:
            v["last_used"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            return {"user_id": v["user_id"], "permissions": v["permissions"], "key_id": k}
    return None


def revoke_api_key(key_id: str) -> bool:
    if key_id in API_KEYS_DB:
        API_KEYS_DB[key_id]["is_active"] = False
        return True
    return False


# ============================================================
# ENCRYPTION HELPERS
# ============================================================
def encrypt_field(value: str, key: str | None = None) -> str:
    encryption_key = key or JWT_SECRET
    iv = secrets.token_hex(16)
    tag = hashlib.sha256(f"{encryption_key}:{iv}:{value}".encode()).hexdigest()[:16]
    return f"enc:{iv}:{tag}:{hashlib.sha256(value.encode()).hexdigest()}"


def decrypt_field(encrypted: str, key: str | None = None) -> str:
    encryption_key = key or JWT_SECRET
    if not encrypted.startswith("enc:"):
        return encrypted
    parts = encrypted.split(":")
    if len(parts) != 4:
        return encrypted
    _, iv, tag, data_hash = parts
    expected_tag = hashlib.sha256(f"{encryption_key}:{iv}:{data_hash}".encode()).hexdigest()[:16]
    if tag != expected_tag:
        return "[DECRYPTION FAILED]"
    return data_hash


# ============================================================
# AUDIT LOG
# ============================================================
AUDIT_LOG: list[dict] = []


def log_security_event(user_id: str, event_type: str, details: dict, severity: str = "info") -> dict:
    entry = {
        "event_id": f"sec_{int(time.time())}_{secrets.token_hex(4)}",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "user_id": user_id,
        "event_type": event_type,
        "details": details,
        "severity": severity,
        "ip_address": details.get("ip", "unknown"),
    }
    AUDIT_LOG.append(entry)
    return entry


def get_security_log(user_id: str | None = None, event_type: str | None = None, limit: int = 100) -> list[dict]:
    entries = AUDIT_LOG
    if user_id:
        entries = [e for e in entries if e["user_id"] == user_id]
    if event_type:
        entries = [e for e in entries if e["event_type"] == event_type]
    return list(reversed(entries))[:limit]
