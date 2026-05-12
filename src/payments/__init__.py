from .engine import PaymentsEngine
from .swift import SWIFTEngine
from .sepa import SEPAEngine
from .ach import AHEngine
from .faster_payments import FasterPaymentsEngine
from .rails import PaymentRailsAgent

engine = PaymentsEngine()
swift = SWIFTEngine()
sepa = SEPAEngine()
ach = AHEngine()
faster = FasterPaymentsEngine()
rails = PaymentRailsAgent()
