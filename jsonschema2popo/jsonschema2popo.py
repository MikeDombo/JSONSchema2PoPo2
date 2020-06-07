#!/usr/bin/env python

import os
import argparse
import json
import re
import pathlib

import networkx
from jinja2 import Environment, FileSystemLoader

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


class JsonSchema2Popo:
    """Converts a JSON Schema to a Plain Old Python Object class"""

    PYTHON_CLASS_TEMPLATE_FNAME = "python_class.tmpl"
    JS_CLASS_TEMPLATE_FNAME = "js_class.tmpl"

    TEMPLATES = {"python": PYTHON_CLASS_TEMPLATE_FNAME, "js": JS_CLASS_TEMPLATE_FNAME}

    J2P_TYPES = {
        "string": str,
        "integer": int,
        "number": float,
        "object": type,
        "array": list,
        "boolean": bool,
        "null": None,
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
    ):
        self.list_used = False
        self.enum_used = False
        self.jinja = Environment(
            loader=FileSystemLoader(searchpath=SCRIPT_DIR), trim_blocks=True
        )
        self.jinja.filters["regex_replace"] = lambda s, find, replace: re.sub(
            find, replace, s
        )
        self.use_types = use_types
        self.use_slots = use_slots
        self.constructor_type_check = constructor_type_check
        self.generate_root = generate_root
        self.generate_definitions = generate_definitions
        self.translate_properties = translate_properties
        self.language = language
        self.namespace_path = namespace_path

        self.definitions = []

    def load(self, json_schema_file):
        self.process(json.load(json_schema_file))

    def get_model_dependencies(self, model):
        deps = set()
        for prop in model["properties"]:
            if prop["_type"]["type"] not in self.J2P_TYPES.values():
                deps.add(prop["_type"]["type"])
            if prop["_type"]["subtype"] not in self.J2P_TYPES.values():
                deps.add(prop["_type"]["subtype"])
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
                models_map[model["name"]] = model
                deps = self.get_model_dependencies(model)
                if not deps:
                    g.add_edge(model["name"], "")
                for dep in deps:
                    g.add_edge(model["name"], dep)

            self.definitions = []
            if self.generate_definitions:
                for model_name in networkx.topological_sort(g):
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
            self.definitions.append(root_model)

    def definition_parser(self, _obj_name, _obj, sub_model=""):
        model = {"name": _obj_name, "subModels": [], "parent": sub_model}

        if "description" in _obj:
            model["comment"] = _obj["description"]

        join_str = "._"
        if self.translate_properties:
            join_str = "."
        sub_prefix = "_"
        if self.translate_properties:
            sub_prefix = ""

        if "$ref" in _obj and _obj["$ref"].startswith("#/definitions/"):
            # References defined at a top level should be copied from what it is referencing
            ref_path = _obj["$ref"].split("/")[2:]
            ref = join_str.join(ref_path)

            for model in self.definitions:
                if model["name"] in ref_path:
                    subModels = model["subModels"]
                    built_path = model["name"]

                    i = 0
                    while i < len(subModels) and subModels:
                        subModel = subModels[i]
                        i = i + 1

                        if "subModels" in subModel:
                            if self.strip_sub_prefix(subModel["name"]) in ref_path:
                                built_path = built_path + "." + subModel["name"]
                                subModels = subModel["subModels"]
                                model = subModel
                                i = 0
                        if built_path == ref:
                            break

                    if ref_path[len(ref_path) - 1] == self.strip_sub_prefix(
                        model["name"]
                    ):
                        model = model.copy()
                        model["name"] = _obj_name
                        model["parent"] = sub_model
                        return model

            print("Unable to find object refs for ", "/".join(ref_path))

        if "type" in _obj:
            model["type"] = self.type_parser(_obj)
            model["text_type"] = _obj["type"]

        if "enum" in _obj:
            enum = {}
            for i, v in enumerate(_obj["enum"]):
                enum[v if "javaEnumNames" not in _obj else _obj["javaEnumNames"][i]] = v
            model["enum"] = enum
            self.enum_used = True

        if "extends" in _obj and "$ref" in _obj["extends"]:
            if _obj["extends"]["$ref"].endswith(".json"):
                with open(_obj["extends"]["$ref"], "r") as f:
                    ref_file = json.load(f)
                    self.process(ref_file)
                    model["extends"] = ref_file["title"]
            else:
                ref_path = _obj["extends"]["$ref"].split("/")[2:]
                ref = join_str.join(ref_path)
                if sub_model and sub_model.endswith(_obj_name):
                    subs = sub_model.split(".")[-1]
                    ref = ref[len(sub_model) - len(subs) :]
                model["extends"] = ref

        model["properties"] = []
        if "properties" in _obj:
            for _prop_name, _prop in _obj["properties"].items():
                _type = self.type_parser(_prop)
                _default = None
                _comment = None
                if "default" in _prop:
                    _default = _type["type"](_prop["default"])
                    if _type["type"] == str:
                        _default = "'{}'".format(_default)

                if "description" in _prop:
                    _comment = _prop["description"]

                read_list = self.definitions[:]
                read_list.append(model)

                def find_parent(path, model):
                    return [
                        (path + "." + m["name"], find_parent(path + "." + m["name"], m))
                        for m in model["subModels"]
                        if "subModels" in m
                    ]

                potential_paths = list(
                    JsonSchema2Popo.flatten(
                        [find_parent(model["name"], model) for model in read_list]
                    )
                )

                parent_name = sub_model + join_str + _prop_name
                if not sub_model:
                    parent_name = _obj_name + join_str + _prop_name
                    for path in potential_paths:
                        if path.endswith(parent_name) and len(path) > len(parent_name):
                            parent_name = path

                if _type["type"] == list and _type["subtype"] == type:
                    _type["subtype"] = sub_prefix + _prop_name
                    _type["parent"] = parent_name
                    model["subModels"].append(
                        self.definition_parser(
                            sub_prefix + _prop_name,
                            _prop["items"],
                            sub_model=parent_name,
                        )
                    )

                if "$ref" in _prop and _prop["$ref"].startswith("#/definitions/"):
                    # Properties with references should reference the existing defined classes
                    ref = _prop["$ref"].split("/")[2:]
                    _type = {"type": join_str.join(ref), "subtype": None}

                if ("type" in _prop and _prop["type"] == "object") or "enum" in _prop:
                    _type = {
                        "type": sub_prefix + _prop_name,
                        "subtype": None,
                        "parent": parent_name,
                    }

                    sub_mod = self.definition_parser(
                        sub_prefix + _prop_name, _prop, sub_model=parent_name
                    )

                    # Only generate sub models when the sub model actually has properties, otherwise treat is as
                    # a dict, which is what an object is to JSON
                    if sub_mod["properties"]:
                        model["subModels"].append(sub_mod)
                    else:
                        _type = {
                            "type": dict,
                            "subtype": None,
                        }

                    if "enum" in _prop:
                        self.enum_used = True

                _format = None
                if "format" in _prop:
                    _format = _prop["format"]
                if (
                    _type["type"] == list
                    and "items" in _prop
                    and isinstance(_prop["items"], list)
                ):
                    _format = _prop["items"][0]["format"]

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
                    if _type["type"] == list and "items" in _prop:
                        array_validation = _prop["items"]
                        if t in array_validation:
                            _validations[t] = array_validation[t]
                if "required" in _obj and _prop_name in _obj["required"]:
                    _validations["required"] = True

                prop = {
                    "_name": self.get_prop_name(_prop_name),
                    "_original_name": _prop_name,
                    "_type": _type,
                    "_default": _default,
                    "_format": _format,
                    "_comment": _comment,
                    "_validations": _validations,
                }
                model["properties"].append(prop)
        model["propertiesHaveComment"] = any(p["_comment"] for p in model["properties"])
        return model

    def type_parser(self, t):
        _type = None
        _subtype = None
        if "type" in t:
            if t["type"] == "array" and "items" in t:
                self.list_used = True
                _type = self.J2P_TYPES[t["type"]]
                if isinstance(t["items"], list):
                    if "type" in t["items"][0]:
                        _subtype = self.J2P_TYPES[t["items"][0]["type"]]
                    elif (
                        "$ref" in t["items"][0]
                        or "oneOf" in t["items"][0]
                        and len(t["items"][0]["oneOf"]) == 1
                    ):
                        if "$ref" in t["items"][0]:
                            ref = t["items"][0]["$ref"]
                        else:
                            ref = t["items"][0]["oneOf"][0]["$ref"]
                        _subtype = ref.split("/")[-1]
                elif isinstance(t["items"], dict):
                    if "type" in t["items"]:
                        _subtype = self.J2P_TYPES[t["items"]["type"]]
                    elif (
                        "$ref" in t["items"]
                        or "oneOf" in t["items"]
                        and len(t["items"]["oneOf"]) == 1
                    ):
                        if "$ref" in t["items"]:
                            ref = t["items"]["$ref"]
                        else:
                            ref = t["items"]["oneOf"][0]["$ref"]
                        _subtype = ref.split("/")[-1]
            elif isinstance(t["type"], list):
                _type = self.J2P_TYPES[t["type"][0]]
            elif t["type"]:
                _type = self.J2P_TYPES[t["type"]]
                if (
                    _type == str
                    and "media" in t
                    and "binaryEncoding" in t["media"]
                    and t["media"]["binaryEncoding"] == "base64"
                ):
                    _type = bytes
        elif "$ref" in t:
            _type = t["$ref"].split("/")[-1]
        elif "anyOf" in t or "allOf" in t or "oneOf" in t:
            _type = list
        return {"type": _type, "subtype": _subtype}

    def write_file(self, filename):
        self.jinja.get_template(self.TEMPLATES[self.language]).stream(
            models=self.definitions,
            use_types=self.use_types,
            constructor_type_check=self.constructor_type_check,
            enum_used=self.enum_used,
            list_used=self.list_used,
            use_slots=self.use_slots,
            namespace_path=self.namespace_path,
        ).dump(filename)
        if hasattr(filename, "close"):
            filename.close()

    def get_prop_name(self, name):
        if not self.translate_properties:
            return name
        s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
        return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()

    def strip_sub_prefix(self, name):
        if self.translate_properties:
            return name
        return name.lstrip("_")


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
    )
    loader.load(args.json_schema_file)

    outfile = args.output_file
    loader.write_file(outfile)
    if args.language == "python":
        format_python_file(outfile.name)
    elif args.language == "js":
        format_js_file(outfile.name)


if __name__ == "__main__":
    main()
