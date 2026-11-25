# -*- coding: utf-8 -*-
from datetime import datetime

def get_request_date(input_data):
    if input_data is None:
        return None
    d = getattr(input_data, "date", None)
    if d is None:
        return None
    if isinstance(d, str):
        return datetime.strptime(d, "%Y-%m-%d")
    return d
