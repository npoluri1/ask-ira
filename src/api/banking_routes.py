from fastapi import APIRouter, Body, Query
from src.banking import accounts, transfers, transactions, loans, deposits, credit_cards, bills

router = APIRouter(prefix="/api/v1/banking")

accounts_engine = accounts
transfers_engine = transfers
transactions_engine = transactions
loans_engine = loans
deposits_engine = deposits
credit_cards_engine = credit_cards
bills_engine = bills

def _seed_all_banking_data():
    user_id = "demo"
    accounts_engine.create_demo_data(user_id)
    if hasattr(transfers_engine, 'create_demo_data'):
        transfers_engine.create_demo_data(user_id)
    if hasattr(loans_engine, 'create_demo_data'):
        loans_engine.create_demo_data(user_id)
    if hasattr(deposits_engine, 'create_demo_data'):
        deposits_engine.create_demo_data(user_id)
    if hasattr(credit_cards_engine, 'create_demo_data'):
        credit_cards_engine.create_demo_data(user_id)
    if hasattr(bills_engine, 'create_demo_data'):
        bills_engine.create_demo_data(user_id)

_seed_all_banking_data()


def _resolve_user_id() -> str:
    return "demo"


@router.get("/accounts")
async def list_accounts():
    user_id = _resolve_user_id()
    accounts_engine.create_demo_data(user_id)
    try:
        result = accounts_engine.get_accounts(user_id)
        return {"data": result}
    except Exception as e:
        return {"error": str(e)}


@router.get("/accounts/summary")
async def account_summary():
    user_id = _resolve_user_id()
    try:
        result = accounts_engine.get_account_summary(user_id)
        return {"data": result}
    except Exception as e:
        return {"error": str(e)}


@router.get("/accounts/{account_id}")
async def get_account(account_id: str):
    user_id = _resolve_user_id()
    try:
        result = accounts_engine.get_account(user_id, account_id)
        if not result:
            return {"error": "Account not found"}
        return {"data": result}
    except Exception as e:
        return {"error": str(e)}


@router.post("/accounts")
async def create_account(
    account_type: str = Body(...),
    currency: str = Body("USD"),
    initial_deposit: float = Body(0),
    nickname: str = Body(""),
):
    user_id = _resolve_user_id()
    try:
        result = accounts_engine.create_account(user_id, account_type, currency, initial_deposit, nickname)
        return {"data": result}
    except Exception as e:
        return {"error": str(e)}


@router.post("/accounts/{account_id}/close")
async def close_account(account_id: str):
    user_id = _resolve_user_id()
    try:
        result = accounts_engine.close_account(user_id, account_id)
        return {"data": result}
    except Exception as e:
        return {"error": str(e)}


@router.post("/accounts/{account_id}/interest")
async def apply_interest(account_id: str):
    user_id = _resolve_user_id()
    try:
        result = accounts_engine.apply_interest(user_id, account_id)
        return {"data": result}
    except Exception as e:
        return {"error": str(e)}


@router.get("/transfers")
async def list_transfers():
    user_id = _resolve_user_id()
    try:
        result = transfers_engine.get_transfers(user_id)
        return {"data": result}
    except Exception as e:
        return {"error": str(e)}


@router.post("/transfers")
async def initiate_transfer(
    from_account: str = Body(...),
    to_account: str = Body(...),
    amount: float = Body(...),
    transfer_type: str = Body("internal"),
    description: str = Body(""),
):
    user_id = _resolve_user_id()
    try:
        result = transfers_engine.initiate_transfer(user_id, from_account, to_account, amount, transfer_type, description)
        return {"data": result}
    except Exception as e:
        return {"error": str(e)}


@router.get("/transfers/fees")
async def get_transfer_fees(transfer_type: str = Query(...), amount: float = Query(...)):
    try:
        result = transfers_engine.get_transfer_fees(transfer_type, amount)
        return {"data": result}
    except Exception as e:
        return {"error": str(e)}


@router.post("/transfers/{transfer_id}/cancel")
async def cancel_transfer(transfer_id: str):
    user_id = _resolve_user_id()
    try:
        result = transfers_engine.cancel_scheduled(user_id, transfer_id)
        return {"data": result}
    except Exception as e:
        return {"error": str(e)}


@router.get("/transactions")
async def list_transactions(account_id: str | None = Query(None), limit: int = Query(50), offset: int = Query(0)):
    user_id = _resolve_user_id()
    try:
        result = transactions_engine.get_transactions(user_id, account_id, limit, offset)
        return {"data": result}
    except Exception as e:
        return {"error": str(e)}


@router.get("/transactions/summary")
async def spending_summary(days: int = Query(30)):
    user_id = _resolve_user_id()
    try:
        result = transactions_engine.get_spending_summary(user_id, days)
        return {"data": result}
    except Exception as e:
        return {"error": str(e)}


@router.get("/loans/products")
async def list_loan_products():
    try:
        result = loans_engine.get_loan_products()
        return {"data": result}
    except Exception as e:
        return {"error": str(e)}


@router.get("/loans/products/{loan_type}")
async def get_loan_product(loan_type: str):
    try:
        result = loans_engine.get_loan_details(loan_type)
        if not result:
            return {"error": "Loan type not found"}
        return {"data": result}
    except Exception as e:
        return {"error": str(e)}


@router.post("/loans/calculate")
async def calculate_emi(loan_type: str = Body(...), amount: float = Body(...), term_months: int = Body(...)):
    try:
        product = loans_engine.get_loan_details(loan_type)
        if not product:
            return {"error": f"Invalid loan type: {loan_type}"}
        rate = product["base_rate"]
        result = loans_engine.calculate_emi(amount, rate, term_months)
        return {"data": result}
    except Exception as e:
        return {"error": str(e)}


@router.get("/loans")
async def list_loans():
    user_id = _resolve_user_id()
    try:
        result = loans_engine.get_loans(user_id)
        return {"data": result}
    except Exception as e:
        return {"error": str(e)}


@router.post("/loans/apply")
async def apply_loan(loan_type: str = Body(...), amount: float = Body(...), term_months: int = Body(...)):
    user_id = _resolve_user_id()
    try:
        result = loans_engine.apply_loan(user_id, loan_type, amount, term_months)
        return {"data": result}
    except Exception as e:
        return {"error": str(e)}


@router.get("/loans/summary")
async def loan_summary():
    user_id = _resolve_user_id()
    try:
        result = loans_engine.get_loan_summary(user_id)
        return {"data": result}
    except Exception as e:
        return {"error": str(e)}


@router.post("/loans/{loan_id}/pay")
async def pay_loan(loan_id: str):
    user_id = _resolve_user_id()
    try:
        result = loans_engine.make_payment(user_id, loan_id)
        return {"data": result}
    except Exception as e:
        return {"error": str(e)}


@router.get("/deposits/products")
async def list_deposit_products():
    try:
        result = deposits_engine.get_products()
        return {"data": result}
    except Exception as e:
        return {"error": str(e)}


@router.post("/deposits/open")
async def open_deposit(product_id: str = Body(...), amount: float = Body(...), auto_renew: bool = Body(True)):
    user_id = _resolve_user_id()
    try:
        result = deposits_engine.open_deposit(user_id, product_id, amount, auto_renew=auto_renew)
        return {"data": result}
    except Exception as e:
        return {"error": str(e)}


@router.get("/deposits")
async def list_deposits():
    user_id = _resolve_user_id()
    try:
        result = deposits_engine.get_deposits(user_id)
        return {"data": result}
    except Exception as e:
        return {"error": str(e)}


@router.get("/deposits/{deposit_id}/maturity")
async def get_maturity_value(deposit_id: str):
    user_id = _resolve_user_id()
    try:
        result = deposits_engine.get_matured_value(deposit_id, user_id)
        return {"data": result}
    except Exception as e:
        return {"error": str(e)}


@router.post("/deposits/{deposit_id}/close")
async def close_deposit(deposit_id: str):
    user_id = _resolve_user_id()
    try:
        result = deposits_engine.close_deposit(user_id, deposit_id)
        return {"data": result}
    except Exception as e:
        return {"error": str(e)}


@router.get("/cards/products")
async def list_card_products():
    try:
        result = credit_cards_engine.get_products()
        return {"data": result}
    except Exception as e:
        return {"error": str(e)}


@router.post("/cards/apply")
async def apply_card(product_id: str = Body(...), income: float = Body(50000)):
    user_id = _resolve_user_id()
    try:
        result = credit_cards_engine.apply_card(user_id, product_id, income)
        return {"data": result}
    except Exception as e:
        return {"error": str(e)}


@router.get("/cards")
async def list_cards():
    user_id = _resolve_user_id()
    try:
        result = credit_cards_engine.get_cards(user_id)
        return {"data": result}
    except Exception as e:
        return {"error": str(e)}


@router.post("/cards/{card_id}/purchase")
async def make_purchase(card_id: str, amount: float = Body(...), merchant: str = Body(...), category: str = Body("")):
    user_id = _resolve_user_id()
    try:
        result = credit_cards_engine.make_purchase(user_id, card_id, amount, merchant, category)
        return {"data": result}
    except Exception as e:
        return {"error": str(e)}


@router.post("/cards/{card_id}/payment")
async def make_card_payment(card_id: str, amount: float = Body(...)):
    user_id = _resolve_user_id()
    try:
        result = credit_cards_engine.make_payment(user_id, card_id, amount)
        return {"data": result}
    except Exception as e:
        return {"error": str(e)}


@router.post("/cards/{card_id}/statement")
async def generate_statement(card_id: str):
    user_id = _resolve_user_id()
    try:
        result = credit_cards_engine.generate_statement(user_id, card_id)
        return {"data": result}
    except Exception as e:
        return {"error": str(e)}


@router.get("/bills/templates")
async def get_bill_templates():
    try:
        result = bills_engine.get_bill_templates()
        return {"data": result}
    except Exception as e:
        return {"error": str(e)}


@router.post("/bills")
async def add_bill(
    biller_name: str = Body(...),
    category: str = Body(...),
    amount: float = Body(...),
    due_day: int = Body(...),
    autopay: bool = Body(False),
):
    user_id = _resolve_user_id()
    try:
        result = bills_engine.add_bill(user_id, biller_name, category, amount, due_day, autopay=autopay)
        return {"data": result}
    except Exception as e:
        return {"error": str(e)}


@router.get("/bills")
async def list_bills():
    user_id = _resolve_user_id()
    try:
        result = bills_engine.get_bills(user_id)
        return {"data": result}
    except Exception as e:
        return {"error": str(e)}


@router.get("/bills/upcoming")
async def upcoming_bills(days: int = Query(30)):
    user_id = _resolve_user_id()
    try:
        result = bills_engine.get_upcoming_bills(user_id, days)
        return {"data": result}
    except Exception as e:
        return {"error": str(e)}


@router.get("/bills/summary")
async def bill_summary():
    user_id = _resolve_user_id()
    try:
        result = bills_engine.get_monthly_bill_summary(user_id)
        return {"data": result}
    except Exception as e:
        return {"error": str(e)}


@router.post("/bills/{bill_id}/pay")
async def pay_bill(bill_id: str):
    user_id = _resolve_user_id()
    try:
        result = bills_engine.pay_bill(user_id, bill_id)
        return {"data": result}
    except Exception as e:
        return {"error": str(e)}


def init_demo_banking_data(user_id: str = "demo"):
    accounts_engine.create_demo_data(user_id)
    transfers_engine.create_demo_data(user_id)
    account_ids = [a["account_id"] for a in accounts_engine.get_accounts(user_id)]
    if account_ids:
        transactions_engine.create_demo_data(user_id, account_ids)
    loans_engine.create_demo_data(user_id)
    deposits_engine.create_demo_data(user_id)
    credit_cards_engine.create_demo_data(user_id)
    bills_engine.create_demo_data(user_id)
