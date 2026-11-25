# -*- coding: utf-8 -*-
import decimal

def math_round_half_up(x):
    return int(decimal.Decimal(str(x)).quantize(decimal.Decimal("1"), rounding=decimal.ROUND_HALF_UP))
