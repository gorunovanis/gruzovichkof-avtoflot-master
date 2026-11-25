from decimal import Decimal

from calc_utils import errors
from calc_utils.math import math_round_half_up
from log_service.models import RequestData, CalcOutput
from tariff_loader.models import Tariff


def get_insurance_premium_sogaz(
    input_data: RequestData, tariff: Tariff, response: CalcOutput
) -> bool:
    """Расчет СП в зависимости от секции и страховой суммы

    :param input_data: входящий запрос
    :param tariff: текущий тариф
    :param response: результат расчетов

    :return: True - СП рассчитана
             False - не удалось рассчитать СП
    """
    if not tariff.extraData:
        return False

    if input_data.declaredValue:
        declared_value_ratio = Decimal(
            str(tariff.extraData.get("declaredValueRatio")),
        )
        response.insurancePrice = int(
            math_round_half_up(
                float(declared_value_ratio) * input_data.declaredValue,
            )
        )
        return True
    return False


def set_insurance_sum_and_section_sogaz(
    input_data: RequestData, tariff: Tariff, response: CalcOutput
):
    """Установка значений секции и страховой суммы

    :param input_data: входящий запрос
    :param tariff: текущий тариф
    :param response: результат расчетов
    """
    response.insuranceSum = tariff.extraData.get("declaredValueLimit")
    if input_data.declaredValue < tariff.extraData.get("declaredValueLimit"):
        response.insuranceSum = int(input_data.declaredValue)

    response.extraData = {
        "insuranceSection": input_data.item.extraData.get("section"),
    }


def get_price_by_section(
    input_data: RequestData,
    tariff: Tariff,
    response: CalcOutput,
):
    """Расчет СП в зависимости от секции и страховой суммы

    :param input_data: входящий запрос
    :param tariff: текущий тариф
    :param response: результат расчетов

    :return: True - СП рассчитана
             False - не удалось рассчитать СП
    """
    input_data_section = input_data.item.extraData["section"]
    if input_data.declaredValue:
        if "declaredValueRatio" not in tariff.extraData:
            return False

        if "declaredValueLimitBySection" in tariff.extraData:
            for item in tariff.extraData["declaredValueLimitBySection"]:
                if item.get("section") == input_data_section:
                    limit = item.get("limit")
                    if input_data.declaredValue > limit:
                        response.error = errors.messages["exceedDeclaredValueLimit"]
                        return False

        min_price = 0
        if "minInsurancePrice" in tariff.extraData:
            min_price = int(tariff.extraData["minInsurancePrice"])

        response.insurancePrice = int(
            math_round_half_up(
                float(tariff.extraData["declaredValueRatio"]) * input_data.declaredValue
            )
        )
        if response.insurancePrice < min_price:
            response.insurancePrice = min_price
    else:
        if "declaredValueLimitByPrice" in tariff.extraData:
            _found = False
            input_ins_price = input_data.item.extraData["inputInsurancePrice"]
            for item in tariff.extraData["declaredValueLimitByPrice"]:
                if item.get("fixedPrice") == input_ins_price:
                    response.insurancePrice = input_ins_price
                    _found = True

            if not _found:
                response.error = errors.messages["rateNotFound"] % input_ins_price
                return False

    return True


def set_insurance_sum_and_section(
    input_data: RequestData, tariff: Tariff, response: CalcOutput
):
    """Установка значений секции и страховой суммы

    :param input_data: входящий запрос
    :param tariff: текущий тариф
    :param response: результат расчетов
    """
    response.insuranceSum = 0
    input_data_section = int(input_data.item.extraData["section"])
    if input_data.declaredValue:
        response.insuranceSum = int(input_data.declaredValue)
    else:
        if "declaredValueLimitByPrice" in tariff.extraData:
            for item in tariff.extraData["declaredValueLimitByPrice"]:
                if item.get("fixedPrice") == input_data.item.extraData.get(
                    "inputInsurancePrice"
                ):
                    response.insuranceSum = item["limit"]

    response.extraData = {"insuranceSection": str(input_data_section)}
