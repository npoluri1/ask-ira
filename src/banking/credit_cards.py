import time
import uuid

CARD_PRODUCTS = {
    "cashback": {
        "name": "Cashback Rewards Card",
        "annual_fee": 0,
        "apr": 0.2499,
        "credit_limit_min": 1000,
        "credit_limit_max": 25000,
        "rewards": {"base": 0.01, "categories": {"groceries": 0.03, "gas": 0.03, "dining": 0.02}},
        "features": ["No Annual Fee", "Cashback Rewards", "Contactless", "Chip Technology", "Mobile Wallet"],
    },
    "travel": {
        "name": "Travel Rewards Card",
        "annual_fee": 95,
        "apr": 0.2699,
        "credit_limit_min": 5000,
        "credit_limit_max": 50000,
        "rewards": {"base": 0.01, "categories": {"travel": 0.03, "dining": 0.02, "hotels": 0.05}},
        "features": ["Travel Insurance", "Airport Lounge Access", "No Foreign Fees", "Travel Credits", "Concierge Service"],
    },
    "premium": {
        "name": "Premium Rewards Card",
        "annual_fee": 550,
        "apr": 0.2299,
        "credit_limit_min": 10000,
        "credit_limit_max": 100000,
        "rewards": {"base": 0.02, "categories": {"travel": 0.05, "dining": 0.04, "entertainment": 0.03}},
        "features": ["Premium Insurance", "Global Lounge Access", "$300 Travel Credit", "Priority Boarding", "Hotel Status", "Concierge"],
    },
    "student": {
        "name": "Student Card",
        "annual_fee": 0,
        "apr": 0.2799,
        "credit_limit_min": 500,
        "credit_limit_max": 5000,
        "rewards": {"base": 0.01, "categories": {"food": 0.02, "transport": 0.02}},
        "features": ["No Annual Fee", "Credit Building", "Student Resources", "No Minimum Income"],
    },
    "secured": {
        "name": "Secured Card",
        "annual_fee": 0,
        "apr": 0.2899,
        "credit_limit_min": 200,
        "credit_limit_max": 2000,
        "security_deposit_required": True,
        "rewards": {"base": 0.0, "categories": {}},
        "features": ["Build Credit", "Refundable Deposit", "Credit Reporting", "Path to Unsecured"],
    },
}

CARDS_DB: dict[str, list[dict]] = {}


class CreditCardsEngine:
    def get_products(self) -> dict:
        return CARD_PRODUCTS

    def apply_card(self, user_id: str, product_id: str, income: float = 50000) -> dict:
        product = CARD_PRODUCTS.get(product_id)
        if not product:
            raise ValueError(f"Invalid card product: {product_id}")

        credit_limit = self._calculate_credit_limit(product, income)
        card = {
            "card_id": f"CRD{uuid.uuid4().hex[:12].upper()}",
            "user_id": user_id,
            "product_id": product_id,
            "product_name": product["name"],
            "credit_limit": credit_limit,
            "available_credit": credit_limit,
            "current_balance": 0,
            "apr": product["apr"],
            "annual_fee": product["annual_fee"],
            "rewards_earned": 0.0,
            "rewards_rate": product["rewards"]["base"],
            "status": "active",
            "issued_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "features": product["features"],
            "last_statement_date": None,
            "minimum_payment_due": 0,
            "due_date": None,
        }

        if user_id not in CARDS_DB:
            CARDS_DB[user_id] = []
        CARDS_DB[user_id].append(card)
        return card

    def get_cards(self, user_id: str) -> list[dict]:
        return CARDS_DB.get(user_id, [])

    def make_purchase(self, user_id: str, card_id: str, amount: float, merchant: str, category: str = "") -> dict:
        for card in CARDS_DB.get(user_id, []):
            if card["card_id"] == card_id:
                if card["available_credit"] < amount:
                    raise ValueError(f"Insufficient credit. Available: ${card['available_credit']:.2f}")
                card["current_balance"] = round(card["current_balance"] + amount, 2)
                card["available_credit"] = round(card["available_credit"] - amount, 2)

                rewards_earned = amount * card["rewards_rate"]
                card["rewards_earned"] = round(card["rewards_earned"] + rewards_earned, 2)

                return {
                    "card_id": card_id,
                    "amount": round(amount, 2),
                    "merchant": merchant,
                    "category": category,
                    "rewards_earned": round(rewards_earned, 2),
                    "available_credit": card["available_credit"],
                    "new_balance": card["current_balance"],
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                }
        raise ValueError("Card not found")

    def make_payment(self, user_id: str, card_id: str, amount: float) -> dict:
        for card in CARDS_DB.get(user_id, []):
            if card["card_id"] == card_id:
                if amount > card["current_balance"]:
                    amount = card["current_balance"]
                card["current_balance"] = round(card["current_balance"] - amount, 2)
                card["available_credit"] = round(card["available_credit"] + amount, 2)
                return {
                    "card_id": card_id,
                    "payment": round(amount, 2),
                    "new_balance": card["current_balance"],
                    "available_credit": card["available_credit"],
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                }
        raise ValueError("Card not found")

    def generate_statement(self, user_id: str, card_id: str) -> dict:
        for card in CARDS_DB.get(user_id, []):
            if card["card_id"] == card_id:
                min_payment = max(25, card["current_balance"] * 0.03)
                statement = {
                    "card_id": card_id,
                    "statement_date": time.strftime("%Y-%m-%d", time.gmtime()),
                    "due_date": time.strftime("%Y-%m-%d", time.gmtime(time.time() + 21 * 86400)),
                    "previous_balance": max(0, card["current_balance"] - 500),
                    "charges": 500,
                    "payments": 0,
                    "current_balance": card["current_balance"],
                    "minimum_payment": round(min_payment, 2),
                    "credit_limit": card["credit_limit"],
                    "available_credit": card["available_credit"],
                    "apr": card["apr"],
                    "rewards_earned_ytd": card["rewards_earned"],
                }
                card["last_statement_date"] = statement["statement_date"]
                card["minimum_payment_due"] = statement["minimum_payment"]
                card["due_date"] = statement["due_date"]
                return statement
        raise ValueError("Card not found")

    def create_demo_data(self, user_id: str, income: float = 75000):
        self.apply_card(user_id, "cashback", income)
        self.apply_card(user_id, "travel", income)

    def _calculate_credit_limit(self, product: dict, income: float) -> int:
        min_limit = product.get("credit_limit_min", 1000)
        max_limit = product.get("credit_limit_max", 25000)
        income_based = int(income * 0.3)
        return max(min_limit, min(max_limit, income_based))
