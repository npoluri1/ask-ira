from .compliance import CryptoComplianceEngine
from .defi import DeFiEngine
from .staking import StakingEngine
from .transactions import CryptoTransactionsEngine
from .wallets import CryptoWalletEngine

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
