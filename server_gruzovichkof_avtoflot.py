# -*- coding: utf-8 -*-

import datetime
import os
import sys
from typing import Optional

from calc_api.models import CalculatorConfig
from calc_api.server import ApiTemplate
from calc_utils import errors
from calc_utils.models import InsuranceType
from dotenv import load_dotenv
from log_service.models import RequestData, CalcOutput
from tariff_loader.loader import TariffLoader
from tariff_loader.models import TariffLoaderSettings, Tariff

import calculation as calc
import config as conf
from distribution import get_insurer_msp
from custom_tariff_loader import CustomTariffLoader

load_dotenv()

PORT = sys.argv[1]
tariff_loader = CustomTariffLoader(
    TariffLoaderSettings(
        transport_msp=conf.transport_msp,
    ),
    conf.insurer_msp,
)


def check_fields(context: RequestData, insurance_type: InsuranceType) -> Optional[str]:
    """Проверка входных данных на корректность полей, необходимых для расчета
    страховой премии.

        :param context: входные данные
        :param insurance_type: тип страхования

        :return: строка ошибки, None - если ошибок нет
    """

    if context.insuranceCompanyMSP == "SogazMSP":
        if not context.declaredValue:
            return errors.messages["missRequiredField"] % "declaredValue"

    if insurance_type == InsuranceType.cargo:
        if not context.item.extraData.get("section"):
            return errors.messages["missRequiredField"] % "insurance.extraData.section"

        if not context.insuranceCompanyMSP and context.date >= datetime.datetime(
            2024, 10, 1
        ):
            return errors.messages["missRequiredField"] % "insuranceCompanyMSP"

        try:
            context.item.extraData["section"] = int(context.item.extraData["section"])
            if context.item.extraData["section"] > 2:
                return (
                    errors.messages["invalidRequiredField"]
                    % "insurance.extraData.section"
                )
        except Exception as err:
            return (
                errors.messages["invalidRequiredField"] % "insurance.extraData.section"
            )

        if context.declaredValue:
            try:
                context.declaredValue = float(context.declaredValue)
            except Exception as err:
                return errors.messages["invalidDeclaredValue"]

            if context.declaredValue < 0:
                return errors.messages["invalidDeclaredValue"]

        else:
            if not context.item.extraData.get("inputInsurancePrice"):
                return (
                    errors.messages["missRequiredField"]
                    % "insurance.extraData.inputInsurancePrice"
                )

            try:
                context.item.extraData["inputInsurancePrice"] = int(
                    context.item.extraData["inputInsurancePrice"]
                )
                if context.item.extraData["inputInsurancePrice"] < 0:
                    raise ValueError("negative input insurance price")
            except:
                return (
                    errors.messages["invalidRequiredField"]
                    % "insurance.extraData.inputInsurancePrice"
                )
    return


def calculator(
    input_data: RequestData, cur_tariff: Tariff, insurance_type: InsuranceType
) -> CalcOutput:
    """Расчет СП в зависимости от типа страхования

    :param input_data: входные данные
    :param cur_tariff: тариф для расчета
    :param insurance_type: тип страхования: по умолчанию грузы

    :return: рассчитанная СП
    """
    ## Шаблон ответа
    output_struct = CalcOutput(**{"insuranceType": insurance_type})

    if input_data.price:
        output_struct.insurancePrice = input_data.price
        output_struct._exists = 1
        return output_struct

    if insurance_type not in conf.insurer_msp.keys():
        output_struct.error = errors.messages["incorrectInsuranceType"]
        return output_struct

    if insurance_type == InsuranceType.cargo:
        if input_data.insuranceCompanyMSP == "SogazMSP":
            if (
                datetime.datetime.strptime(cur_tariff.actualStartDate, "%Y-%m-%d")
                <= input_data.date
            ):
                if calc.get_insurance_premium_sogaz(
                    input_data, cur_tariff, output_struct
                ):
                    calc.set_insurance_sum_and_section_sogaz(
                        input_data, cur_tariff, output_struct
                    )
                return output_struct

        if calc.get_price_by_section(input_data, cur_tariff, output_struct):
            calc.set_insurance_sum_and_section(
                input_data,
                cur_tariff,
                output_struct,
            )

    return output_struct


#################################### API #######################################
calc_config = CalculatorConfig(
    transport_msp=conf.transport_msp,
    insurer_msp=conf.insurer_msp,
    process=os.path.basename(__file__),
)
api = ApiTemplate(
    calc_config,
    check_fields=check_fields,
    calculator=calculator,
    get_insurer_msp=get_insurer_msp,
    tariff_loader=tariff_loader,
)
app = api.get_app()


@api.auth(tech=True)
def calc_config():
    """Получение конфигурации калькулятора"""
    info_by_insurer = {}
    for ins_type, insurers in conf.insurer_msp.items():
        for insurer in insurers:
            tariffs = tariff_loader.general_tariffs.get(ins_type, {}).get(insurer)
            if not tariffs:
                continue

            dates = [
                {"actualStartDate": date, "insurance_type": ins_type}
                for date in tariffs.keys()
            ]

            if info_by_insurer.get(insurer):
                cur_info = info_by_insurer[insurer]
                if len(dates):
                    cur_info["insurance_type"].append(ins_type)
                    cur_info["tariffs"].extend(dates)
            else:
                cur_info = {
                    "insurer_msp": insurer,
                    "insurance_type": [ins_type],
                    "currency_codes": conf.currency_codes,
                    "tariffs": dates,
                    "special_tariffs": [],
                }
                info_by_insurer[insurer] = cur_info

    response = {
        "transport_msp": conf.transport_msp,
        "insurer_info": list(info_by_insurer.values()),
        "endpoints": {
            "v1": {
                "single": "/api/v1/calc_price_all",
                "bulk": "/api/v1/calc_price_bulk_all",
            }
        },
        "distribution": False,
        "use_auth": bool(conf.use_auth),
    }
    return response


## Запуск сервера
"""Получение конфигурации калькулятора"""
app.add_url_rule("/api/v1/calc_config", "config", calc_config)


if __name__ == "__main__":
    import sys as _sys
    api.log_service.log_start(PORT)
    _processes = 1 if _sys.platform == "win32" else conf.PROCESSES
    app.run(
        host="0.0.0.0",
        port=int(PORT),
        debug=bool(conf.DEBUG),
        use_reloader=bool(conf.USE_RELOADER),
        processes=_processes,
        threaded=False,
    )
