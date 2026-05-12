from .wallets import CryptoWalletEngine
from .transactions import CryptoTransactionsEngine
from .staking import StakingEngine
from .defi import DeFiEngine
from .compliance import CryptoComplianceEngine

wallets = CryptoWalletEngine()
transactions = CryptoTransactionsEngine()
staking = StakingEngine()
defi = DeFiEngine()
compliance = CryptoComplianceEngine()

__all__ = [
    "CryptoWalletEngine",
    "CryptoTransactionsEngine",
    "StakingEngine",
    "DeFiEngine",
    "CryptoComplianceEngine",
    "wallets",
    "transactions",
    "staking",
    "defi",
    "compliance",
]
