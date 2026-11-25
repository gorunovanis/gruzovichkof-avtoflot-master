# -*- coding: utf-8 -*-

class CalculatorConfig:
    def __init__(self, transport_msp=None, insurer_msp=None, process=None, **kwargs):
        self.transport_msp = transport_msp
        self.insurer_msp = insurer_msp
        self.process = process
