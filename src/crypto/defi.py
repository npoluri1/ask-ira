from __future__ import annotations

import time
import uuid
from typing import Any, Dict, List

PROTOCOLS: Dict[str, Dict[str, Any]] = {
    "uniswap_v3": {"name": "Uniswap V3", "tvl": 3800000000, "avg_apy": 15.0, "risk": "medium"},
    "aave": {"name": "Aave", "tvl": 12000000000, "avg_apy": 4.5, "risk": "low"},
    "compound": {"name": "Compound", "tvl": 2800000000, "avg_apy": 3.8, "risk": "low"},
    "curve": {"name": "Curve", "tvl": 2100000000, "avg_apy": 8.2, "risk": "low"},
    "balancer": {"name": "Balancer", "tvl": 950000000, "avg_apy": 12.0, "risk": "medium"},
    "1inch": {"name": "1inch", "tvl": 420000000, "avg_apy": 6.5, "risk": "medium"},
}

LIQUIDITY_POOLS: Dict[str, List[Dict[str, Any]]] = {
    "uniswap_v3": [
        {"pair": "ETH/USDC", "fee": 0.05, "tvl": 1200000000, "apy": 18.5, "volume_24h": 450000000},
        {"pair": "ETH/USDT", "fee": 0.05, "tvl": 900000000, "apy": 16.2, "volume_24h": 380000000},
        {"pair": "BTC/ETH", "fee": 0.30, "tvl": 650000000, "apy": 12.0, "volume_24h": 210000000},
        {"pair": "SOL/ETH", "fee": 0.30, "tvl": 280000000, "apy": 22.0, "volume_24h": 95000000},
    ],
    "aave": [
        {"pair": "ETH/supply", "fee": 0.0, "tvl": 4500000000, "apy": 3.5, "volume_24h": 0},
        {"pair": "USDC/supply", "fee": 0.0, "tvl": 3200000000, "apy": 5.2, "volume_24h": 0},
        {"pair": "WBTC/supply", "fee": 0.0, "tvl": 1800000000, "apy": 1.8, "volume_24h": 0},
    ],
    "compound": [
        {"pair": "ETH/supply", "fee": 0.0, "tvl": 1100000000, "apy": 3.2, "volume_24h": 0},
        {"pair": "USDC/supply", "fee": 0.0, "tvl": 850000000, "apy": 4.8, "volume_24h": 0},
    ],
    "curve": [
        {"pair": "3pool", "fee": 0.01, "tvl": 750000000, "apy": 6.5, "volume_24h": 120000000},
        {"pair": "stETH/ETH", "fee": 0.04, "tvl": 580000000, "apy": 4.2, "volume_24h": 85000000},
    ],
    "balancer": [
        {"pair": "80ETH/20WBTC", "fee": 0.05, "tvl": 280000000, "apy": 14.0, "volume_24h": 42000000},
        {"pair": "50USDC/50DAI", "fee": 0.01, "tvl": 190000000, "apy": 8.5, "volume_24h": 28000000},
    ],
    "1inch": [
        {"pair": "multi-pool", "fee": 0.0, "tvl": 420000000, "apy": 6.5, "volume_24h": 180000000},
    ],
}

MOCK_SWAP_RATES: Dict[str, float] = {
    "ETH": 3450.0,
    "USDC": 1.0,
    "USDT": 1.0,
    "BTC": 67450.0,
    "SOL": 142.0,
    "MATIC": 0.72,
    "DAI": 1.0,
    "WBTC": 67450.0,
    "LINK": 16.50,
    "UNI": 8.20,
}


class LiquidityPosition:
    def __init__(
        self,
        position_id: str,
        user_id: str,
        protocol: str,
        pool: str,
        amount0: float,
        amount1: float,
        token0: str,
        token1: str,
        shares: float,
        value_usd: float,
        apy: float,
        status: str,
        created_at: float,
    ) -> None:
        self.position_id = position_id
        self.user_id = user_id
        self.protocol = protocol
        self.pool = pool
        self.amount0 = amount0
        self.amount1 = amount1
        self.token0 = token0
        self.token1 = token1
        self.shares = shares
        self.value_usd = value_usd
        self.apy = apy
        self.status = status
        self.created_at = created_at

    def to_dict(self) -> Dict[str, Any]:
        return {
            "position_id": self.position_id,
            "user_id": self.user_id,
            "protocol": self.protocol,
            "pool": self.pool,
            "amount0": self.amount0,
            "amount1": self.amount1,
            "token0": self.token0,
            "token1": self.token1,
            "shares": self.shares,
            "value_usd": self.value_usd,
            "apy": self.apy,
            "status": self.status,
            "created_at": self.created_at,
        }


class DeFiEngine:
    def __init__(self) -> None:
        self.POSITIONS_DB: Dict[str, Dict[str, LiquidityPosition]] = {}

    def get_protocols(self) -> List[Dict[str, Any]]:
        return [
            {
                "id": pid,
                "name": info["name"],
                "tvl": info["tvl"],
                "avg_apy": info["avg_apy"],
                "risk": info["risk"],
                "pool_count": len(LIQUIDITY_POOLS.get(pid, [])),
            }
            for pid, info in PROTOCOLS.items()
        ]

    def get_liquidity_pools(self, protocol: str) -> List[Dict[str, Any]]:
        if protocol not in LIQUIDITY_POOLS:
            raise ValueError(f"Unsupported protocol: {protocol}")
        return LIQUIDITY_POOLS[protocol]

    def provide_liquidity(
        self,
        user_id: str,
        protocol: str,
        pool: str,
        amount0: float,
        amount1: float,
        token0: str = "ETH",
        token1: str = "USDC",
    ) -> LiquidityPosition:
        if protocol not in PROTOCOLS:
            raise ValueError(f"Unsupported protocol: {protocol}")
        pool_list = LIQUIDITY_POOLS.get(protocol, [])
        matching_pool = next((p for p in pool_list if p["pair"] == pool), None)
        if matching_pool is None:
            raise ValueError(f"Pool {pool} not found on {protocol}")

        position_id = str(uuid.uuid4())
        value_usd = amount0 * MOCK_SWAP_RATES.get(token0, 1.0) + amount1 * MOCK_SWAP_RATES.get(token1, 1.0)
        apy = matching_pool["apy"]
        shares = (amount0 + amount1) * 1000

        position = LiquidityPosition(
            position_id=position_id,
            user_id=user_id,
            protocol=protocol,
            pool=pool,
            amount0=amount0,
            amount1=amount1,
            token0=token0,
            token1=token1,
            shares=shares,
            value_usd=value_usd,
            apy=apy,
            status="active",
            created_at=time.time(),
        )
        if user_id not in self.POSITIONS_DB:
            self.POSITIONS_DB[user_id] = {}
        self.POSITIONS_DB[user_id][position_id] = position
        return position

    def remove_liquidity(self, user_id: str, position_id: str) -> Dict[str, Any]:
        user_positions = self.POSITIONS_DB.get(user_id, {})
        position = user_positions.get(position_id)
        if position is None:
            raise ValueError(f"Position {position_id} not found")
        if position.status != "active":
            raise ValueError(f"Position {position_id} is not active")

        position.status = "withdrawn"
        return {
            "position_id": position_id,
            "protocol": position.protocol,
            "pool": position.pool,
            "amount0_returned": position.amount0,
            "amount1_returned": position.amount1,
            "value_usd_returned": position.value_usd,
            "status": "withdrawn",
        }

    def get_positions(self, user_id: str) -> List[LiquidityPosition]:
        user_positions = self.POSITIONS_DB.get(user_id, {})
        return list(user_positions.values())

    def get_yield_opportunities(
        self,
        min_tvl: float = 0.0,
        max_risk: str = "high",
    ) -> List[Dict[str, Any]]:
        risk_order = {"low": 0, "medium": 1, "high": 2}
        max_risk_level = risk_order.get(max_risk, 2)
        opportunities: List[Dict[str, Any]] = []
        for pid, info in PROTOCOLS.items():
            if info["tvl"] < min_tvl:
                continue
            if risk_order.get(info["risk"], 2) > max_risk_level:
                continue
            for pool in LIQUIDITY_POOLS.get(pid, []):
                if pool["tvl"] < min_tvl:
                    continue
                opportunities.append({
                    "protocol": pid,
                    "protocol_name": info["name"],
                    "pool": pool["pair"],
                    "tvl": pool["tvl"],
                    "apy": pool["apy"],
                    "risk": info["risk"],
                    "volume_24h": pool["volume_24h"],
                })
        opportunities.sort(key=lambda x: x["apy"], reverse=True)
        return opportunities

    def swap_quote(
        self,
        from_token: str,
        to_token: str,
        amount: float,
        protocol: str = "1inch",
    ) -> Dict[str, Any]:
        if protocol not in PROTOCOLS:
            raise ValueError(f"Unsupported protocol: {protocol}")
        from_rate = MOCK_SWAP_RATES.get(from_token.upper(), 1.0)
        to_rate = MOCK_SWAP_RATES.get(to_token.upper(), 1.0)
        if from_rate == 0 or to_rate == 0:
            raise ValueError(f"Unsupported token pair: {from_token}/{to_token}")

        exchange_rate = from_rate / to_rate
        gross_output = amount * exchange_rate
        price_impact = min(amount / 100000 * 0.1, 5.0)
        fee = amount * 0.003
        net_output = gross_output * (1 - price_impact / 100) - fee * exchange_rate

        return {
            "from_token": from_token.upper(),
            "to_token": to_token.upper(),
            "from_amount": amount,
            "to_amount": round(max(net_output, 0), 8),
            "exchange_rate": round(exchange_rate, 8),
            "price_impact_percent": round(price_impact, 4),
            "fee": round(fee, 8),
            "fee_usd": round(fee * from_rate, 2),
            "protocol": protocol,
            "route": [from_token.upper(), to_token.upper()],
        }

    def create_demo_data(self, user_id: str) -> List[LiquidityPosition]:
        demo_positions = [
            ("uniswap_v3", "ETH/USDC", 2.0, 5000.0, "ETH", "USDC", 18.5),
            ("aave", "USDC/supply", 0.0, 10000.0, "USDC", "USDC", 5.2),
            ("curve", "3pool", 0.0, 5000.0, "DAI", "USDC", 6.5),
        ]
        created: List[LiquidityPosition] = []
        for protocol, pool, amt0, amt1, token0, token1, apy in demo_positions:
            position = self.provide_liquidity(
                user_id, protocol, pool, amt0, amt1, token0, token1,
            )
            position.apy = apy
            created.append(position)
        return created
