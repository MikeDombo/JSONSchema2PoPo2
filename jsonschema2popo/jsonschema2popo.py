#!/usr/bin/env python
import logging
import os
import argparse
import json
import re
import pathlib
from collections import defaultdict
from typing import List, Optional, Dict, Union, Set

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
)
from . import __version__

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

logger = logging.getLogger("main")

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


def python_type(v: Union[Definition, str], relative_to: Definition = None) -> str:
    if isinstance(v, Definition):
        if isinstance(v, ListNode):
            return python_type(v.type)
        elif v.is_primitive:
            return python_type(v.string_type)
        else:
            return python_type(v.full_name_python_path(relative_to=relative_to))
    else:
        return string_to_type(v)


class JsonSchema2Popo:
    """Converts a JSON Schema to a Plain Old Python Object class"""

    PYTHON_CLASS_TEMPLATE_FNAME = "python_class.tmpl"
    JS_CLASS_TEMPLATE_FNAME = "js_class.tmpl"
    GO_STRUCT_TEMPLATE_FNAME = "go_struct.tmpl"

    TEMPLATES = {
        "python": PYTHON_CLASS_TEMPLATE_FNAME,
        "js": JS_CLASS_TEMPLATE_FNAME,
        "go": GO_STRUCT_TEMPLATE_FNAME,
    }

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
        use_types=False,
        constructor_type_check=False,
        use_slots=False,
        generate_definitions=True,
        generate_root=True,
        translate_properties=False,
        language="python",
        namespace_path="",
        package_name="",
        custom_template="",
    ):
        self.list_used = False
        self.enum_used = False

        search_path = SCRIPT_DIR if not custom_template else os.getcwd()
        self.jinja = Environment(
            loader=FileSystemLoader(searchpath=search_path), trim_blocks=True
        )
        self.jinja.filters["regex_replace"] = lambda s, find, replace: re.sub(
            find, replace, s
        )
        self.jinja.globals["python_type"] = python_type
        self.jinja.globals["jsdoc_type"] = self.jsdoc_type
        self.jinja.globals["trn"] = self.get_prop_name
        self.jinja.filters["trn"] = self.get_prop_name
        self.use_types = use_types
        self.use_slots = use_slots
        self.constructor_type_check = constructor_type_check
        self.generate_root = generate_root
        self.generate_definitions = generate_definitions
        self.translate_properties = translate_properties
        self.language = language
        self.namespace_path = namespace_path
        self.package_name = package_name
        self.custom_template = custom_template

        self.definitions: List[Definition] = []
        self.searching_for_references: Dict[str, Set[ReferenceNode]] = defaultdict(set)

        extra_generation_options["translate_properties"] = self.translate_properties

    def load(self, json_schema_file):
        self.process(json.load(json_schema_file))

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
        if model.full_name_path in self.searching_for_references:
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

                _format = None
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
        self.attach_extra_bits(t, model)
        return model

    def write_file(self, filename):
        template = self.custom_template or self.TEMPLATES[self.language]
        self.jinja.get_template(template).stream(
            models=self.definitions,
            use_types=self.use_types,
            constructor_type_check=self.constructor_type_check,
            enum_used=self.enum_used,
            list_used=self.list_used,
            use_slots=self.use_slots,
            namespace_path=self.namespace_path,
            package_name=self.package_name,
        ).dump(filename)
        if hasattr(filename, "close"):
            filename.close()

    def get_prop_name(self, name):
        if not self.translate_properties:
            return name
        s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
        return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()

    def jsdoc_type(
        self, v: Union[Definition, str], relative_to: Definition = None, was_ref=False
    ) -> str:
        if isinstance(v, Definition):
            if isinstance(v, ListNode):
                return self.jsdoc_type(v.type)
            elif v.is_primitive:
                return self.jsdoc_type(v.string_type)
            elif isinstance(v, ReferenceNode) and v.parent is not None:
                return self.jsdoc_type(v.value, relative_to=v.value, was_ref=True)
            else:
                return (
                    (v.parent.full_name_python_path(relative_to=v) + "~")
                    if v.parent and not was_ref
                    else ""
                ) + v.full_name_python_path(relative_to=None)
        else:
            return string_to_type(v)


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
    parser.add_argument("-t", "--use-types", action="store_true", help="Add typings")
    parser.add_argument(
        "-ct",
        "--constructor-type-check",
        action="store_true",
        help="Validate input types in constructor",
    )
    parser.add_argument(
        "-s", "--use_slots", action="store_true", help="Generate class with __slots__."
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
        choices=JsonSchema2Popo.TEMPLATES.keys(),
        help="Which language to generate in",
        default="python",
    )
    parser.add_argument(
        "--namespace-path",
        help="Namespace path to be prepended to the @memberOf for JSDoc (only used for JS)",
    )
    parser.add_argument(
        "--package-name",
        help="Package name for generated code (only used for Go)",
        default="generated",
    )
    parser.add_argument(
        "--version", action="version", version="%(prog)s v{}".format(__version__)
    )
    return parser


def format_python_file(filename):
    try:
        import black

        black.format_file_in_place(
            pathlib.Path(filename).absolute(),
            fast=True,
            mode=black.FileMode(
                line_length=88, target_versions={black.TargetVersion.PY33}
            ),
            write_back=black.WriteBack.YES,
        )
    except:
        pass


def format_js_file(filename):
    try:
        import jsbeautifier

        format_opts = jsbeautifier.default_options()
        format_opts.end_with_newline = True
        format_opts.preserve_newlines = True
        format_opts.max_preserve_newlines = 2
        format_opts.wrap_line_length = 120

        with open(filename, "r") as fr:
            file = fr.read()
            with open(filename, "w") as f:
                f.write(jsbeautifier.beautify(file, opts=format_opts))
    except:
        pass


def format_go_file(filename):
    os.system("go fmt " + filename)


def main():
    parser = init_parser()
    args = parser.parse_args()

    loader = JsonSchema2Popo(
        use_types=args.use_types,
        constructor_type_check=args.constructor_type_check,
        use_slots=args.use_slots,
        generate_definitions=args.no_generate_from_definitions,
        generate_root=args.no_generate_from_root_object,
        translate_properties=args.translate_properties,
        language=args.language,
        namespace_path=args.namespace_path,
        package_name=args.package_name,
        custom_template=args.custom_template,
    )
    loader.load(args.json_schema_file)

    outfile = args.output_file
    loader.write_file(outfile)
    if args.language == "python":
        format_python_file(outfile.name)
    elif args.language == "js":
        format_js_file(outfile.name)
    elif args.language == "go":
        format_go_file(outfile.name)


if __name__ == "__main__":
    main()
