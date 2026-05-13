from .aml import AMLEngine
from .kyc import KYCEngine
from .reporting import ReportingEngine
from .sanctions import SanctionsEngine

aml = AMLEngine()
sanctions = SanctionsEngine()
kyc = KYCEngine()
reporting = ReportingEngine()
