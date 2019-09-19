class A:
    class _sub1:

        _types_map = {
            "prop1": {"type": int, "subtype": None},
            "prop2": {"type": float, "subtype": None},
        }
        _formats_map = {}
        _validations_map = {"prop1": {"required": False}, "prop2": {"required": False}}

        def __init__(self, prop1=None, prop2=None):
            pass
            self.__prop1 = prop1
            self.__prop2 = prop2

        def _get_prop1(self):
            return self.__prop1

        def _set_prop1(self, value):
            if not isinstance(value, int):
                raise TypeError("prop1 must be int")

            self.__prop1 = value

        prop1 = property(_get_prop1, _set_prop1)

        def _get_prop2(self):
            return self.__prop2

        def _set_prop2(self, value):
            if not isinstance(value, float):
                raise TypeError("prop2 must be float")

            self.__prop2 = value

        prop2 = property(_get_prop2, _set_prop2)

        @staticmethod
        def from_dict(d):
            v = {}
            if "prop1" in d:
                v["prop1"] = (
                    int.from_dict(d["prop1"])
                    if hasattr(int, "from_dict")
                    else d["prop1"]
                )
            if "prop2" in d:
                v["prop2"] = (
                    float.from_dict(d["prop2"])
                    if hasattr(float, "from_dict")
                    else d["prop2"]
                )
            return A._sub1(**v)

        def as_dict(self):
            d = {}
            if self.__prop1 is not None:
                d["prop1"] = (
                    self.__prop1.as_dict()
                    if hasattr(self.__prop1, "as_dict")
                    else self.__prop1
                )
            if self.__prop2 is not None:
                d["prop2"] = (
                    self.__prop2.as_dict()
                    if hasattr(self.__prop2, "as_dict")
                    else self.__prop2
                )
            return d

        def __repr__(self):
            return "<Class _sub1. prop1: {}, prop2: {}>".format(
                self.__prop1, self.__prop2
            )

    _types_map = {"sub1": {"type": list, "subtype": _sub1}}
    _formats_map = {}
    _validations_map = {"sub1": {"required": False}}

    def __init__(self, sub1=None):
        pass
        self.__sub1 = sub1

    def _get_sub1(self):
        return self.__sub1

    def _set_sub1(self, value):
        if not isinstance(value, list):
            raise TypeError("sub1 must be list")
        if not all(isinstance(i, A._sub1) for i in value):
            raise TypeError("sub1 list values must be A._sub1")

        self.__sub1 = value

    sub1 = property(_get_sub1, _set_sub1)

    @staticmethod
    def from_dict(d):
        v = {}
        if "sub1" in d:
            v["sub1"] = [
                A._sub1.from_dict(p) if hasattr(A._sub1, "from_dict") else p
                for p in d["sub1"]
            ]
        return A(**v)

    def as_dict(self):
        d = {}
        if self.__sub1 is not None:
            d["sub1"] = [
                p.as_dict() if hasattr(p, "as_dict") else p for p in self.__sub1
            ]
        return d

    def __repr__(self):
        return "<Class A. sub1: {}>".format(self.__sub1)


class RootObject:
    def __init__(self):
        pass

    @staticmethod
    def from_dict(d):
        v = {}
        return RootObject(**v)

    def as_dict(self):
        d = {}
        return d

    def __repr__(self):
        return "<Class RootObject. >".format()
