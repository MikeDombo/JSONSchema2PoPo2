import argparse
import os
from typing import Dict, Callable, Any

from jsonschema2popo import version
from jsonschema2popo.classes import CodeGenPlugin
from jsonschema2popo.python.python import Python


class Go(CodeGenPlugin):
    def plugin_name(self) -> str:
        return "Go"

    def plugin_version(self) -> str:
        return version

    def command_line_parser(self, sub_parser: argparse.ArgumentParser) -> None:
        sub_parser.add_argument(
            "--package-name",
            help="Package name for generated code",
            default="generated",
        )

    def set_args(self, args):
        self.package_name = args.package_name if "package_name" in args else None

    def extra_jinja_inputs(self) -> Dict[str, Any]:
        return {"package_name": self.package_name}

    def template(self) -> str:
        return "go_struct.tmpl"

    def jinja_globals(self) -> Dict[str, Callable]:
        return {"python_type": Python.python_type}

    def template_search_path(self) -> str:
        return os.path.dirname(os.path.abspath(__file__))

    def after_generation(self, filename=None):
        Go.format_go_file(filename=filename)

    @staticmethod
    def format_go_file(filename):
        os.system("go fmt " + filename)
