from .accounts import AccountsEngine
from .transfers import TransfersEngine
from .transactions import TransactionsEngine
from .loans import LoansEngine
from .deposits import DepositsEngine
from .credit_cards import CreditCardsEngine
from .bills import BillsEngine

accounts = AccountsEngine()
transfers = TransfersEngine()
transactions = TransactionsEngine()
loans = LoansEngine()
deposits = DepositsEngine()
credit_cards = CreditCardsEngine()
bills = BillsEngine()
