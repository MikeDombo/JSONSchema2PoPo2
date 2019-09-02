#!/usr/bin/env/python


class ABcd:

    _types_map = {
        "Child1": {"type": int, "subtype": None},
        "Child2": {"type": str, "subtype": None},
    }
    _formats_map = {}

    def __init__(self, Child1=None, Child2=None):
        pass
        self.__Child1 = Child1
        self.__Child2 = Child2

    def _get_Child1(self):
        return self.__Child1

    def _set_Child1(self, value):
        if not isinstance(value, int):
            raise TypeError("Child1 must be int")

        self.__Child1 = value

    Child1 = property(_get_Child1, _set_Child1)

    def _get_Child2(self):
        return self.__Child2

    def _set_Child2(self, value):
        if not isinstance(value, str):
            raise TypeError("Child2 must be str")

        self.__Child2 = value

    Child2 = property(_get_Child2, _set_Child2)

    @staticmethod
    def from_dict(d):
        v = {}
        if "Child1" in d:
            if not isinstance(d["Child1"], int):
                raise TypeError("Child1 must be int")

            v["Child1"] = (
                int.from_dict(d["Child1"]) if hasattr(int, "from_dict") else d["Child1"]
            )
        if "Child2" in d:
            if not isinstance(d["Child2"], str):
                raise TypeError("Child2 must be str")

            v["Child2"] = (
                str.from_dict(d["Child2"]) if hasattr(str, "from_dict") else d["Child2"]
            )
        return ABcd(**v)

    def as_dict(self):
        d = {}
        if self.__Child1 is not None:
            d["Child1"] = (
                self.__Child1.as_dict()
                if hasattr(self.__Child1, "as_dict")
                else self.__Child1
            )
        if self.__Child2 is not None:
            d["Child2"] = (
                self.__Child2.as_dict()
                if hasattr(self.__Child2, "as_dict")
                else self.__Child2
            )
        return d

    def __repr__(self):
        return "<Class ABcd. Child1: {}, Child2: {}>".format(
            self.__Child1, self.__Child2
        )


class SubRef:

    _types_map = {"ChildA": {"type": ABcd, "subtype": None}}
    _formats_map = {}

    def __init__(self, ChildA=None):
        pass
        self.__ChildA = ChildA

    def _get_ChildA(self):
        return self.__ChildA

    def _set_ChildA(self, value):
        if not isinstance(value, ABcd):
            raise TypeError("ChildA must be ABcd")

        self.__ChildA = value

    ChildA = property(_get_ChildA, _set_ChildA)

    @staticmethod
    def from_dict(d):
        v = {}
        if "ChildA" in d:
            if not isinstance(d["ChildA"], ABcd):
                raise TypeError("ChildA must be ABcd")

            v["ChildA"] = (
                ABcd.from_dict(d["ChildA"])
                if hasattr(ABcd, "from_dict")
                else d["ChildA"]
            )
        return SubRef(**v)

    def as_dict(self):
        d = {}
        if self.__ChildA is not None:
            d["ChildA"] = (
                self.__ChildA.as_dict()
                if hasattr(self.__ChildA, "as_dict")
                else self.__ChildA
            )
        return d

    def __repr__(self):
        return "<Class SubRef. ChildA: {}>".format(self.__ChildA)


class DirectRef:

    _types_map = {
        "Child1": {"type": int, "subtype": None},
        "Child2": {"type": str, "subtype": None},
    }
    _formats_map = {}

    def __init__(self, Child1=None, Child2=None):
        pass
        self.__Child1 = Child1
        self.__Child2 = Child2

    def _get_Child1(self):
        return self.__Child1

    def _set_Child1(self, value):
        if not isinstance(value, int):
            raise TypeError("Child1 must be int")

        self.__Child1 = value

    Child1 = property(_get_Child1, _set_Child1)

    def _get_Child2(self):
        return self.__Child2

    def _set_Child2(self, value):
        if not isinstance(value, str):
            raise TypeError("Child2 must be str")

        self.__Child2 = value

    Child2 = property(_get_Child2, _set_Child2)

    @staticmethod
    def from_dict(d):
        v = {}
        if "Child1" in d:
            if not isinstance(d["Child1"], int):
                raise TypeError("Child1 must be int")

            v["Child1"] = (
                int.from_dict(d["Child1"]) if hasattr(int, "from_dict") else d["Child1"]
            )
        if "Child2" in d:
            if not isinstance(d["Child2"], str):
                raise TypeError("Child2 must be str")

            v["Child2"] = (
                str.from_dict(d["Child2"]) if hasattr(str, "from_dict") else d["Child2"]
            )
        return DirectRef(**v)

    def as_dict(self):
        d = {}
        if self.__Child1 is not None:
            d["Child1"] = (
                self.__Child1.as_dict()
                if hasattr(self.__Child1, "as_dict")
                else self.__Child1
            )
        if self.__Child2 is not None:
            d["Child2"] = (
                self.__Child2.as_dict()
                if hasattr(self.__Child2, "as_dict")
                else self.__Child2
            )
        return d

    def __repr__(self):
        return "<Class DirectRef. Child1: {}, Child2: {}>".format(
            self.__Child1, self.__Child2
        )


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
