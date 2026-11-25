import os

from calc_utils.models import Currency, InsuranceType
from dotenv import load_dotenv

load_dotenv()

## Server settings
DEBUG = int(os.getenv("DEBUG", "0"))
USE_RELOADER = int(os.getenv("USE_RELOADER", "0"))
PROCESSES = int(os.getenv("PROCESSES", "10"))

transport_msp = "GruzovichkofAvtoflotMSP"
insurer_msp = {
    InsuranceType.cargo: [
        "AlfastrahMSP",
        "RenaissanceMSP",
        "SberbankInsMSP",
        "SogazMSP",
    ],
}
insurer_dates = {
    "RenaissanceMSP": {"start": "2023-06-15", "end": None},
    "AlfastrahMSP": {"start": "2023-09-01", "end": None},
    "SberbankInsMSP": {"start": "2024-10-01", "end": None},
    "SogazMSP": {"start": "2024-11-18", "end": None},
}

use_auth = int(os.getenv("USE_AUTH", "0"))
currency_codes = [Currency.RUB]
