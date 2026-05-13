from .accounts import AccountsEngine
from .bills import BillsEngine
from .credit_cards import CreditCardsEngine
from .deposits import DepositsEngine
from .loans import LoansEngine
from .transactions import TransactionsEngine
from .transfers import TransfersEngine

accounts = AccountsEngine()
transfers = TransfersEngine()
transactions = TransactionsEngine()
loans = LoansEngine()
deposits = DepositsEngine()
credit_cards = CreditCardsEngine()
bills = BillsEngine()
