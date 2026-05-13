from .annuities import AnnuitiesEngine
from .fixed_deposits import FixedDepositsEngine
from .mutual_funds import MutualFundsEngine
from .sip import SIPEngine

mutual_funds = MutualFundsEngine()
fixed_deposits = FixedDepositsEngine()
annuities = AnnuitiesEngine()
sip = SIPEngine()
