from datetime import datetime
from typing import Optional

from log_service.models import RequestData

import config


def get_insurer_msp(input_data: Optional[RequestData] = None) -> str:
    """Получение СК MSP в зависимости от условий распределения

    :param input_data: входящий запрос

    :return: СК MSP
    """
    try:
        if isinstance(input_data.date, str):
            cur_date = datetime.strptime(input_data.date, "%Y-%m-%d")
        else:
            cur_date = input_data.date or datetime.now()
    except:
        cur_date = datetime.now()

    if cur_date >= datetime.strptime(
        config.insurer_dates["SberbankInsMSP"]["start"], "%Y-%m-%d"
    ):
        return input_data.insuranceCompanyMSP
    elif cur_date >= datetime.strptime(
        config.insurer_dates["AlfastrahMSP"]["start"], "%Y-%m-%d"
    ):
        return "AlfastrahMSP"
    else:
        return "RenaissanceMSP"
