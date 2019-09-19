class B:

    _types_map = {"prop1": {"type": int, "subtype": None}}
    _formats_map = {}
    _validations_map = {"prop1": {"required": False}}

    def __init__(self, prop1=None):
        pass
        self.__prop1 = prop1

    def _get_prop1(self):
        return self.__prop1

    def _set_prop1(self, value):
        if not isinstance(value, int):
            raise TypeError("prop1 must be int")

        self.__prop1 = value

    prop1 = property(_get_prop1, _set_prop1)

    @staticmethod
    def from_dict(d):
        v = {}
        if "prop1" in d:
            v["prop1"] = (
                int.from_dict(d["prop1"]) if hasattr(int, "from_dict") else d["prop1"]
            )
        return B(**v)

    def as_dict(self):
        d = {}
        if self.__prop1 is not None:
            d["prop1"] = (
                self.__prop1.as_dict()
                if hasattr(self.__prop1, "as_dict")
                else self.__prop1
            )
        return d

    def __repr__(self):
        return "<Class B. prop1: {}>".format(self.__prop1)


class A:

    _types_map = {"prop1": {"type": list, "subtype": B}}
    _formats_map = {}
    _validations_map = {"prop1": {"required": False}}

    def __init__(self, prop1=None):
        pass
        self.__prop1 = prop1

    def _get_prop1(self):
        return self.__prop1

    def _set_prop1(self, value):
        if not isinstance(value, list):
            raise TypeError("prop1 must be list")
        if not all(isinstance(i, B) for i in value):
            raise TypeError("prop1 list values must be B")

        self.__prop1 = value

    prop1 = property(_get_prop1, _set_prop1)

    @staticmethod
    def from_dict(d):
        v = {}
        if "prop1" in d:
            v["prop1"] = [
                B.from_dict(p) if hasattr(B, "from_dict") else p for p in d["prop1"]
            ]
        return A(**v)

    def as_dict(self):
        d = {}
        if self.__prop1 is not None:
            d["prop1"] = [
                p.as_dict() if hasattr(p, "as_dict") else p for p in self.__prop1
            ]
        return d

    def __repr__(self):
        return "<Class A. prop1: {}>".format(self.__prop1)


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
