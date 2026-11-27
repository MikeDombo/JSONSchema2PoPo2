#!/usr/bin/env python
import argparse
import importlib
import json
import logging
import os
import re
import sys
from collections import defaultdict
from typing import List, Optional, Dict, Set

import networkx
from jinja2 import Environment, FileSystemLoader

from jsonschema2popo.classes import (
    Definition,
    ReferenceNode,
    EnumNode,
    ListNode,
    StringNode,
    IntegerNode,
    NumericNode,
    ObjectNode,
    BooleanNode,
    NullNode,
    Property,
    extra_generation_options,
    CodeGenPlugin,
)
from . import __version__

logger = logging.getLogger("main")

# Strings that were always pasted into the code unquoted and are kept that way (ignoring surrounding whitespace):
# a number in any notation the languages accept (0x10, 1_000, 1e-3, 10n...), or a plain dotted name such as
# True, null, Color.RED or -Infinity. Neither can call anything; any other string is quoted.
UNQUOTED_RE = re.compile(
    r"[+-]?(\.?\d[\w.]*([eE][+-]\d\w*)?|[^\W\d]\w*(\.[^\W\d]\w*)*)"
)

# Characters that end a single-line string literal, and whether a backslash may escape them (line continuation)
LINE_BREAKS = {"python": ("\r\n", True), "js": ("\r\n", True), "go": ("\n", False)}


def is_closed_docstring(s: str) -> bool:
    """
    Whether s can go between triple quotes as-is: no unescaped \"\"\" inside it. The template puts a newline after
    the text, so a trailing backslash can't escape the closing quotes.
    """
    i = 0
    while i < len(s):
        if s[i] == "\\":
            i += 2
        elif s.startswith('"""', i):
            return False
        else:
            i += 1
    return True


def is_closed_js_regex(s: str) -> bool:
    """Whether /s/ is one complete JS regex literal (like old_literal, plus [...] classes)."""
    if not s or s[0] == "*":
        return False
    in_class = False
    i = 0
    while i < len(s):
        c = s[i]
        if c in "\r\n\u2028\u2029":
            return False
        if c == "\\":
            if i + 1 >= len(s) or s[i + 1] in "\r\n\u2028\u2029":
                return False
            i += 2
            continue
        if c == "[":
            in_class = True
        elif c == "]":
            in_class = False
        elif c == "/" and not in_class:
            return False
        i += 1
    # An unclosed [ class would swallow the closing / and whatever follows it on the line
    return not in_class


def json_literal(v) -> str:
    # U+2028/U+2029 are valid in JS strings but jsbeautifier turns them into line breaks, so escape them
    return (
        json.dumps(v, ensure_ascii=False)
        .replace("\u2028", "\\u2028")
        .replace("\u2029", "\\u2029")
    )


def old_literal(s: str, quote: str, language: str) -> Optional[str]:
    """
    quote + s + quote, as the templates used to emit it, if that is one complete string literal in the language:
    every quote inside s is escaped, s does not end in an escaping backslash, and line breaks only appear as
    line continuations where the language allows them. Escape sequences then mean exactly what they used to.
    Raw U+2028/U+2029 are escaped (same value) because jsbeautifier would turn them into line breaks.
    Returns None if the old form was not a complete literal.
    """
    breaks, continuation = LINE_BREAKS[language]
    out = []
    i = 0
    while i < len(s):
        c = s[i]
        if c == "\\":
            if i + 1 >= len(s) or (s[i + 1] in breaks and not continuation):
                return None
            j = i + 3 if s.startswith("\r\n", i + 1) else i + 2
            out.append(s[i:j])
            i = j
            continue
        if s.startswith(quote, i) or c in breaks:
            return None
        out.append("\\u%04x" % ord(c) if c in "\u2028\u2029" else c)
        i += 1
    return quote + "".join(out) + quote


def py_quote(v, quote: str) -> str:
    """A Python string literal for v: the old quote + v + quote when that was already a complete literal."""
    s = str(v)
    return old_literal(s, quote, "python") or repr(s)


def json_quote(v, quote: str, language: str = "js") -> str:
    """A JS/Go string literal for v: the old quote + v + quote when that was already a complete literal."""
    s = str(v)
    return old_literal(s, quote, language) or json_literal(s)


def unquoted(v) -> Optional[str]:
    """The text a string value used to be pasted in as, if it is a number or a plain name; otherwise None."""
    t = v.strip()
    return t if UNQUOTED_RE.fullmatch(t) else None


def py_value(v) -> str:
    """Python source for a value that was emitted unquoted: as before, except strings that aren't numbers or names are quoted."""
    if isinstance(v, str):
        return unquoted(v) or repr(v)
    return str(v)


def json_value(v) -> str:
    """JS/Go source for a value that was emitted unquoted: numbers and names as before, everything else as JSON."""
    if isinstance(v, str):
        return unquoted(v) or json_literal(v)
    return json_literal(v)


def py_docstring(s: str) -> str:
    """Docstring text, unchanged unless it would end the docstring early; then every '"' is escaped."""
    return s if is_closed_docstring(s) else s.replace('"', '\\"')


def js_regex(v) -> str:
    s = str(v)
    return (
        "/" + s + "/"
        if is_closed_js_regex(s)
        else "new RegExp(" + json_literal(s) + ")"
    )


J2P_TYPES = {
    "string": str,
    "integer": int,
    "number": float,
    "object": dict,
    "list": list,
    "boolean": bool,
    "null": None,
    "bytes": bytes,
}


def string_to_type(t: str) -> str:
    return J2P_TYPES[t].__name__ if t in J2P_TYPES else t


class JsonSchema2Popo:
    """Converts a JSON Schema to a Plain Old Python Object class"""

    J2P_TYPES = {
        "string": StringNode(),
        "integer": IntegerNode(),
        "number": NumericNode(),
        "object": ObjectNode(),
        "array": ListNode(),
        "boolean": BooleanNode(),
        "null": NullNode(),
    }

    @staticmethod
    def flatten(something):
        if isinstance(something, (list, tuple, set, range)):
            for sub in something:
                yield from JsonSchema2Popo.flatten(sub)
        else:
            yield something

    def __init__(
        self,
        generate_definitions=True,
        generate_root=True,
        translate_properties=False,
        language="python",
        custom_template="",
    ):
        self.list_used = False
        self.enum_used = False

        if language == "python" or language == "js" or language == "go":
            self.module = importlib.import_module("." + language, "jsonschema2popo")
        # Try importing from a specified file path
        elif os.path.exists(language):
            spec = importlib.util.spec_from_file_location("", language)
            self.module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(self.module)
        # Try importing from some other python module
        else:
            self.module = importlib.import_module(language)
        self.module: CodeGenPlugin = self.module.Plugin()
        search_path = (
            self.module.template_search_path() if not custom_template else os.getcwd()
        )

        self.jinja = Environment(
            loader=FileSystemLoader(searchpath=search_path), trim_blocks=True
        )
        self.jinja.filters["regex_replace"] = lambda s, find, replace: re.sub(
            find, replace, s
        )
        self.jinja.globals["trn"] = self.maybe_translate_property_name
        # Values from the schema are emitted as literals, never pasted into the generated source as code.
        self.jinja.filters.update(
            py_quote=py_quote,
            py_value=py_value,
            py_docstring=py_docstring,
            json_literal=json_literal,
            json_quote=json_quote,
            json_value=json_value,
            js_regex=js_regex,
        )
        self.jinja.filters["block_comment"] = lambda s: s.replace("*/", "*\\/")
        self.jinja.filters["trn"] = self.maybe_translate_property_name

        jinja_globals = self.module.jinja_globals()
        self.jinja.globals.update(jinja_globals)
        self.jinja.filters.update(jinja_globals)

        self.generate_root = generate_root
        self.generate_definitions = generate_definitions
        self.translate_properties = translate_properties
        self.custom_template = custom_template

        self.definitions: List[Definition] = []
        self.searching_for_references: Dict[str, Set[ReferenceNode]] = defaultdict(set)
        self.__update_self()

    def __update_self(self):
        extra_generation_options["translate_properties"] = self.translate_properties
        extra_generation_options["translate_name_func"] = self.translate_type_name

    def load(self, json_schema_file):
        self.process(json.load(json_schema_file))
        self.module.after_processing(definitions=self.definitions)

    def get_model_dependencies(self, model: Definition) -> List[str]:
        deps = set()
        if isinstance(model, ObjectNode):
            for prop in model.properties:
                if not prop.definition.is_primitive:
                    deps.update(self.get_model_dependencies(prop.definition))
                    for a in prop.definition.ancestors():
                        deps.add(a.full_name_path)
                if (
                    isinstance(prop.definition, ListNode)
                    and not prop.definition.item_type.is_primitive
                ):
                    deps.update(self.get_model_dependencies(prop.definition.item_type))
        elif isinstance(model, ListNode) and not model.item_type.is_primitive:
            deps.update(self.get_model_dependencies(model.item_type))
        if isinstance(model, ReferenceNode) and model.parent is not None:
            deps.add(model.full_name_path)
        else:
            deps.discard(model.full_name_path)

        return list(deps)

    def process(self, json_schema):
        if "definitions" in json_schema:
            for _obj_name, _obj in json_schema["definitions"].items():
                model = self.definition_parser(_obj_name, _obj)
                self.definitions.append(model)

            # topological ordered dependencies
            g = networkx.DiGraph()
            models_map = {}
            for model in self.definitions:
                models_map[model.full_name_path] = model
                deps = self.get_model_dependencies(model)
                if not deps:
                    g.add_edge(model.full_name_path, "")
                for dep in deps:
                    g.add_edge(model.full_name_path, dep)

            self.definitions = []
            if self.generate_definitions:
                # use lexicographical topo sort so that the generation order is stable
                for model_name in networkx.lexicographical_topological_sort(g):
                    if model_name in models_map:
                        # insert to front so that the sorting is reversed
                        self.definitions.insert(0, models_map[model_name])

        # create root object if there are some properties in the root
        if "title" in json_schema:
            root_object_name = "".join(
                x for x in json_schema["title"].title() if x.isalpha()
            )
        else:
            root_object_name = "RootObject"
        if self.generate_root:
            root_model = self.definition_parser(root_object_name, json_schema)
            if root_model is None:
                root_model = ObjectNode(name=root_object_name)
            self.definitions.append(root_model)

    def attach_extra_bits(self, _obj, model: Definition):
        if "$ref" in _obj:
            self.attach_ref_value(_obj["$ref"], model)
        if (
            not isinstance(model, ReferenceNode) or model.value is not None
        ) and model.full_name_path in self.searching_for_references:
            for m in self.searching_for_references[model.full_name_path]:
                m.value = model
            del self.searching_for_references[model.full_name_path]

        if "description" in _obj:
            model.comment = _obj["description"]

        if (
            not model.is_primitive
            and not isinstance(model, ReferenceNode)
            and not isinstance(model, ListNode)
            and model.parent is not None
        ):
            model.parent.children.add(model)

    def attach_ref_value(self, ref: str, model: Definition):
        if isinstance(model, ReferenceNode) and model.value is None:
            # Only supporting "#/definitions/"
            ref_path = ref.split("/")[2:]
            ref = ".".join(ref_path)
            # Add to search list so that it is filled in at a later time
            self.searching_for_references[ref].add(model)

    def ref_lookup(self, ref) -> Optional[Definition]:
        if not ref.startswith("#/definitions/"):
            logger.warning(
                "References to anything other than #/definitions/ are not supported %s",
                ref,
            )
            return None

        ref_path = ref.split("/")[2:]
        ref = ".".join(ref_path)

        def search(m: Definition, ref):
            if m.full_name_path == ref:
                return m
            for mo in m.children:
                found = search(mo, ref)
                if found is not None:
                    return found
            return None

        for model in self.definitions:
            found = search(model, ref)
            if found is not None:
                return found
        return None

    def definition_parser(
        self, _obj_name, _obj, parent: Definition = None
    ) -> Optional[Definition]:
        model: Optional[Definition] = None

        if "$ref" in _obj:
            ref = self.ref_lookup(_obj["$ref"])
            model = ReferenceNode(parent=parent, name=_obj_name, value=ref)

        if "enum" in _obj:
            enum = {}
            for i, v in enumerate(_obj["enum"]):
                enum[v if "javaEnumNames" not in _obj else _obj["javaEnumNames"][i]] = v
            model = EnumNode(parent=parent, name=_obj_name, values=enum)
            model.value_type = self.type_parser(_obj, name=_obj_name)
            model.value_type.parent = model
            self.enum_used = True

        if "type" in _obj:
            if model is None:
                model = self.type_parser(_obj, name=_obj_name, parent=parent)
        else:
            if model is not None:
                self.attach_extra_bits(_obj, model)
            return model

        if "extends" in _obj and "$ref" in _obj["extends"]:
            if _obj["extends"]["$ref"].endswith(".json"):
                with open(_obj["extends"]["$ref"], "r") as f:
                    ref_file = json.load(f)
                    self.process(ref_file)
                    model.extends = self.ref_lookup(ref_file["title"])
            else:
                model.extends = self.ref_lookup(_obj["extends"]["$ref"])

        properties: List[Property] = []
        if "properties" in _obj:
            for _prop_name, _prop in _obj["properties"].items():
                property = Property(
                    name=_prop_name,
                    definition=self.definition_parser(_prop_name, _prop, parent=model),
                )
                property.definition.name = _prop_name
                properties.append(property)

                if "default" in _prop:
                    property.default = _prop["default"]

                if "description" in _prop:
                    property.comment = _prop["description"]

                if (
                    isinstance(property.definition, ListNode)
                    and not property.definition.item_type.is_primitive
                    and not isinstance(property.definition.item_type, ReferenceNode)
                ):
                    self.definition_parser(
                        _prop_name, _prop["items"], parent=property.definition
                    )

                if "format" in _prop:
                    property.format = _prop["format"]
                if (
                    isinstance(property.definition, ListNode)
                    and "items" in _prop
                    and isinstance(_prop["items"], list)
                ):
                    property.format = _prop["items"][0]["format"]

                _validations = {"required": False}
                validation_types = [
                    "maximum",
                    "minimum",
                    "maxItems",
                    "minItems",
                    "minLength",
                    "maxLength",
                    "pattern",
                ]
                for t in validation_types:
                    if t in _prop:
                        _validations[t] = _prop[t]
                    if isinstance(property.definition, ListNode) and "items" in _prop:
                        array_validation = _prop["items"]
                        if t in array_validation:
                            _validations[t] = array_validation[t]
                if "required" in _obj and _prop_name in _obj["required"]:
                    _validations["required"] = True
                property.validations = _validations

        if isinstance(model, ObjectNode):
            model.properties = properties
            model.properties_have_comments = any(p.comment for p in model.properties)
        self.attach_extra_bits(_obj, model)
        return model

    def type_parser(self, t, name, parent: Definition = None) -> Definition:
        model = None
        if "type" in t:
            if t["type"] == "array" and "items" in t:
                self.list_used = True
                model = ListNode(name=name, parent=parent)
                if isinstance(t["items"], list):
                    if "type" in t["items"][0]:
                        model.item_type = self.definition_parser(
                            name, t["items"][0], parent
                        )
                    elif (
                        "$ref" in t["items"][0]
                        or "oneOf" in t["items"][0]
                        and len(t["items"][0]["oneOf"]) == 1
                    ):
                        if "$ref" in t["items"][0]:
                            ref = t["items"][0]["$ref"]
                        else:
                            ref = t["items"][0]["oneOf"][0]["$ref"]
                        model.item_type = ReferenceNode(
                            value=self.ref_lookup(ref), name=name, parent=parent
                        )
                        self.attach_ref_value(ref, model.item_type)
                    if "format" in t["items"][0]:
                        model.item_format = t["items"][0]["format"]
                elif isinstance(t["items"], dict):
                    if "type" in t["items"]:
                        model.item_type = self.definition_parser(
                            name, t["items"], parent
                        )
                    elif (
                        "$ref" in t["items"]
                        or "oneOf" in t["items"]
                        and len(t["items"]["oneOf"]) == 1
                    ):
                        if "$ref" in t["items"]:
                            ref = t["items"]["$ref"]
                        else:
                            ref = t["items"]["oneOf"][0]["$ref"]
                        model.item_type = ReferenceNode(
                            value=self.ref_lookup(ref), name=name, parent=parent
                        )
                        self.attach_ref_value(ref, model.item_type)
                    if "format" in t["items"]:
                        model.item_format = t["items"]["format"]
            elif isinstance(t["type"], list):
                model = self.J2P_TYPES[t["type"][0]].__class__(name=name, parent=parent)
            elif t["type"]:
                model = self.J2P_TYPES[t["type"]].__class__(name=name, parent=parent)
                if (
                    isinstance(model, StringNode)
                    and "media" in t
                    and "binaryEncoding" in t["media"]
                    and t["media"]["binaryEncoding"] == "base64"
                ):
                    model.specific_type = bytes
        elif "$ref" in t:
            model = ReferenceNode(
                value=self.ref_lookup(t["$ref"]), name=name, parent=parent
            )
        elif "anyOf" in t or "allOf" in t or "oneOf" in t:
            model = ListNode(name=name, parent=parent, item_type=ObjectNode())
        # Do not attach extra bits to enum's inner types, otherwise any references to the enum could instead end up
        # with a reference to the inner type
        if "enum" not in t:
            self.attach_extra_bits(t, model)
        return model

    def write_file(self, filename):
        if not self.custom_template:
            self.check_names()
        template = self.custom_template or self.module.template()
        self.jinja.get_template(template).stream(
            models=self.definitions,
            enum_used=self.enum_used,
            list_used=self.list_used,
            **self.module.extra_jinja_inputs(),
        ).dump(filename)
        if hasattr(filename, "close"):
            filename.close()

    def maybe_translate_property_name(self, name):
        name = name.replace("-", "_").replace(".", "_")
        if not self.translate_properties:
            return name
        s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
        return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()

    def check_names(self):
        """Check every name the built-in templates emit as an identifier, for what is actually generated."""
        seen = set()

        def check_path(d: Definition):
            # A type is emitted by its full path, e.g. Parent._child
            for a in d.ancestors():
                if a.name is not None:
                    self.check_identifier(a.name, "Type or property")

        def visit(d: Optional[Definition]):
            if d is None or id(d) in seen:
                return
            seen.add(id(d))
            check_path(d)
            if isinstance(d, ReferenceNode):
                if d.value is not None:
                    check_path(d.value)
                return
            if getattr(d, "extends", None) is not None:
                check_path(d.extends)
            if isinstance(d, ListNode):
                visit(d.item_type)
            if isinstance(d, EnumNode):
                for name in d.values:
                    self.check_identifier(
                        name,
                        "Enum member",
                        enum_member=True,
                        hint=" Enum member names are the enum values, or javaEnumNames if given.",
                    )
            for p in getattr(d, "properties", None) or []:
                self.check_identifier(p.name, "Type or property")
                visit(p.definition)
            for c in d.children:
                visit(c)

        for model in self.definitions:
            visit(model)

    def check_identifier(self, name, kind: str, enum_member=False, hint=""):
        """
        Names from the schema are emitted as identifiers, so they must be identifiers in the target language.
        Type and property names have '-' and '.' replaced with '_' first; enum member names are used as-is.
        """
        candidate = str(name)
        if not enum_member:
            candidate = candidate.replace("-", "_").replace(".", "_")
        if not self.module.is_valid_identifier(candidate, enum_member=enum_member):
            raise ValueError(
                f"{kind} name {name!r} cannot be used as an identifier in the generated "
                f"{self.module.plugin_name()} code.{hint}"
            )

    def translate_type_name(self, name):
        name = name.replace("-", "_").replace(".", "_")
        return name

    def after_generation(self, filename=None):
        self.module.after_generation(filename=filename)

    def update_args(self, args):
        if "no_generate_from_definitions" in args:
            self.generate_definitions = args.no_generate_from_definitions
        if "no_generate_from_root_object" in args:
            self.generate_root = args.no_generate_from_root_object
        if "translate_properties" in args:
            self.translate_properties = args.translate_properties
        self.__update_self()
        self.module.set_args(args)


def init_parser():
    parser = argparse.ArgumentParser(
        description="Converts JSON Schema to Plain Old Python Object"
    )
    parser.add_argument(
        "json_schema_file",
        type=argparse.FileType("r", encoding="utf-8"),
        help="Path to JSON Schema file to load",
    )
    parser.add_argument(
        "-o",
        "--output-file",
        type=argparse.FileType("w", encoding="utf-8"),
        help="Path to file output",
        default="model.py",
    )
    parser.add_argument(
        "-jt",
        "--custom-template",
        help="Path to custom Jinja template file",
        default="",
    )
    parser.add_argument(
        "--no-generate-from-definitions",
        action="store_false",
        help='Don\'t generate classes from "definitions" section of the schema.',
        default=True,
    )
    parser.add_argument(
        "--no-generate-from-root-object",
        action="store_false",
        help="Don't generate classes from root of the schema.",
        default=True,
    )
    parser.add_argument(
        "-tp",
        "--translate-properties",
        action="store_true",
        help="Translate property names into snake_case.",
    )
    parser.add_argument(
        "-l",
        "--language",
        help="Which language to generate in. Use python, js, go, or enter in a Python module name to use a plugin",
        default="python",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="JSONSchema2PoPo2 v{}".format(__version__),
    )
    return parser


def main():
    parser = init_parser()
    rewritten_args = sys.argv.copy()
    rewritten_args.pop(0)  # Remove script path from args which argparse doesn't handle

    def remove_if_present(l, to_remove):
        try:
            l.remove(to_remove)
        except ValueError:
            pass

    # If a language option is chosen, then remove any option which should be handled by the subparser instead
    if "-l" in rewritten_args or "--language" in rewritten_args:
        remove_if_present(rewritten_args, "--version")
        remove_if_present(rewritten_args, "-h")
        remove_if_present(rewritten_args, "--help")

    args = parser.parse_known_args(args=rewritten_args)[0]

    loader = JsonSchema2Popo(
        language=args.language,
        custom_template=args.custom_template,
    )
    loader.module.command_line_parser(
        sub_parser=parser.add_argument_group(loader.module.plugin_name())
    )
    # Update version action to output the plugin's version (if there is a plugin)
    for action in parser._actions:
        if isinstance(action, argparse._VersionAction):
            action.version = action.version + " with {} plugin v{}".format(
                loader.module.plugin_name(), loader.module.plugin_version()
            )
            break

    args = parser.parse_args()
    loader.update_args(args)
    loader.load(args.json_schema_file)

    outfile = args.output_file
    loader.write_file(outfile)
    loader.after_generation(filename=outfile.name)


if __name__ == "__main__":
    main()
