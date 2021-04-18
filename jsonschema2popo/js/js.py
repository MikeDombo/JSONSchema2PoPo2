import argparse
import os
from typing import Union, Dict, Callable, Any

from jsonschema2popo import version
from jsonschema2popo.classes import Definition, ListNode, ReferenceNode, CodeGenPlugin
from jsonschema2popo.jsonschema2popo import string_to_type
from jsonschema2popo.python.python import Python


class JS(CodeGenPlugin):
    def plugin_name(self) -> str:
        return "JavaScript"

    def plugin_version(self) -> str:
        return version

    def command_line_parser(self, sub_parser: argparse.ArgumentParser) -> None:
        sub_parser.add_argument(
            "-ct",
            "--constructor-type-check",
            action="store_true",
            help="Validate input types in constructor",
        )
        sub_parser.add_argument(
            "--namespace-path",
            help="Namespace path to be prepended to the @memberOf for JSDoc",
        )

    def set_args(self, args):
        self.constructor_type_check = (
            args.constructor_type_check if "constructor_type_check" in args else None
        )
        self.namespace_path = args.namespace_path if "namespace_path" in args else None

    def extra_jinja_inputs(self) -> Dict[str, Any]:
        return {
            "constructor_type_check": self.constructor_type_check,
            "namespace_path": self.namespace_path,
        }

    def template(self) -> str:
        return "js_class.tmpl"

    def jinja_globals(self) -> Dict[str, Callable]:
        return {"jsdoc_type": self.jsdoc_type, "python_type": Python.python_type}

    def template_search_path(self) -> str:
        return os.path.dirname(os.path.abspath(__file__))

    def after_generation(self, filename=None):
        JS.format_js_file(filename=filename)

    def jsdoc_type(
        self,
        v: Union[Definition, str],
        relative_to: Definition = None,
        was_ref=False,
        with_namespace=False,
    ) -> str:
        if isinstance(v, Definition):
            if isinstance(v, ListNode):
                return self.jsdoc_type(v.type, with_namespace=with_namespace)
            elif v.is_primitive:
                return self.jsdoc_type(v.string_type, with_namespace=with_namespace)
            elif isinstance(v, ReferenceNode) and v.parent is not None:
                return self.jsdoc_type(
                    v.value,
                    relative_to=v.value,
                    was_ref=True,
                    with_namespace=with_namespace,
                )
            else:
                return (
                    (
                        self.namespace_path + "."
                        if self.namespace_path and with_namespace
                        else ""
                    )
                    + (
                        (v.parent.full_name_python_path(relative_to=v) + "~")
                        if v.parent and not was_ref
                        else ""
                    )
                    + v.full_name_python_path(relative_to=None)
                )
        else:
            return string_to_type(v)

    @staticmethod
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
