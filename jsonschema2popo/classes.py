from typing import Dict, Any, List, Set


class Definition:
    name: str
    m_type: str
    parent: "Definition"
    extends: "Definition"
    children: Set["Definition"]
    comment: str
    most_specific_type: type
    is_primitive: bool = True

    def __init__(self):
        self.children = set()

    @property
    def string_type(self):
        if hasattr(self, "most_specific_type"):
            return self.most_specific_type.__name__
        return self.m_type

    @property
    def names(self):
        return list(map(lambda a: a.name, self.ancestors()))

    def ancestors(self, stop: "Definition" = None):
        ancestors = [self]
        p = self.parent
        while p is not None and p != stop:
            ancestors.append(p)
            p = p.parent
        return list(reversed(ancestors))

    @property
    def full_name_path(self):
        return ".".join(self.names)

    def full_name_python_path(self, relative_to: "Definition" = None):
        l = list(
            map(
                lambda a: a.name,
                self.ancestors(
                    stop=Definition.lowest_common_ancestor(self, relative_to)
                ),
            )
        )
        if len(l) == 1 and self.parent is not None:
            return "_" + self.name
        return "._".join(l)

    @property
    def python_type_name(self):
        if self.parent is not None:
            return "_" + self.name
        return self.name

    @staticmethod
    def lowest_common_ancestor(a: "Definition", b: "Definition") -> "Definition":
        if b is None:
            return a
        path1 = a.ancestors()
        path2 = b.ancestors()
        i = 0
        while i < len(path1) and i < len(path2):
            if path1[i] != path2[i]:
                break
            i += 1
        return path1[i - 1]


class ListType(Definition):
    item_type: Definition
    item_format: dict
    m_type = "list"

    def __init__(
        self, item_type: Definition = None, parent: Definition = None, name: str = None
    ):
        super().__init__()
        self.item_type = item_type
        self.parent = parent
        self.name = name

    @property
    def string_item_type(self):
        return self.item_type.string_type

    @property
    def is_primitive(self):
        return self.item_type.is_primitive


class Properties:
    name: str
    definition: Definition
    default: Any
    comment: str
    format: str
    validations: Dict

    def __init__(
        self,
        name=None,
        default=None,
        definition: Definition = None,
        comment: str = None,
    ):
        self.name = name
        self.default = default
        self.definition = definition
        self.comment = comment


class ObjectType(Definition):
    m_type = "object"
    properties: List[Properties]
    properties_have_comments: bool

    def __init__(self, properties=None, parent: Definition = None, name: str = None):
        super().__init__()
        if properties is None:
            properties = []
        self.properties = properties
        self.parent = parent
        self.name = name

    @property
    def is_primitive(self):
        return (
            len(self.properties) == 0 and self.parent is not None
        )  # if there are no properties and it isn't a
        # root-defined object then it is primitive

    @property
    def string_type(self):
        if self.is_primitive:
            return self.m_type
        return self.full_name_path


class StringType(Definition):
    m_type = "string"

    def __init__(self, parent: Definition = None, name: str = None):
        super().__init__()
        self.parent = parent
        self.name = name


class EnumType(Definition):
    m_type = "enum"
    value_type: Definition
    values: Dict[str, str]
    is_primitive = False

    def __init__(
        self, parent: Definition = None, name: str = None, values: Dict[str, str] = None
    ):
        super().__init__()
        self.parent = parent
        self.name = name
        self.values = values


class NumericType(Definition):
    m_type = "number"

    def __init__(self, parent: Definition = None, name: str = None):
        super().__init__()
        self.parent = parent
        self.name = name


class IntegerType(Definition):
    m_type = "integer"

    def __init__(self, parent: Definition = None, name: str = None):
        super().__init__()
        self.parent = parent
        self.name = name


class BooleanType(Definition):
    m_type = "boolean"

    def __init__(self, parent: Definition = None, name: str = None):
        super().__init__()
        self.parent = parent
        self.name = name


class NullType(Definition):
    m_type = "null"

    def __init__(self, parent: Definition = None, name: str = None):
        super().__init__()
        self.parent = parent
        self.name = name


class ReferenceType(Definition):
    value: Definition

    def __init__(
        self, value: Definition = None, parent: Definition = None, name: str = None
    ):
        super().__init__()
        self.__value_setter(value)
        self.parent = parent
        self.name = name

    def __value_getter(self):
        return self.__value

    def __value_setter(self, v: Definition):
        self.__value = v
        for k in v.__dir__():
            if (
                k.startswith("__")
                or k == "parent"
                or k == "name"
                or k == "comment"
                or k == "full_name_python_path"
            ):
                continue
            if isinstance(v.__getattribute__(k), property):
                continue
            print(k, v.__getattribute__(k).__class__)
            try:
                self.__setattr__(k, v.__getattribute__(k))
            except AttributeError as e:
                print(k, e)

    value = property(__value_getter, __value_setter)

    @property
    def string_type(self):
        return self.value.string_type

    @property
    def full_name_path(self):
        if isinstance(self.value, ObjectType) and self.parent is None:
            return self.name
        return self.value.full_name_path

    def full_name_python_path(self, relative_to: Definition = None):
        if isinstance(self.value, ObjectType) and self.parent is None:
            return self.name
        return self.value.full_name_python_path(relative_to=relative_to)

    @property
    def python_type_name(self):
        if isinstance(self.value, ObjectType) and self.parent is None:
            return self.name
        return self.value.python_type_name
