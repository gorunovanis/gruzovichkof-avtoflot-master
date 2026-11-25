# -*- coding: utf-8 -*-

class _DotDict(dict):
    def __init__(self, d=None, **kw):
        super().__init__(d or {}, **kw)
    def __getattr__(self, k):
        v = self.get(k)
        if isinstance(v, dict) and not isinstance(v, _DotDict):
            return _DotDict(v)
        return v
    def __setattr__(self, k, v):
        if k.startswith("_"):
            super().__setattr__(k, v)
        else:
            self[k] = v

class RequestData:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            if k == "item" and v is not None and isinstance(v, dict):
                setattr(self, k, _DotDict(v))
            else:
                setattr(self, k, v)

class CalcOutput:
    def __init__(self, **kwargs):
        self.insuranceType = None
        self.insurancePrice = None
        self.insuranceSum = None
        self.extraData = None
        self.error = None
        self._exists = 0
        for k, v in kwargs.items():
            setattr(self, k, v)

    def to_dict(self):
        d = {"insuranceType": self.insuranceType}
        if self.insurancePrice is not None:
            d["insurancePrice"] = self.insurancePrice
        if self.insuranceSum is not None:
            d["insuranceSum"] = self.insuranceSum
        if self.extraData is not None:
            d["extraData"] = self.extraData
        if self.error is not None:
            d["error"] = self.error
        return d
