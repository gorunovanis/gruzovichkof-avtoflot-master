# -*- coding: utf-8 -*-

class TariffLoaderSettings:
    def __init__(self, transport_msp=None, **kwargs):
        self.transport_msp = transport_msp

class Tariff:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

class TariffInfo:
    def __init__(self, tariff=None, tariff_start_date=None, description=None, error=None):
        self.tariff = tariff
        self.tariff_start_date = tariff_start_date
        self.description = description
        self.error = error
