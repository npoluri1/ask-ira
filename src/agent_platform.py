import asyncio
import hashlib
import hmac
import json
import time
import uuid
from collections import defaultdict
from typing import Any, Callable

AGENT_REGISTRY: dict[str, dict] = {}
AGENT_INSTANCES: dict[str, dict] = {}
AGENT_LEDGER: list[dict] = []
AGENT_MESH_BUFFER: dict[str, list[dict]] = defaultdict(list)
AGENT_METRICS: dict[str, dict] = defaultdict(lambda: {"runs": 0, "success": 0, "failures": 0, "total_latency": 0, "total_tokens": 0})
AGENT_SANDBOX_CONFIG: dict[str, dict] = {}


def _generate_id(prefix: str = "") -> str:
    return f"{prefix}{uuid.uuid4().hex}" if prefix else uuid.uuid4().hex


def _hash_payload(payload: dict) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


def _now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S.") + f"{int(time.time() * 1000000) % 1000000:06d}Z"


# ============================================================
# AGENT REGISTRY
# ============================================================
def register_agent_type(agent_type: str, schema: dict, capabilities: list[str], sla_seconds: int = 30, cost_per_call: float = 0.001, timeout: int = 30, allowed_tools: list[str] | None = None, blocked_patterns: list[str] | None = None, version: str = "1.0.0") -> dict:
    entry = {
        "agent_type": agent_type,
        "schema": schema,
        "capabilities": capabilities,
        "sla_seconds": sla_seconds,
        "cost_per_call": cost_per_call,
        "timeout": timeout,
        "allowed_tools": allowed_tools or [],
        "blocked_patterns": blocked_patterns or [],
        "version": version,
        "registered_at": _now_iso(),
        "status": "active",
    }
    AGENT_REGISTRY[agent_type] = entry
    AGENT_SANDBOX_CONFIG[agent_type] = {"timeout": timeout, "allowed_tools": allowed_tools or [], "blocked_patterns": blocked_patterns or []}
    return entry


def get_registered_agent_types() -> dict[str, dict]:
    return {k: {kk: vv for kk, vv in v.items() if kk != "schema"} for k, v in AGENT_REGISTRY.items()}


def get_agent_type(agent_type: str) -> dict | None:
    return AGENT_REGISTRY.get(agent_type)


def deregister_agent_type(agent_type: str) -> bool:
    if agent_type in AGENT_REGISTRY:
        AGENT_REGISTRY[agent_type]["status"] = "inactive"
        return True
    return False


# ============================================================
# AGENT SPAWNER
# ============================================================
def spawn_agent(agent_type: str, params: dict, user_id: str = "system", timeout_seconds: int | None = None, on_complete: str | None = None, trace_id: str | None = None) -> dict:
    registered = AGENT_REGISTRY.get(agent_type)
    if not registered:
        raise ValueError(f"Unknown agent type: {agent_type}")

    instance_id = _generate_id("agent_")
    trace = trace_id or _generate_id("trace_")
    instance = {
        "instance_id": instance_id,
        "agent_type": agent_type,
        "params": params,
        "user_id": user_id,
        "status": "spawned",
        "trace_id": trace,
        "timeout": timeout_seconds or registered["timeout"],
        "on_complete": on_complete,
        "spawned_at": _now_iso(),
        "started_at": None,
        "completed_at": None,
        "result": None,
        "error": None,
    }
    AGENT_INSTANCES[instance_id] = instance
    return instance


def start_agent(instance_id: str) -> dict:
    inst = AGENT_INSTANCES.get(instance_id)
    if not inst:
        raise ValueError(f"Unknown instance: {instance_id}")
    inst["status"] = "running"
    inst["started_at"] = _now_iso()
    return inst


def complete_agent(instance_id: str, result: dict) -> dict:
    inst = AGENT_INSTANCES.get(instance_id)
    if not inst:
        raise ValueError(f"Unknown instance: {instance_id}")
    inst["status"] = "completed"
    inst["completed_at"] = _now_iso()
    inst["result"] = result
    return inst


def fail_agent(instance_id: str, error: str) -> dict:
    inst = AGENT_INSTANCES.get(instance_id)
    if not inst:
        raise ValueError(f"Unknown instance: {instance_id}")
    inst["status"] = "failed"
    inst["completed_at"] = _now_iso()
    inst["error"] = error
    return inst


def get_agent_instance(instance_id: str) -> dict | None:
    return AGENT_INSTANCES.get(instance_id)


def get_active_instances(agent_type: str | None = None) -> list[dict]:
    instances = [i for i in AGENT_INSTANCES.values() if i["status"] in ("spawned", "running")]
    if agent_type:
        instances = [i for i in instances if i["agent_type"] == agent_type]
    return instances


def kill_agent(instance_id: str) -> dict:
    inst = AGENT_INSTANCES.get(instance_id)
    if not inst:
        raise ValueError(f"Unknown instance: {instance_id}")
    inst["status"] = "killed"
    inst["completed_at"] = _now_iso()
    inst["error"] = "Manually killed"
    return inst


# ============================================================
# AGENT MESH (Message Bus)
# ============================================================
def send_message(source: str, target: str, message_type: str, payload: dict, trace_id: str | None = None, ttl: int = 30) -> dict:
    msg = {
        "id": _generate_id("msg_"),
        "source": source,
        "target": target,
        "type": message_type,
        "payload": payload,
        "trace_id": trace_id or _generate_id("trace_"),
        "timestamp": _now_iso(),
        "ttl": ttl,
    }
    AGENT_MESH_BUFFER[target].append(msg)
    return msg


def consume_messages(target: str, limit: int = 10) -> list[dict]:
    messages = AGENT_MESH_BUFFER[target][:limit]
    AGENT_MESH_BUFFER[target] = AGENT_MESH_BUFFER[target][limit:]
    return messages


def get_mesh_stats() -> dict:
    return {
        "total_topics": len(AGENT_MESH_BUFFER),
        "total_messages": sum(len(v) for v in AGENT_MESH_BUFFER.values()),
        "topics": {k: len(v) for k, v in AGENT_MESH_BUFFER.items()},
    }


# ============================================================
# AGENT GOVERNOR (Rate Limits + Budget)
# ============================================================
AGENT_RATE_LIMITS: dict[str, dict] = {}


def set_agent_rate_limit(agent_type: str, max_calls_per_minute: int = 60, max_tokens_per_call: int = 4096, max_concurrent: int = 10, budget_per_day: float = 10.0) -> dict:
    rule = {
        "agent_type": agent_type,
        "max_calls_per_minute": max_calls_per_minute,
        "max_tokens_per_call": max_tokens_per_call,
        "max_concurrent": max_concurrent,
        "budget_per_day": budget_per_day,
        "budget_spent_today": 0.0,
    }
    AGENT_RATE_LIMITS[agent_type] = rule
    return rule


def check_agent_quota(agent_type: str, token_count: int = 0) -> dict:
    rule = AGENT_RATE_LIMITS.get(agent_type, {})
    if not rule:
        return {"allowed": True}
    active = len([i for i in AGENT_INSTANCES.values() if i["agent_type"] == agent_type and i["status"] == "running"])
    if active >= rule.get("max_concurrent", 99):
        return {"allowed": False, "reason": f"Max concurrent ({rule['max_concurrent']}) reached"}
    if rule.get("budget_spent_today", 0) >= rule.get("budget_per_day", 999):
        return {"allowed": False, "reason": "Daily budget exhausted"}
    return {"allowed": True}


def record_agent_usage(agent_type: str, tokens: int = 0, cost: float = 0.0):
    if agent_type in AGENT_RATE_LIMITS:
        AGENT_RATE_LIMITS[agent_type]["budget_spent_today"] = AGENT_RATE_LIMITS[agent_type].get("budget_spent_today", 0) + cost


# ============================================================
# AGENT LEDGER (Immutable Audit)
# ============================================================
def log_agent_action(agent_type: str, instance_id: str, user_id: str, action: str, payload: dict, parent_event_id: str | None = None) -> dict:
    payload_hash = _hash_payload(payload)
    signature = hmac.new(f"agent-ledger-key-{agent_type}".encode(), payload_hash.encode(), hashlib.sha256).hexdigest()
    entry = {
        "event_id": _generate_id("evt_"),
        "timestamp": _now_iso(),
        "agent_type": agent_type,
        "instance_id": instance_id,
        "user_id": user_id,
        "action": action,
        "payload_hash": payload_hash,
        "parent_event_id": parent_event_id,
        "signature": signature,
        "blockchain_anchor": None,
    }
    AGENT_LEDGER.append(entry)
    return entry


def get_audit_trail(agent_type: str | None = None, user_id: str | None = None, limit: int = 100) -> list[dict]:
    entries = AGENT_LEDGER
    if agent_type:
        entries = [e for e in entries if e["agent_type"] == agent_type]
    if user_id:
        entries = [e for e in entries if e["user_id"] == user_id]
    return list(reversed(entries))[:limit]


def get_audit_entry(event_id: str) -> dict | None:
    for e in AGENT_LEDGER:
        if e["event_id"] == event_id:
            return e
    return None


def verify_ledger_integrity() -> dict:
    for i, entry in enumerate(AGENT_LEDGER):
        expected_hash = _hash_payload(entry.get("payload", {}))
        if entry["payload_hash"] != expected_hash:
            return {"valid": False, "tampered_entry": i, "event_id": entry["event_id"]}
    return {"valid": True, "total_entries": len(AGENT_LEDGER)}


# ============================================================
# AGENT MONITOR
# ============================================================
def record_metric(agent_type: str, latency: float, success: bool, tokens: int = 0):
    m = AGENT_METRICS[agent_type]
    m["runs"] += 1
    if success:
        m["success"] += 1
    else:
        m["failures"] += 1
    m["total_latency"] += latency
    m["total_tokens"] += tokens


def get_agent_metrics(agent_type: str | None = None) -> dict:
    if agent_type:
        m = AGENT_METRICS.get(agent_type, {})
        return {
            "agent_type": agent_type,
            "runs": m.get("runs", 0),
            "success_rate": round(m.get("success", 0) / max(m.get("runs", 1), 1) * 100, 2),
            "avg_latency": round(m.get("total_latency", 0) / max(m.get("runs", 1), 1), 3),
            "avg_tokens": round(m.get("total_tokens", 0) / max(m.get("runs", 1), 1), 0),
            "total_tokens": m.get("total_tokens", 0),
        }
    return {at: get_agent_metrics(at) for at in AGENT_METRICS}


def get_platform_health() -> dict:
    total = len(AGENT_REGISTRY)
    active_types = sum(1 for a in AGENT_REGISTRY.values() if a.get("status") == "active")
    running = len([i for i in AGENT_INSTANCES.values() if i["status"] == "running"])
    return {
        "registered_agent_types": total,
        "active_agent_types": active_types,
        "running_instances": running,
        "total_instances_spawned": len(AGENT_INSTANCES),
        "total_ledger_entries": len(AGENT_LEDGER),
        "mesh_messages_pending": sum(len(v) for v in AGENT_MESH_BUFFER.values()),
    }


# ============================================================
# AGENT SANDBOX DECORATOR
# ============================================================
def agent_sandbox(agent_type: str = "", timeout: int = 30, max_tokens: int = 4096, allowed_tools: list[str] | None = None, blocked_patterns: list[str] | None = None, audit: bool = True, max_calls_per_session: int = 100):
    def decorator(func: Callable):
        async def wrapper(*args, **kwargs):
            record_agent_usage(agent_type)
            if audit:
                log_agent_action(agent_type, "", "system", f"sandbox_call_{func.__name__}", {"args": str(args)[:200]})
            start = time.time()
            try:
                result = await asyncio.wait_for(func(*args, **kwargs), timeout=timeout)
                record_metric(agent_type, time.time() - start, True)
                return result
            except asyncio.TimeoutError:
                record_metric(agent_type, timeout, False)
                raise TimeoutError(f"Agent {agent_type} timed out after {timeout}s")
            except Exception:
                record_metric(agent_type, time.time() - start, False)
                raise
        return wrapper
    return decorator


# ============================================================
# PARALLEL / PIPELINE EXECUTION
# ============================================================
async def run_agents_parallel(agents: list[dict], strategy: str = "all") -> list[dict]:
    async def _run_single(a: dict) -> dict:
        instance = spawn_agent(a["type"], a.get("params", {}), a.get("user_id", "system"))
        start_agent(instance["instance_id"])
        try:
            result = {"type": a["type"], "status": "completed", "result": a.get("handler", lambda: {})(), "instance_id": instance["instance_id"]}
            complete_agent(instance["instance_id"], result)
        except Exception as e:
            fail_agent(instance["instance_id"], str(e))
            result = {"type": a["type"], "status": "failed", "error": str(e), "instance_id": instance["instance_id"]}
        return result

    tasks = [_run_single(a) for a in agents]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    processed = [r if not isinstance(r, Exception) else {"status": "error"} for r in results]
    return processed


async def run_agent_pipeline(steps: list[dict]) -> list[dict]:
    results: dict[int, Any] = {}
    outputs: list[dict] = []
    for i, step in enumerate(steps):
        deps = step.get("depends_on", [])
        for d in deps:
            if d not in results:
                raise ValueError(f"Step {i} depends on step {d} which hasn't run yet")
        instance = spawn_agent(step["agent"], step.get("params", {}), step.get("user_id", "system"))
        start_agent(instance["instance_id"])
        try:
            result_value = step.get("handler", lambda r: {})(results)
            result = {"step": i, "agent": step["agent"], "status": "completed", "result": result_value, "instance_id": instance["instance_id"]}
            complete_agent(instance["instance_id"], result)
            results[i] = result_value
        except Exception as e:
            fail_agent(instance["instance_id"], str(e))
            result = {"step": i, "agent": step["agent"], "status": "failed", "error": str(e), "instance_id": instance["instance_id"]}
        outputs.append(result)
    return outputs


# ============================================================
# REGISTER DEFAULT FINANCIAL AGENTS
# ============================================================
def register_default_agents():
    agents = [
        ("banking.accounts.create", {"params": ["user_id", "account_type", "currency"]}, ["create_accounts", "manage_balances"], 15),
        ("banking.payments.swift", {"params": ["amount", "currency", "beneficiary_iban", "bic"]}, ["swift_mt103", "cross_border"], 30),
        ("banking.payments.sepa", {"params": ["amount", "from_iban", "to_iban"]}, ["sepa_credit", "sepa_debit"], 15),
        ("banking.payments.ach", {"params": ["amount", "routing", "account"]}, ["ach_credit", "ach_debit"], 20),
        ("banking.cards.authorize", {"params": ["card_id", "amount", "merchant"]}, ["card_auth", "fraud_check"], 5),
        ("banking.reconciliation", {"params": ["date"]}, ["match_statements", "flag_discrepancies"], 60),
        ("banking.treasury", {"params": ["user_id"]}, ["cash_flow_forecast", "liquidity_optimization"], 30),
        ("insurance.underwriting.life", {"params": ["age", "health_data", "coverage"]}, ["risk_assessment", "premium_calc"], 20),
        ("insurance.claims.photo", {"params": ["image_data"]}, ["damage_estimation", "auto_adjudication"], 15),
        ("insurance.policy.renew", {"params": ["policy_id"]}, ["auto_renew", "premium_adjustment"], 10),
        ("crypto.wallet.create", {"params": ["currency", "wallet_type"]}, ["hd_wallet", "multi_sig"], 10),
        ("crypto.swap", {"params": ["from_currency", "to_currency", "amount"]}, ["dex_routing", "price_impact"], 15),
        ("crypto.staking", {"params": ["currency", "amount", "validator"]}, ["stake", "claim_rewards"], 20),
        ("compliance.kyc", {"params": ["user_id", "documents"]}, ["identity_verification", "document_check"], 30),
        ("compliance.aml", {"params": ["user_id", "transaction"]}, ["sanctions_screening", "pep_check", "risk_scoring"], 20),
        ("compliance.sar", {"params": ["transaction_id", "reason"]}, ["sar_filing", "regulatory_reporting"], 30),
        ("fx.rate", {"params": ["pair"]}, ["live_rates", "spread_calc"], 5),
        ("fx.hedge", {"params": ["amount", "from_currency", "to_currency"]}, ["forward_contracts", "auto_hedge"], 20),
        ("notification.send", {"params": ["user_id", "message", "channel"]}, ["email", "sms", "push"], 5),
        ("audit.logger", {"params": ["action", "payload"]}, ["immutable_logging", "blockchain_anchor"], 5),
    ]
    for agent_type, schema, capabilities, sla in agents:
        register_agent_type(agent_type, schema, capabilities, sla)
        set_agent_rate_limit(agent_type, max_calls_per_minute=120, budget_per_day=5.0)


register_default_agents()
