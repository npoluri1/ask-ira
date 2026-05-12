from __future__ import annotations

import copy
from typing import Any, Optional

from src.config.logging import get_logger

logger = get_logger(__name__)

RAIL_DEFINITIONS: dict[str, dict[str, Any]] = {
    "internal": {
        "name": "Internal Transfer",
        "currencies": ["USD", "EUR", "GBP", "JPY", "AED", "SAR", "INR", "SGD", "CHF", "CAD", "AUD", "CNY", "HKD", "KRW", "BRL"],
        "same_currency_only": True,
        "fee": 0.0,
        "fee_description": "Free",
        "estimated_time": "Instant",
        "estimated_time_seconds": 0,
        "max_amount": None,
        "supports_urgency": ["instant"],
    },
    "faster_payments": {
        "name": "Faster Payments (UK)",
        "currencies": ["GBP"],
        "same_currency_only": True,
        "fee": 1.0,
        "fee_description": "£1.00",
        "estimated_time": "Instant (<2 minutes)",
        "estimated_time_seconds": 120,
        "max_amount": 1_000_000.0,
        "supports_urgency": ["instant", "fast"],
    },
    "sepa_credit": {
        "name": "SEPA Credit Transfer",
        "currencies": ["EUR"],
        "same_currency_only": True,
        "fee": 1.0,
        "fee_description": "€1.00",
        "estimated_time": "1 business day",
        "estimated_time_seconds": 86400,
        "max_amount": None,
        "supports_urgency": ["standard"],
    },
    "ach": {
        "name": "ACH (US)",
        "currencies": ["USD"],
        "same_currency_only": True,
        "fee": 0.50,
        "fee_description": "$0.50",
        "estimated_time": "1-2 business days",
        "estimated_time_seconds": 172800,
        "max_amount": None,
        "supports_urgency": ["standard", "economy"],
    },
    "swift": {
        "name": "SWIFT",
        "currencies": ["USD", "EUR", "GBP", "JPY", "AED", "SAR", "INR", "SGD", "CHF", "CAD", "AUD", "CNY", "HKD", "KRW", "BRL"],
        "same_currency_only": False,
        "fee": 25.0,
        "fee_description": "$25.00 + intermediary fees",
        "estimated_time": "2-5 business days",
        "estimated_time_seconds": 432000,
        "max_amount": None,
        "supports_urgency": ["standard", "economy"],
    },
    "rtp": {
        "name": "RTP (US Real-Time Payments)",
        "currencies": ["USD"],
        "same_currency_only": True,
        "fee": 0.10,
        "fee_description": "$0.10",
        "estimated_time": "Instant",
        "estimated_time_seconds": 0,
        "max_amount": 100_000.0,
        "supports_urgency": ["instant", "fast"],
    },
    "crypto": {
        "name": "Cryptocurrency",
        "currencies": ["USD", "EUR", "GBP", "JPY", "AED", "SAR", "INR", "SGD", "CHF", "CAD", "AUD", "CNY", "HKD", "KRW", "BRL"],
        "same_currency_only": False,
        "fee": 0.0,
        "fee_description": "Varies (network fees)",
        "estimated_time": "10-60 minutes",
        "estimated_time_seconds": 3600,
        "max_amount": None,
        "supports_urgency": ["instant", "fast"],
    },
    "upi": {
        "name": "UPI (India)",
        "currencies": ["INR"],
        "same_currency_only": True,
        "fee": 0.0,
        "fee_description": "Free",
        "estimated_time": "Instant",
        "estimated_time_seconds": 0,
        "max_amount": 1_000_000.0,
        "supports_urgency": ["instant", "fast"],
    },
    "pix": {
        "name": "PIX (Brazil)",
        "currencies": ["BRL"],
        "same_currency_only": True,
        "fee": 0.0,
        "fee_description": "Free",
        "estimated_time": "Instant",
        "estimated_time_seconds": 0,
        "max_amount": None,
        "supports_urgency": ["instant", "fast"],
    },
}

URGENCY_ORDER: dict[str, int] = {
    "instant": 0,
    "fast": 1,
    "standard": 2,
    "economy": 3,
}

FX_RATES: dict[str, dict[str, float]] = {
    "USD": {"EUR": 0.92, "GBP": 0.79, "JPY": 149.50, "AED": 3.67, "SAR": 3.75, "INR": 83.20, "SGD": 1.35, "CHF": 0.88, "CAD": 1.36, "AUD": 1.54, "CNY": 7.24, "HKD": 7.82, "KRW": 1320.00, "BRL": 4.97},
    "EUR": {"USD": 1.09, "GBP": 0.86, "JPY": 162.50, "AED": 4.00, "SAR": 4.08, "INR": 90.50, "SGD": 1.47, "CHF": 0.96, "CAD": 1.48, "AUD": 1.68, "CNY": 7.87, "HKD": 8.51, "KRW": 1436.00, "BRL": 5.41},
    "GBP": {"USD": 1.27, "EUR": 1.16, "JPY": 189.00, "AED": 4.66, "SAR": 4.76, "INR": 105.30, "SGD": 1.71, "CHF": 1.12, "CAD": 1.72, "AUD": 1.95, "CNY": 9.15, "HKD": 9.89, "KRW": 1670.00, "BRL": 6.29},
    "JPY": {"USD": 0.0067, "EUR": 0.0062, "GBP": 0.0053, "AED": 0.0246, "SAR": 0.0251, "INR": 0.557, "SGD": 0.0090, "CHF": 0.0059, "CAD": 0.0091, "AUD": 0.0103, "CNY": 0.0485, "HKD": 0.0524, "KRW": 8.83, "BRL": 0.0333},
    "AED": {"USD": 0.272, "EUR": 0.250, "GBP": 0.215, "JPY": 40.70, "SAR": 1.02, "INR": 22.66, "SGD": 0.368, "CHF": 0.240, "CAD": 0.370, "AUD": 0.420, "CNY": 1.97, "HKD": 2.13, "KRW": 359.5, "BRL": 1.35},
    "SAR": {"USD": 0.267, "EUR": 0.245, "GBP": 0.210, "JPY": 39.90, "AED": 0.980, "INR": 22.21, "SGD": 0.361, "CHF": 0.235, "CAD": 0.363, "AUD": 0.412, "CNY": 1.93, "HKD": 2.09, "KRW": 352.5, "BRL": 1.33},
    "INR": {"USD": 0.012, "EUR": 0.011, "GBP": 0.0095, "JPY": 1.80, "AED": 0.044, "SAR": 0.045, "SGD": 0.0162, "CHF": 0.0106, "CAD": 0.0163, "AUD": 0.0185, "CNY": 0.087, "HKD": 0.094, "KRW": 15.87, "BRL": 0.0598},
    "SGD": {"USD": 0.74, "EUR": 0.68, "GBP": 0.58, "JPY": 110.8, "AED": 2.72, "SAR": 2.77, "INR": 61.7, "CHF": 0.652, "CAD": 1.01, "AUD": 1.14, "CNY": 5.36, "HKD": 5.79, "KRW": 977.5, "BRL": 3.68},
    "CHF": {"USD": 1.14, "EUR": 1.04, "GBP": 0.89, "JPY": 170.0, "AED": 4.17, "SAR": 4.26, "INR": 94.6, "SGD": 1.53, "CAD": 1.55, "AUD": 1.75, "CNY": 8.23, "HKD": 8.89, "KRW": 1500.0, "BRL": 5.65},
    "CAD": {"USD": 0.74, "EUR": 0.68, "GBP": 0.58, "JPY": 109.9, "AED": 2.70, "SAR": 2.76, "INR": 61.3, "SGD": 0.995, "CHF": 0.646, "AUD": 1.13, "CNY": 5.33, "HKD": 5.76, "KRW": 972.5, "BRL": 3.66},
    "AUD": {"USD": 0.65, "EUR": 0.60, "GBP": 0.51, "JPY": 97.2, "AED": 2.38, "SAR": 2.43, "INR": 54.0, "SGD": 0.877, "CHF": 0.571, "CAD": 0.883, "CNY": 4.71, "HKD": 5.09, "KRW": 859.5, "BRL": 3.24},
    "CNY": {"USD": 0.14, "EUR": 0.13, "GBP": 0.11, "JPY": 20.63, "AED": 0.507, "SAR": 0.518, "INR": 11.49, "SGD": 0.187, "CHF": 0.122, "CAD": 0.188, "AUD": 0.212, "HKD": 1.08, "KRW": 182.5, "BRL": 0.688},
    "HKD": {"USD": 0.128, "EUR": 0.118, "GBP": 0.101, "JPY": 19.10, "AED": 0.469, "SAR": 0.479, "INR": 10.64, "SGD": 0.173, "CHF": 0.112, "CAD": 0.174, "AUD": 0.196, "CNY": 0.926, "KRW": 169.0, "BRL": 0.637},
    "KRW": {"USD": 0.000758, "EUR": 0.000696, "GBP": 0.000599, "JPY": 0.113, "AED": 0.00278, "SAR": 0.00284, "INR": 0.063, "SGD": 0.00102, "CHF": 0.000667, "CAD": 0.00103, "AUD": 0.00116, "CNY": 0.00548, "HKD": 0.00592, "BRL": 0.00377},
    "BRL": {"USD": 0.20, "EUR": 0.18, "GBP": 0.16, "JPY": 30.0, "AED": 0.739, "SAR": 0.754, "INR": 16.73, "SGD": 0.272, "CHF": 0.177, "CAD": 0.273, "AUD": 0.309, "CNY": 1.45, "HKD": 1.57, "KRW": 265.0},
}


def _convert_currency(
    amount: float,
    from_currency: str,
    to_currency: str,
) -> float:
    if from_currency.upper() == to_currency.upper():
        return amount
    rate_map = FX_RATES.get(from_currency.upper())
    if rate_map is None:
        raise ValueError(f"No FX rate available for {from_currency}")
    rate = rate_map.get(to_currency.upper())
    if rate is None:
        raise ValueError(f"No FX rate for {from_currency} -> {to_currency}")
    return round(amount * rate, 2)


class PaymentRailsAgent:
    def select_best_rail(
        self,
        source_currency: str,
        target_currency: str,
        amount: float,
        urgency: str = "standard",
    ) -> dict[str, Any]:
        if urgency not in URGENCY_ORDER:
            raise ValueError(f"Unsupported urgency: {urgency}")
        max_urgency_priority = URGENCY_ORDER[urgency]

        candidates: list[dict[str, Any]] = []
        for rail_key, rail in RAIL_DEFINITIONS.items():
            if source_currency.upper() not in rail["currencies"]:
                continue
            if target_currency.upper() not in rail["currencies"]:
                continue
            if rail["same_currency_only"] and source_currency.upper() != target_currency.upper():
                continue
            if rail["max_amount"] is not None and amount > rail["max_amount"]:
                continue

            rail_urgency_priority = min(
                URGENCY_ORDER.get(u, 99) for u in rail["supports_urgency"]
            )
            if rail_urgency_priority > max_urgency_priority:
                continue

            total_cost = rail["fee"]
            if source_currency.upper() != target_currency.upper():
                fx_cost = round(amount * 0.005, 2)
                total_cost += fx_cost
            else:
                fx_cost = 0.0

            candidates.append({
                "rail": rail_key,
                "name": rail["name"],
                "estimated_time": rail["estimated_time"],
                "fee": rail["fee"],
                "fx_cost": fx_cost,
                "total_cost": total_cost,
                "urgency_match": urgency == rail["supports_urgency"][0],
            })

        if not candidates:
            return {
                "rail": None,
                "estimated_time": "N/A",
                "fees": {"total": 0},
                "total_cost": 0,
                "reasoning": f"No available rail for {source_currency} -> {target_currency} with urgency '{urgency}'",
            }

        candidates.sort(key=lambda c: (c["total_cost"], c["fx_cost"]))
        best = candidates[0]

        reasoning = (
            f"{best['name']} selected: fastest rail meeting urgency '{urgency}' "
            f"with lowest total cost of {best['total_cost']} "
            f"({best['fee']} fee + {best['fx_cost']} FX cost). "
            f"Estimated time: {best['estimated_time']}."
        )

        return {
            "rail": best["rail"],
            "estimated_time": best["estimated_time"],
            "fees": {
                "processing_fee": best["fee"],
                "fx_cost": best["fx_cost"],
                "total": best["total_cost"],
            },
            "total_cost": best["total_cost"],
            "reasoning": reasoning,
        }

    def calculate_optimized_route(
        self,
        source_currency: str,
        target_currency: str,
        amount: float,
    ) -> dict[str, Any]:
        direct = self.select_best_rail(source_currency, target_currency, amount, "economy")

        converted_amount = _convert_currency(amount, source_currency, target_currency)
        internal = RAIL_DEFINITIONS.get("internal", {})
        same_currency = source_currency.upper() == target_currency.upper()

        routes: list[dict[str, Any]] = []
        routes.append({
            "route": "direct",
            "rail": direct["rail"],
            "source_currency": source_currency.upper(),
            "target_currency": target_currency.upper(),
            "source_amount": amount,
            "target_amount": converted_amount if not same_currency else amount,
            "total_fees": direct["total_cost"],
            "estimated_time": direct["estimated_time"],
        })

        if same_currency and internal:
            routes.append({
                "route": "internal",
                "rail": "internal",
                "source_currency": source_currency.upper(),
                "target_currency": target_currency.upper(),
                "source_amount": amount,
                "target_amount": amount,
                "total_fees": 0.0,
                "estimated_time": "Instant",
            })

        routes.sort(key=lambda r: (r["total_fees"], r["estimated_time"]))
        best = routes[0]

        return {
            "source_currency": source_currency.upper(),
            "target_currency": target_currency.upper(),
            "amount": amount,
            "routes": routes,
            "recommended_route": best["route"],
            "recommended_rail": best["rail"],
            "total_fees": best["total_fees"],
            "estimated_time": best["estimated_time"],
        }

    def get_all_rails(self) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        for rail_key, rail in RAIL_DEFINITIONS.items():
            entry = copy.deepcopy(rail)
            entry["key"] = rail_key
            result.append(entry)
        return result

    def estimate_all_rails(
        self,
        source_currency: str,
        target_currency: str,
        amount: float,
    ) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        for rail_key, rail in RAIL_DEFINITIONS.items():
            if source_currency.upper() not in rail["currencies"]:
                continue
            if target_currency.upper() not in rail["currencies"]:
                continue
            if rail["same_currency_only"] and source_currency.upper() != target_currency.upper():
                continue
            if rail["max_amount"] is not None and amount > rail["max_amount"]:
                continue

            fee = rail["fee"]
            fx_cost = 0.0
            if source_currency.upper() != target_currency.upper():
                fx_cost = round(amount * 0.005, 2)

            results.append({
                "rail": rail_key,
                "name": rail["name"],
                "available": True,
                "processing_fee": fee,
                "fx_cost": fx_cost,
                "total_cost": round(fee + fx_cost, 2),
                "estimated_time": rail["estimated_time"],
                "currency_pair": f"{source_currency.upper()} -> {target_currency.upper()}",
            })

        results.sort(key=lambda r: (r["total_cost"], r["estimated_time"]))
        return results
