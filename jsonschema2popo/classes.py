import abc
import argparse
from typing import Dict, Any, List, Set, Optional, Callable, Type

extra_generation_options = dict()


def translate_properties():
    return extra_generation_options.get("translate_properties", False)


class Definition:
    name: str
    type: str
    parent: "Definition"
    extends: "Definition"
    children: Set["Definition"]
    comment: str
    is_primitive: bool = True

    def __init__(self):
        self.children = set()

    @property
    def string_type(self):
        return self.type

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
                lambda a: a.python_type_name,
                self.ancestors(
                    stop=Definition.lowest_common_ancestor(self, relative_to)
                ),
            )
        )
        return ".".join(l)

    @property
    def python_type_name(self):
        # When this is a subtype and we're not translating properties then we do not prefix the type with an underscore
        # because the subtype's name shouldn't be conflicting with the property of the parent class
        # since we've translated the name. There is some possibility of conflicts when the property name is a single
        # word, in which case this would output broken code. Keeping it this way for compatibility with 2.x.x.
        if self.parent is not None and not translate_properties():
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


class ListNode(Definition):
    item_type: Definition
    item_format: Optional[str]
    type = "list"

    def __init__(
        self, item_type: Definition = None, parent: Definition = None, name: str = None
    ):
        super().__init__()
        self.item_type = item_type
        self.parent = parent
        self.name = name
        self.item_format = None

    @property
    def string_item_type(self):
        return self.item_type.string_type

    @property
    def is_primitive(self):
        return self.item_type.is_primitive


class Property:
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


class ObjectNode(Definition):
    type = "object"
    properties: List[Property]
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
            return self.type
        return self.full_name_path


class StringNode(Definition):
    type = "string"
    specific_type: Optional[type]

    def __init__(self, parent: Definition = None, name: str = None):
        super().__init__()
        self.parent = parent
        self.name = name
        self.specific_type = None

    @property
    def string_type(self):
        return self.specific_type and self.specific_type.__name__ or self.type


class EnumNode(Definition):
    type = "enum"
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


class NumericNode(Definition):
    type = "number"

    def __init__(self, parent: Definition = None, name: str = None):
        super().__init__()
        self.parent = parent
        self.name = name


class IntegerNode(Definition):
    type = "integer"

    def __init__(self, parent: Definition = None, name: str = None):
        super().__init__()
        self.parent = parent
        self.name = name


class BooleanNode(Definition):
    type = "boolean"

    def __init__(self, parent: Definition = None, name: str = None):
        super().__init__()
        self.parent = parent
        self.name = name


class NullNode(Definition):
    type = "null"

    def __init__(self, parent: Definition = None, name: str = None):
        super().__init__()
        self.parent = parent
        self.name = name


class ReferenceNode(Definition):
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
        # Automatically copy all properties from the referenced value into this type
        # so that users can just do x.y instead of x.value.y; this way the fact that this
        # is a reference shouldn't matter to any users.
        # Copy most, but not quite all values.
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
            try:
                self.__setattr__(k, v.__getattribute__(k))
            except AttributeError:
                pass

    value = property(__value_getter, __value_setter)

    @property
    def string_type(self):
        return self.value.string_type

    @property
    def full_name_path(self):
        if isinstance(self.value, ObjectNode) and self.parent is None:
            return self.name
        return self.value.full_name_path

    def full_name_python_path(self, relative_to: Definition = None):
        if isinstance(self.value, ObjectNode) and self.parent is None:
            return self.name
        return self.value.full_name_python_path(relative_to=relative_to)

    @property
    def python_type_name(self):
        if isinstance(self.value, ObjectNode) and self.parent is None:
            return self.name
        return self.value.python_type_name


class CodeGenPlugin(abc.ABC):
    @abc.abstractmethod
    def plugin_name(self) -> str:
        pass

    @abc.abstractmethod
    def plugin_version(self) -> str:
        pass

    @abc.abstractmethod
    def template_search_path(self) -> str:
        pass

    @abc.abstractmethod
    def template(self) -> str:
        pass

    def jinja_globals(self) -> Dict[str, Callable]:
        pass

    def command_line_parser(self, sub_parser: argparse.ArgumentParser) -> None:
        pass

    def set_args(self, args: argparse.Namespace) -> None:
        pass

    def after_processing(self, definitions: List[Definition]):
        pass

    def extra_jinja_inputs(self) -> Dict[str, Any]:
        return {}

    def after_generation(self, filename: Optional[str] = None) -> None:
        pass
