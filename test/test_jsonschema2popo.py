import importlib.util
import json
import os
import subprocess
import sys
import unittest
from types import ModuleType

import mypy.main
from mypy.fscache import FileSystemCache

from jsonschema2popo import jsonschema2popo
from jsonschema2popo.jsonschema2popo import (
    format_python_file,
    format_js_file,
    format_go_file,
)

DEFINITIONS_BASIC_GENERATION = """{
            "definitions": {
                "ABcd": {
                    "type": "object",
                    "properties": {
                        "Int": {
                            "type": "integer"
                        },
                        "Float": {
                            "type": "number"
                        },
                        "ListInt": {
                            "type": "array",
                            "items": {
                                "type": "integer"
                            }
                        },
                        "String": {
                            "type": "string"
                        },
                        "Object": {
                            "type": "object"
                        }
                    }
                }
            }
        }"""


def import_file(file_path: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location("", file_path)
    foo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(foo)
    return foo


class JsonSchema2Popo(unittest.TestCase):
    def tearDown(self):
        try:
            self.mypy_test()
            self.js_test()
            self.go_test()
        finally:
            os.remove(self.test_file)
            os.remove(self.test_file_js)
            os.remove(self.test_file_go)

    def setUp(self):
        os.chdir(os.path.dirname(os.path.realpath(__file__)))

    def id(self) -> str:
        return (
            os.path.basename(os.path.realpath(__file__)).replace(".py", ".")
            + self._testMethodName
        )

    def js_test(self):
        self.assertEqual(
            0, os.system(f"node test_js.js {self.id()} {self.test_file_js}")
        )

    def go_test(self):
        proc = subprocess.run(
            args=["go", "run", "-tags=" + self.id(), "test_go.go"],
            capture_output=True,
            env={**os.environ},
        )
        print(proc.stderr.decode("utf-8"))
        print(proc.stdout.decode("utf-8"))
        self.assertEqual(0, proc.returncode)

    def mypy_test(self):
        """
        Make sure that the generated python typechecks successfully
        """
        messages = []

        def flush_errors(new_messages, serious):
            messages.extend(new_messages)

        options = mypy.main.Options()
        options.allow_untyped_globals = True
        mypy.main.build.build(
            [mypy.main.BuildSource(path=self.test_file, module="")],
            options,
            None,
            flush_errors,
            FileSystemCache(),
            sys.stdout,
            sys.stderr,
        )
        for m in messages:
            print(m)
        self.assertFalse(messages)

    def import_test_file(self):
        return import_file(self.test_file)

    def generate_files(self, schema, **kwargs):
        self.test_file = f"generated/{self.id()}.py"
        self.test_file_js = f"generated/{self.id()}.js"
        try:
            os.makedirs("generated", exist_ok=True)
        except:
            pass
        self.test_file_go = f"generated/{self.id()}.go"

        loader = jsonschema2popo.JsonSchema2Popo(
            use_types=True,
            constructor_type_check=True,
            use_slots=True,
            language="python",
            **kwargs,
        )
        loader.process(json.loads(schema))
        loader.write_file(self.test_file)
        format_python_file(self.test_file)

        loader = jsonschema2popo.JsonSchema2Popo(
            use_types=True,
            constructor_type_check=True,
            use_slots=True,
            language="js",
            **kwargs,
        )
        loader.process(json.loads(schema))
        loader.write_file(self.test_file_js)
        format_js_file(self.test_file_js)

        loader = jsonschema2popo.JsonSchema2Popo(
            language="go",
            package_name="generated",
            **kwargs,
        )
        loader.process(json.loads(schema))
        loader.write_file(self.test_file_go)
        format_go_file(self.test_file_go)

    def test_root_basic_generation(self):
        self.generate_files(
            """{
            "title": "ABcd",
            "type": "object",
            "properties": {
                "Int": {
                    "type": "integer"
                },
                "Float": {
                    "type": "number"
                },
                "ListInt": {
                    "type": "array",
                    "items": {
                        "type": "integer"
                    }
                },
                "String": {
                    "type": "string"
                },
                "Object": {
                    "type": "object"
                },
                "StringEnum": {
                    "type": "string",
                    "enum": ["A", "b", "c"]
                }
            }
        }"""
        )

        foo = self.import_test_file()

        a = foo.Abcd.from_dict(
            {
                "Int": 0,
                "Float": 0.1,
                "ListInt": [0, 1, 2],
                "String": "ABC",
                "Object": {"A": "X"},
                "StringEnum": "A",
            }
        )
        self.assertEqual(a.Int, 0)
        self.assertEqual(a.Float, 0.1)
        self.assertEqual(a.ListInt, [0, 1, 2])
        self.assertEqual(a.String, "ABC")
        self.assertEqual(a.Object, {"A": "X"})
        self.assertEqual(a.StringEnum.value, "A")

        self.assertRaisesRegex(
            TypeError, "Int must be int", lambda: foo.Abcd.from_dict({"Int": 0.1})
        )
        self.assertRaisesRegex(
            TypeError,
            "Float must be float",
            lambda: foo.Abcd.from_dict({"Float": True}),
        )
        self.assertRaisesRegex(
            TypeError,
            "'bool' object is not iterable",
            lambda: foo.Abcd.from_dict({"ListInt": True}),
        )
        self.assertRaisesRegex(
            TypeError,
            "ListInt list values must be int",
            lambda: foo.Abcd.from_dict({"ListInt": [0.2]}),
        )
        self.assertRaisesRegex(
            TypeError, "String must be str", lambda: foo.Abcd.from_dict({"String": 0})
        )
        self.assertRaisesRegex(
            ValueError,
            "is not a valid .*_StringEnum",
            lambda: foo.Abcd._StringEnum.from_dict({"String": 0}),
        )

    def test_root_string_enum(self):
        self.generate_files(
            """{
            "title": "ABcd",
            "type": "string",
            "enum": ["A", "B", "C"]
        }"""
        )

        foo = self.import_test_file()
        self.assertIsInstance(foo.Abcd.A, foo.Abcd)
        self.assertEqual(foo.Abcd.A.value, "A")
        self.assertEqual(foo.Abcd.B.value, "B")
        self.assertEqual(foo.Abcd.C.value, "C")

    def test_root_integer_enum(self):
        self.generate_files(
            """{
            "title": "ABcd",
            "type": "integer",
            "enum": [0, 1, 2, 99],
            "javaEnumNames": ["A", "B", "C", "D"]
        }"""
        )

        foo = self.import_test_file()
        self.assertIsInstance(foo.Abcd.A, foo.Abcd)
        self.assertEqual(foo.Abcd.A.value, 0)
        self.assertEqual(foo.Abcd.B.value, 1)
        self.assertEqual(foo.Abcd.C.value, 2)
        self.assertEqual(foo.Abcd.D.value, 99)

    def test_root_nested_objects(self):
        self.generate_files(
            """{
            "title": "ABcd",
            "type": "object",
            "properties": {
                "Child1": {
                    "type": "object",
                    "properties": {
                        "IntVal": {
                            "type": "integer"
                        },
                        "Child2": {
                            "type": "object",
                            "properties": {
                                "IntVal": {
                                    "type": "integer"
                                },
                                "ListVal": {
                                    "type": "array",
                                    "items": {
                                        "type": "string"
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }"""
        )

        foo = self.import_test_file()
        foo.Abcd(foo.Abcd._Child1(0, foo.Abcd._Child1._Child2(0, ["0"])))

        self.assertRaisesRegex(
            TypeError, "Child1 must be Abcd._Child1", lambda: foo.Abcd(0)
        )
        self.assertRaisesRegex(
            TypeError,
            "Child2 must be Abcd._Child1._Child2",
            lambda: foo.Abcd._Child1(0, 0),
        )

    def test_definitions_basic_generation(self):
        self.generate_files(DEFINITIONS_BASIC_GENERATION)

        foo = self.import_test_file()
        foo.ABcd()
        foo.RootObject()

    def test_definitions_basic_generation_no_generation(self):
        self.generate_files(DEFINITIONS_BASIC_GENERATION, generate_definitions=False)

        foo = self.import_test_file()
        self.assertRaisesRegex(
            AttributeError, "module '' has no attribute 'ABcd'", lambda: foo.ABcd()
        )
        foo.RootObject()

    def test_definitions_with_refs(self):
        self.generate_files(
            """{
            "definitions": {
                "ABcd": {
                    "type": "object",
                    "properties": {
                        "Child1": {
                            "type": "integer"
                        },
                        "Child2": {
                            "type": "string"
                        }
                    }
                },
                "SubRef": {
                    "type": "object",
                    "properties": {
                        "ChildA": {
                            "$ref": "#/definitions/ABcd"
                        }
                    }
                },
                "DirectRef": {
                    "$ref": "#/definitions/ABcd"
                }
            }
        }"""
        )

        foo = self.import_test_file()
        foo.ABcd(Child1=0, Child2="2")
        foo.SubRef(ChildA=foo.ABcd())
        foo.DirectRef(Child1=0, Child2="2")

    def test_definitions_with_nested_refs(self):
        self.generate_files(
            """{
            "definitions": {
                "ABcd": {
                    "type": "object",
                    "properties": {
                        "Child1": {
                            "type": "object",
                            "properties": {
                                "IntVal": {
                                    "type": "integer"
                                },
                                "Child2": {
                                    "type": "object",
                                    "properties": {
                                        "IntVal": {
                                            "type": "integer"
                                        },
                                        "ListVal": {
                                            "type": "array",
                                            "items": {
                                                "type": "string"
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "Ref": {
                    "$ref": "#/definitions/ABcd/Child1/Child2"
                },
                "AAAA": {
                    "type": "object",
                    "properties": {
                        "X": {
                            "type": "integer"
                        },
                        "YRef": {
                            "$ref": "#/definitions/ABcd/Child1/Child2"
                        }
                    }
                }
            }
        }"""
        )

        foo = self.import_test_file()
        foo.ABcd(
            Child1=foo.ABcd._Child1(
                IntVal=0, Child2=foo.ABcd._Child1._Child2(IntVal=0, ListVal=["1"])
            )
        )
        foo.Ref(IntVal=0, ListVal=["1"])
        foo.AAAA(X=0, YRef=foo.ABcd._Child1._Child2(IntVal=0, ListVal=["1"]))

    def test_list_definitions_with_nested_object(self):
        self.generate_files(
            """{
    "definitions": {
        "A": {
            "type": "object",
            "properties": {
                "sub1": {
                    "type": "array",
                    "items": {
                        "type": "object", 
                        "properties": {
                            "prop1": {
                                "type": "integer"
                            },
                            "prop2": {
                                "type": "number"
                            }
                        }
                    }
                }
            }
        }
    }
}"""
        )

        foo = self.import_test_file()
        foo.A(sub1=[foo.A._sub1(prop1=0, prop2=1.2)])

    def test_list_definitions_with_ref(self):
        self.generate_files(
            """{
    "definitions": {
        "A": {
            "type": "object",
            "properties": {
                "prop1": {
                    "type": "array",
                    "items": {
                        "$ref": "#/definitions/B"
                    }
                }
            }
        },
        "B": {
            "type": "object",
            "properties": {
                "prop1": {
                    "type": "integer"
                }
            }
        }
    }
}"""
        )

        foo = self.import_test_file()
        foo.A(prop1=[foo.B(prop1=0)])

    def test_bytes_type(self):
        self.generate_files(
            """{
    "definitions": {
        "B": {
            "type": "object",
            "properties": {
                "prop1": {
                    "type": "string",
                    "media": {
                        "binaryEncoding": "base64"
                    }
                }
            }
        }
    }
}"""
        )

        foo = self.import_test_file()
        foo.B(prop1=bytes(100 for _ in range(1024)))


if __name__ == "__main__":
    unittest.main()
