from .ach import AHEngine
from .engine import PaymentsEngine
from .faster_payments import FasterPaymentsEngine
from .rails import PaymentRailsAgent
from .sepa import SEPAEngine
from .swift import SWIFTEngine

engine = PaymentsEngine()
swift = SWIFTEngine()
sepa = SEPAEngine()
ach = AHEngine()
faster = FasterPaymentsEngine()
rails = PaymentRailsAgent()
