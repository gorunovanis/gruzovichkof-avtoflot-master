from datetime import datetime
from typing import Optional, Union

from calc_utils.models import InsuranceType
from log_service.models import RequestData
from tariff_loader.loader import TariffLoader
from tariff_loader.models import TariffInfo, Tariff
from tariff_loader.utils import get_request_date

from calc_utils import errors


class CustomTariffLoader(TariffLoader):
    """Кастомный загрузчик тарифов с поддержкой выбора по businessLine и id ГД для SberbankInsMSP"""

    def get_general_tariff_by_date(
        self,
        input_data: Union[RequestData, dict],
        insurance_type: InsuranceType,
        insurer: Optional[str] = None,
    ) -> Optional[TariffInfo]:
        """Получение тарифа с учетом businessLine и id ГД для SberbankInsMSP"""

        if insurance_type:
            general_tariffs_by_ins_type = self.general_tariffs.get(insurance_type)
        else:
            general_tariffs_by_ins_type = self.general_tariffs_without_type

        if not general_tariffs_by_ins_type:
            return

        if not insurer:
            insurer = input_data.insuranceCompanyMSP

        if callable(insurer):
            insurer = insurer(input_data)

        # Специальная логика для SberbankInsMSP
        if insurer == "SberbankInsMSP":
            return self._get_sberbank_tariff(
                input_data,
                insurance_type,
                insurer,
                general_tariffs_by_ins_type,
            )

        # Стандартная логика для остальных СК
        return super().get_general_tariff_by_date(
            input_data,
            insurance_type,
            insurer,
        )

    def _get_sberbank_tariff(
        self,
        input_data: Union[RequestData, dict],
        insurance_type: InsuranceType,
        insurer: str,
        general_tariffs_by_ins_type: dict,
    ) -> Optional[TariffInfo]:
        """Получение тарифа для SberbankInsMSP с учетом businessLine и id ГД"""

        date_keys = sorted(general_tariffs_by_ins_type.get(insurer, {}).keys())
        if not date_keys:
            return

        request_date = get_request_date(input_data)
        if not request_date:
            # Если дата не указана, возвращаем последний тариф
            cur_tariff: Tariff = general_tariffs_by_ins_type.get(insurer, {})[
                date_keys[-1]
            ]
            return TariffInfo(
                tariff=cur_tariff,
                tariff_start_date=datetime.now().strftime("%Y-%m-%d"),
                description=f'Применён тариф от {datetime.now().strftime("%Y-%m-%d")}',
            )

        # Получаем businessLine из запроса
        # Проверяем item.extraData.businessLine или insurance[0].extraData.businessLine
        business_line = None
        if hasattr(input_data, "item") and input_data.item:
            if isinstance(input_data.item, dict):
                business_line = (
                    input_data.item.get("extraData", {}).get("businessLine")
                    if input_data.item.get("extraData")
                    else None
                )
            elif hasattr(input_data.item, "extraData") and input_data.item.extraData:
                business_line = input_data.item.extraData.get("businessLine")

        if (
            not business_line
            and hasattr(input_data, "insurance")
            and input_data.insurance
        ):
            # Берем первый элемент списка insurance
            insurance_item = (
                input_data.insurance[0]
                if isinstance(input_data.insurance, list)
                else input_data.insurance
            )
            if hasattr(insurance_item, "extraData") and insurance_item.extraData:
                business_line = insurance_item.extraData.get("businessLine")

        # Получаем id ГД из запроса
        # Проверяем item.masterAgreementId или insurance[0].masterAgreementId
        master_agreement_id = None

        if hasattr(input_data, "item") and input_data.item:
            if isinstance(input_data.item, dict):
                master_agreement_id = input_data.item.get(
                    "masterAgreementId"
                ) or input_data.item.get("originalMasterAgreementId")
            elif (
                hasattr(input_data.item, "masterAgreementId")
                and input_data.item.masterAgreementId
            ):
                master_agreement_id = input_data.item.masterAgreementId
            elif (
                hasattr(input_data.item, "originalMasterAgreementId")
                and input_data.item.originalMasterAgreementId
            ):
                master_agreement_id = input_data.item.originalMasterAgreementId

        if (
            not master_agreement_id
            and hasattr(input_data, "insurance")
            and input_data.insurance
        ):
            insurance_item = (
                input_data.insurance[0]
                if isinstance(input_data.insurance, list)
                else input_data.insurance
            )
            if (
                hasattr(insurance_item, "masterAgreementId")
                and insurance_item.masterAgreementId
            ):
                master_agreement_id = insurance_item.masterAgreementId
            elif (
                hasattr(insurance_item, "originalMasterAgreementId")
                and insurance_item.originalMasterAgreementId
            ):
                master_agreement_id = insurance_item.originalMasterAgreementId

        # Проверяем, что дата в запросе позже начала действия первого тарифа
        cur_date = date_keys[0]
        tariff_start_date = datetime.strptime(cur_date, "%Y-%m-%d")
        if request_date < tariff_start_date:
            return

        # Логика выбора тарифа:
        # 1. Если указан businessLine - ищем тариф по businessLine
        # 2. Если businessLine не указан, но указан id ГД - ищем тариф по id ГД
        # 3. Если ни то, ни другое не указано - ошибка

        if business_line:
            # Ищем тариф по businessLine
            # Берем самый актуальный тариф (последний по дате, который не превышает request_date)
            matching_tariff = None
            matching_date = None

            for key in date_keys:
                actual_date = datetime.strptime(key, "%Y-%m-%d")
                if actual_date <= request_date:
                    tariff = general_tariffs_by_ins_type[insurer][key]
                    # Проверяем, что тариф не закончил своё действие
                    if tariff.endDate and request_date > datetime.strptime(
                        tariff.endDate, "%Y-%m-%d"
                    ):
                        continue

                    # Проверяем businessLine в тарифе
                    if (
                        tariff.extraData
                        and tariff.extraData.get("businessLine") == business_line
                    ):
                        # Обновляем matching_tariff, если нашли более актуальный тариф
                        matching_tariff = tariff
                        matching_date = key

            if matching_tariff:
                return TariffInfo(
                    tariff=matching_tariff,
                    tariff_start_date=matching_tariff.actualStartDate,
                    description=f"Применён тариф от {matching_tariff.actualStartDate} (businessLine: {business_line})",
                )
            else:
                # Тариф с указанным businessLine не найден
                return TariffInfo(
                    tariff=None,
                    error=errors.messages.get(
                        "invalidRequiredField", "Некорректное значение поля"
                    )
                    % "insurance.extraData.businessLine",
                )

        elif master_agreement_id:
            # Ищем тариф по id ГД
            # Для этого нужно найти тариф, у которого masterAgreementUID соответствует переданному id
            # Берем самый актуальный тариф (последний по дате, который не превышает request_date)
            matching_tariff = None
            matching_date = None

            for key in date_keys:
                actual_date = datetime.strptime(key, "%Y-%m-%d")
                if actual_date <= request_date:
                    tariff = general_tariffs_by_ins_type[insurer][key]
                    # Проверяем, что тариф не закончил своё действие
                    if tariff.endDate and request_date > datetime.strptime(
                        tariff.endDate, "%Y-%m-%d"
                    ):
                        continue

                    # Проверяем masterAgreementUID в тарифе
                    if tariff.masterAgreementUID == master_agreement_id:
                        # Обновляем matching_tariff, если нашли более актуальный тариф
                        matching_tariff = tariff
                        matching_date = key

            if matching_tariff:
                return TariffInfo(
                    tariff=matching_tariff,
                    tariff_start_date=matching_tariff.actualStartDate,
                    description=f"Применён тариф от {matching_tariff.actualStartDate} (ГД: {master_agreement_id})",
                )
            else:
                # Тариф с указанным id ГД не найден
                return TariffInfo(
                    tariff=None,
                    error=errors.messages.get(
                        "invalidRequiredField", "Некорректное значение поля"
                    )
                    % "insurance.extraData.originalMasterAgreementId",
                )
        else:
            # Не указаны ни businessLine, ни id ГД - ошибка
            return TariffInfo(
                tariff=None,
                error=errors.messages.get(
                    "missRequiredField", "Отсутствует обязательное поле"
                )
                % "insurance.originalMasterAgreementId",
            )
