# -*- coding: utf-8 -*-
from flask import Flask, request, jsonify
from calc_utils.models import InsuranceType
from log_service.models import RequestData, CalcOutput

class LogService:
    def log_start(self, port):
        print("Server starting on port %s" % port)

class ApiTemplate:
    def __init__(self, calc_config, check_fields=None, calculator=None, get_insurer_msp=None, tariff_loader=None):
        self.calc_config = calc_config
        self.check_fields = check_fields
        self.calculator = calculator
        self.get_insurer_msp = get_insurer_msp
        self.tariff_loader = tariff_loader
        self.log_service = LogService()

    def get_app(self):
        app = Flask(__name__)

        @app.route("/")
        def index():
            return (
                "<h1>Калькулятор Грузовичкёф Автофлот</h1>"
                "<p>Сервис запущен. Доступные эндпоинты:</p>"
                "<ul>"
                '<li><a href="/api/v1/calc_config">GET /api/v1/calc_config</a> — конфигурация</li>'
                "<li>POST /api/v1/calc_price_all — расчёт цены</li>"
                "<li>POST /api/v1/calc_price_bulk_all — расчёт по списку</li>"
                "</ul>"
            ), 200

        @app.route("/api/v1/calc_price_all", methods=["POST"])
        def calc_price_all():
            try:
                data = request.get_json(force=True, silent=True) or {}
                if isinstance(data, list):
                    data = data[0] if data else {}
                input_data = RequestData(**data)
                insurance_type = InsuranceType.cargo
                if self.check_fields:
                    err = self.check_fields(input_data, insurance_type)
                    if err:
                        return jsonify({"error": err}), 400
                insurer = self.get_insurer_msp(input_data) if self.get_insurer_msp else getattr(input_data, "insuranceCompanyMSP", None)
                tariff_info = self.tariff_loader.get_general_tariff_by_date(input_data, insurance_type, insurer)
                if not tariff_info or not getattr(tariff_info, "tariff", None):
                    if tariff_info and getattr(tariff_info, "error", None):
                        return jsonify({"error": tariff_info.error}), 400
                    return jsonify({"error": "Тариф не найден"}), 404
                output = self.calculator(input_data, tariff_info.tariff, insurance_type)
                return jsonify(output.to_dict())
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        @app.route("/api/v1/calc_price_bulk_all", methods=["POST"])
        def calc_price_bulk_all():
            try:
                data = request.get_json(force=True, silent=True)
                if not isinstance(data, list):
                    data = [data] if data else []
                results = []
                for item in data:
                    d = item if isinstance(item, dict) else {}
                    input_data = RequestData(**d)
                    insurance_type = InsuranceType.cargo
                    err = self.check_fields(input_data, insurance_type) if self.check_fields else None
                    if err:
                        results.append({"error": err})
                        continue
                    insurer = self.get_insurer_msp(input_data) if self.get_insurer_msp else getattr(input_data, "insuranceCompanyMSP", None)
                    tariff_info = self.tariff_loader.get_general_tariff_by_date(input_data, insurance_type, insurer)
                    if not tariff_info or not getattr(tariff_info, "tariff", None):
                        results.append({"error": tariff_info.error if tariff_info else "Тариф не найден"})
                        continue
                    output = self.calculator(input_data, tariff_info.tariff, insurance_type)
                    results.append(output.to_dict())
                return jsonify(results)
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        return app

    def auth(self, tech=False):
        def deco(f):
            return f
        return deco
