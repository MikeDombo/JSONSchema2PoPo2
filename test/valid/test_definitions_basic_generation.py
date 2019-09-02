#!/usr/bin/env/python


class ABcd:
    class _Object:
        def __init__(self):
            pass

        @staticmethod
        def from_dict(d):
            v = {}
            return ABcd._Object(**v)

        def as_dict(self):
            d = {}
            return d

        def __repr__(self):
            return "<Class _Object. >".format()

    _types_map = {
        "Int": {"type": int, "subtype": None},
        "Float": {"type": float, "subtype": None},
        "ListInt": {"type": list, "subtype": int},
        "String": {"type": str, "subtype": None},
        "Object": {"type": _Object, "subtype": None},
    }
    _formats_map = {}

    def __init__(self, Int=None, Float=None, ListInt=None, String=None, Object=None):
        pass
        self.__Int = Int
        self.__Float = Float
        self.__ListInt = ListInt
        self.__String = String
        self.__Object = Object

    def _get_Int(self):
        return self.__Int

    def _set_Int(self, value):
        if not isinstance(value, int):
            raise TypeError("Int must be int")

        self.__Int = value

    Int = property(_get_Int, _set_Int)

    def _get_Float(self):
        return self.__Float

    def _set_Float(self, value):
        if not isinstance(value, float):
            raise TypeError("Float must be float")

        self.__Float = value

    Float = property(_get_Float, _set_Float)

    def _get_ListInt(self):
        return self.__ListInt

    def _set_ListInt(self, value):
        if not isinstance(value, list):
            raise TypeError("ListInt must be list")
        if not all(isinstance(i, int) for i in value):
            raise TypeError("ListInt list values must be int")

        self.__ListInt = value

    ListInt = property(_get_ListInt, _set_ListInt)

    def _get_String(self):
        return self.__String

    def _set_String(self, value):
        if not isinstance(value, str):
            raise TypeError("String must be str")

        self.__String = value

    String = property(_get_String, _set_String)

    def _get_Object(self):
        return self.__Object

    def _set_Object(self, value):
        if not isinstance(value, ABcd._Object):
            raise TypeError("Object must be ABcd._Object")

        self.__Object = value

    Object = property(_get_Object, _set_Object)

    @staticmethod
    def from_dict(d):
        v = {}
        if "Int" in d:
            if not isinstance(d["Int"], int):
                raise TypeError("Int must be int")

            v["Int"] = (
                int.from_dict(d["Int"]) if hasattr(int, "from_dict") else d["Int"]
            )
        if "Float" in d:
            if not isinstance(d["Float"], float):
                raise TypeError("Float must be float")

            v["Float"] = (
                float.from_dict(d["Float"])
                if hasattr(float, "from_dict")
                else d["Float"]
            )
        if "ListInt" in d:
            if not isinstance(d["ListInt"], list):
                raise TypeError("ListInt must be list")
            if not all(isinstance(i, int) for i in d["ListInt"]):
                raise TypeError("ListInt list values must be int")

            v["ListInt"] = [
                int.from_dict(p) if hasattr(int, "from_dict") else p
                for p in d["ListInt"]
            ]
        if "String" in d:
            if not isinstance(d["String"], str):
                raise TypeError("String must be str")

            v["String"] = (
                str.from_dict(d["String"]) if hasattr(str, "from_dict") else d["String"]
            )
        if "Object" in d:
            if not isinstance(d["Object"], ABcd._Object):
                raise TypeError("Object must be ABcd._Object")

            v["Object"] = (
                ABcd._Object.from_dict(d["Object"])
                if hasattr(ABcd._Object, "from_dict")
                else d["Object"]
            )
        return ABcd(**v)

    def as_dict(self):
        d = {}
        if self.__Int is not None:
            d["Int"] = (
                self.__Int.as_dict() if hasattr(self.__Int, "as_dict") else self.__Int
            )
        if self.__Float is not None:
            d["Float"] = (
                self.__Float.as_dict()
                if hasattr(self.__Float, "as_dict")
                else self.__Float
            )
        if self.__ListInt is not None:
            d["ListInt"] = [
                p.as_dict() if hasattr(p, "as_dict") else p for p in self.__ListInt
            ]
        if self.__String is not None:
            d["String"] = (
                self.__String.as_dict()
                if hasattr(self.__String, "as_dict")
                else self.__String
            )
        if self.__Object is not None:
            d["Object"] = (
                self.__Object.as_dict()
                if hasattr(self.__Object, "as_dict")
                else self.__Object
            )
        return d

    def __repr__(self):
        return "<Class ABcd. Int: {}, Float: {}, ListInt: {}, String: {}, Object: {}>".format(
            self.__Int, self.__Float, self.__ListInt, self.__String, self.__Object
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
