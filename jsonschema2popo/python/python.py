import argparse
import os
import pathlib
from typing import Union, Dict, Callable, Any

from jsonschema2popo import version
from jsonschema2popo.classes import Definition, ListNode, CodeGenPlugin
from jsonschema2popo.jsonschema2popo import string_to_type


class Python(CodeGenPlugin):
    def plugin_name(self) -> str:
        return "Python"

    def plugin_version(self) -> str:
        return version

    def command_line_parser(self, sub_parser: argparse.ArgumentParser) -> None:
        sub_parser.add_argument(
            "-t", "--use-types", action="store_true", help="Add typings"
        )
        sub_parser.add_argument(
            "-ct",
            "--constructor-type-check",
            action="store_true",
            help="Validate input types in constructor",
        )
        sub_parser.add_argument(
            "-s",
            "--use_slots",
            action="store_true",
            help="Generate class with __slots__",
        )

    def set_args(self, args):
        self.use_slots = args.use_slots if "use_slots" in args else False
        self.constructor_type_check = (
            args.constructor_type_check if "constructor_type_check" in args else None
        )
        self.use_types = args.use_types if "use_types" in args else False

    def extra_jinja_inputs(self) -> Dict[str, Any]:
        return {
            "use_slots": self.use_slots,
            "constructor_type_check": self.constructor_type_check,
            "use_types": self.use_types,
        }

    def template(self) -> str:
        return "python_class.tmpl"

    def jinja_globals(self) -> Dict[str, Callable]:
        return {"python_type": Python.python_type}

    def template_search_path(self) -> str:
        return os.path.dirname(os.path.abspath(__file__))

    def after_generation(self, filename=None):
        Python.format_python_file(filename=filename)

    @staticmethod
    def python_type(v: Union[Definition, str], relative_to: Definition = None) -> str:
        if isinstance(v, Definition):
            if isinstance(v, ListNode):
                return Python.python_type(v.type)
            elif v.is_primitive:
                return Python.python_type(v.string_type)
            else:
                return Python.python_type(
                    v.full_name_python_path(relative_to=relative_to)
                )
        else:
            return string_to_type(v)

    @staticmethod
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
