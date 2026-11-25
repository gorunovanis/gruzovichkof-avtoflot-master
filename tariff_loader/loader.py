# -*- coding: utf-8 -*-
import json
import os
from datetime import datetime

from calc_utils.models import InsuranceType
from tariff_loader.models import TariffLoaderSettings, Tariff

# data dir relative to project root
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

class TariffLoader:
    def __init__(self, settings: TariffLoaderSettings, insurer_msp: dict):
        self.settings = settings
        self.insurer_msp = insurer_msp
        self.general_tariffs = {}
        self.general_tariffs_without_type = {}
        self._load_tariffs()

    def _load_tariffs(self):
        from calc_utils.models import InsuranceType
        self.general_tariffs[InsuranceType.cargo] = {}
        for ins_type, insurers in self.insurer_msp.items():
            if ins_type not in self.general_tariffs:
                self.general_tariffs[ins_type] = {}
            for insurer in insurers:
                self.general_tariffs[ins_type][insurer] = {}
        # Load from data/*.json: AlfastrahMSP_cargo_tariffs.json -> insurer=AlfastrahMSP
        if not os.path.isdir(DATA_DIR):
            return
        for fn in os.listdir(DATA_DIR):
            if not fn.endswith(".json") or "_cargo_tariffs" not in fn:
                continue
            insurer = fn.replace("_cargo_tariffs.json", "")
            path = os.path.join(DATA_DIR, fn)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                continue
            if InsuranceType.cargo not in self.general_tariffs:
                self.general_tariffs[InsuranceType.cargo] = {}
            if insurer not in self.general_tariffs[InsuranceType.cargo]:
                self.general_tariffs[InsuranceType.cargo][insurer] = {}
            for date_key, t in data.items():
                self.general_tariffs[InsuranceType.cargo][insurer][date_key] = Tariff(**t)

    def get_general_tariff_by_date(self, input_data, insurance_type, insurer=None):
        from tariff_loader.models import TariffInfo
        from tariff_loader.utils import get_request_date
        general_tariffs_by_ins_type = self.general_tariffs.get(insurance_type) or {}
        if not general_tariffs_by_ins_type:
            return None
        if insurer is None:
            insurer = getattr(input_data, "insuranceCompanyMSP", None)
        if callable(insurer):
            insurer = insurer(input_data)
        if not insurer or insurer not in general_tariffs_by_ins_type:
            return None
        date_keys = sorted(general_tariffs_by_ins_type[insurer].keys())
        if not date_keys:
            return None
        request_date = get_request_date(input_data)
        if not request_date:
            cur_tariff = general_tariffs_by_ins_type[insurer][date_keys[-1]]
            return TariffInfo(
                tariff=cur_tariff,
                tariff_start_date=datetime.now().strftime("%Y-%m-%d"),
                description="Применён тариф от %s" % datetime.now().strftime("%Y-%m-%d"),
            )
        cur_date = None
        cur_tariff = None
        for key in date_keys:
            actual = datetime.strptime(key, "%Y-%m-%d")
            if actual <= request_date:
                cur_date = key
                cur_tariff = general_tariffs_by_ins_type[insurer][key]
        if cur_tariff is None:
            return None
        return TariffInfo(
            tariff=cur_tariff,
            tariff_start_date=cur_date,
            description="Применён тариф от %s" % cur_date,
        )
