import argparse
import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from types import ModuleType

import mypy.main
from mypy.fscache import FileSystemCache

from jsonschema2popo import jsonschema2popo
from jsonschema2popo.go.go import Go
from jsonschema2popo.js.js import JS
from jsonschema2popo.python.python import Python

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


# Quotes, backslashes, comment/docstring terminators, a regex delimiter and a newline: anything that
# could end a literal or comment in the generated Python, JS or Go. Must match test_js.js and go/special_values.go.
TRICKY = 'a\'b"c\\d */ """ /e\nf'


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
            pass

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

        def flush_errors(*args):
            # mypy >= 0.990 passes (filename, new_messages, serious); older passes (new_messages, serious)
            messages.extend(args[-2])

        options = mypy.main.Options()
        options.allow_untyped_globals = True
        # Generated constructors use `x: T = None`; newer mypy rejects that by default
        options.implicit_optional = True
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
            language="python",
            **kwargs,
        )
        loader.update_args(
            argparse.Namespace(
                use_types=True,
                constructor_type_check=True,
                use_slots=True,
            )
        )
        loader.process(json.loads(schema))
        loader.write_file(self.test_file)
        Python.format_python_file(self.test_file)

        loader = jsonschema2popo.JsonSchema2Popo(
            language="js",
            **kwargs,
        )
        loader.update_args(argparse.Namespace(constructor_type_check=True))
        loader.process(json.loads(schema))
        loader.write_file(self.test_file_js)
        JS.format_js_file(self.test_file_js)

        loader = jsonschema2popo.JsonSchema2Popo(
            language="go",
            **kwargs,
        )
        loader.update_args(
            argparse.Namespace(
                package_name="generated",
            )
        )
        loader.process(json.loads(schema))
        loader.write_file(self.test_file_go)
        Go.format_go_file(self.test_file_go)

    def test_root_basic_generation(self):
        self.generate_files("""{
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
        }""")

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
        self.generate_files("""{
            "title": "ABcd",
            "type": "string",
            "enum": ["A", "B", "C"]
        }""")

        foo = self.import_test_file()
        self.assertIsInstance(foo.Abcd.A, foo.Abcd)
        self.assertEqual(foo.Abcd.A.value, "A")
        self.assertEqual(foo.Abcd.B.value, "B")
        self.assertEqual(foo.Abcd.C.value, "C")

    def test_root_integer_enum(self):
        self.generate_files("""{
            "title": "ABcd",
            "type": "integer",
            "enum": [0, 1, 2, 99],
            "javaEnumNames": ["A", "B", "C", "D"]
        }""")

        foo = self.import_test_file()
        self.assertIsInstance(foo.Abcd.A, foo.Abcd)
        self.assertEqual(foo.Abcd.A.value, 0)
        self.assertEqual(foo.Abcd.B.value, 1)
        self.assertEqual(foo.Abcd.C.value, 2)
        self.assertEqual(foo.Abcd.D.value, 99)

    def test_root_nested_objects(self):
        self.generate_files("""{
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
        }""")

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
        self.generate_files("""{
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
        }""")

        foo = self.import_test_file()
        foo.ABcd(Child1=0, Child2="2")
        foo.SubRef(ChildA=foo.ABcd())
        foo.DirectRef(Child1=0, Child2="2")
        assert isinstance(foo.DirectRef.from_dict({}), foo.DirectRef)

    def test_definitions_with_nested_refs(self):
        self.generate_files("""{
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
        }""")

        foo = self.import_test_file()
        foo.ABcd(
            Child1=foo.ABcd._Child1(
                IntVal=0, Child2=foo.ABcd._Child1._Child2(IntVal=0, ListVal=["1"])
            )
        )
        foo.Ref(IntVal=0, ListVal=["1"])
        foo.AAAA(X=0, YRef=foo.ABcd._Child1._Child2(IntVal=0, ListVal=["1"]))

    def test_list_definitions_with_nested_object(self):
        self.generate_files("""{
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
}""")

        foo = self.import_test_file()
        foo.A(sub1=[foo.A._sub1(prop1=0, prop2=1.2)])

    def test_list_definitions_with_ref(self):
        self.generate_files("""{
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
}""")

        foo = self.import_test_file()
        foo.A(prop1=[foo.B(prop1=0)])

    def test_bytes_type(self):
        self.generate_files("""{
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
}""")

        foo = self.import_test_file()
        foo.B(prop1=bytes(100 for _ in range(1024)))

    def test_special_character(self):
        self.generate_files("""{
    "definitions": {
        "B": {
            "type": "object",
            "properties": {
                "test-hyphen": {
                    "type": "string"
                },
                "test.dot": {
                    "type": "string"
                }
            }
        }
    }
}""")
        foo = self.import_test_file()
        B = foo.B.from_dict({"test-hyphen": "1", "test.dot": "2"})
        assert B.test_hyphen == "1"
        assert B.test_dot == "2"

    def test_nested_enum(self):
        self.generate_files("""
{
  "title": "Test",
  "type": "object",
  "properties": {
    "prop1": {
      "type": "string"
    },
    "prop2": {
      "description": "My favorite Enum!",
      "type": "string",
      "enum": [
        "First",
        "Second",
        "Third"
      ]
    }
  }
}
""")
        test = self.import_test_file().Test
        assert test("a", test._prop2.First).prop2 == test._prop2.First

    def test_special_values(self):
        t = json.dumps(TRICKY)
        self.generate_files(f"""{{
    "definitions": {{
        "A": {{
            "type": "object",
            "description": {t},
            "properties": {{
                "s": {{
                    "type": "string",
                    "description": {t},
                    "default": {t},
                    "format": {t},
                    "pattern": {t}
                }},
                "i": {{
                    "type": "integer",
                    "maximum": "1 + 1"
                }}
            }}
        }},
        "E": {{
            "type": "string",
            "enum": [{t}],
            "javaEnumNames": ["X"]
        }}
    }}
}}""")
        foo = self.import_test_file()
        self.assertEqual(foo.A().s, TRICKY)
        self.assertEqual(foo.A._formats_map["s"], TRICKY)
        self.assertEqual(foo.A._validations_map["s"]["pattern"], TRICKY)
        self.assertEqual(foo.A._validations_map["i"]["maximum"], "1 + 1")
        self.assertEqual(foo.E.X.value, TRICKY)
        self.assertIn('a\'b"c\\d */ """ /e', foo.A.__doc__)


class GeneratedOutput(unittest.TestCase):
    """Checks on the generated source text, for one language at a time."""

    def render(self, schema, language="python", **kwargs):
        loader = jsonschema2popo.JsonSchema2Popo(language=language, **kwargs)
        loader.update_args(argparse.Namespace(package_name="generated"))
        loader.process(schema)
        out = io.StringIO()
        out.close = lambda: None
        loader.write_file(out)
        return out.getvalue()

    def test_rejects_invalid_names(self):
        for schema in [
            {"definitions": {"A(": {"type": "object"}}},
            {
                "definitions": {
                    "A": {"type": "object", "properties": {"x=1": {"type": "integer"}}}
                }
            },
            {
                "definitions": {
                    "A": {"type": "object", "properties": {"x\n": {"type": "integer"}}}
                }
            },
            {"definitions": {"E": {"type": "string", "enum": ["a b"]}}},
            {
                "definitions": {
                    "E": {"type": "string", "enum": ["a"], "javaEnumNames": ["1a"]}
                }
            },
        ]:
            for language in ("python", "js", "go"):
                with self.subTest(schema=schema, language=language):
                    self.assertRaisesRegex(
                        ValueError,
                        "cannot be used as an identifier",
                        self.render,
                        schema,
                        language,
                    )

    def test_accepts_names_that_worked_before(self):
        for language in ("python", "js", "go"):
            with self.subTest(language=language):
                out = self.render(
                    {
                        "title": "Bestellung für Kunden",
                        "type": "object",
                        "properties": {
                            "größe": {"type": "integer"},
                            "x-y.z": {"type": "string"},
                        },
                    },
                    language,
                )
                self.assertIn("BestellungFürKunden", out)
        # JS identifiers may contain '$', and JS enum keys may be numbers
        self.render(
            {
                "definitions": {
                    "A": {"type": "object", "properties": {"$x": {"type": "integer"}}}
                }
            },
            "js",
        )
        self.assertIn(
            "0: 0,",
            self.render(
                {"definitions": {"E": {"type": "integer", "enum": [0, 1]}}}, "js"
            ),
        )

    def test_valid_literals_are_emitted_as_before(self):
        schema = {
            "definitions": {
                "A": {
                    "type": "object",
                    "properties": {
                        "s": {"type": "string", "default": "a\\nb", "format": "x\\ty"},
                        "i": {"type": "integer", "default": "5", "maximum": "10"},
                        "b": {"type": "boolean", "default": "True"},
                        "c": {"type": "integer", "default": "Color.RED"},
                    },
                },
                "E": {"type": "string", "enum": ["a", None]},
            }
        }
        py = self.render(schema)
        self.assertIn(", s='a\\nb'", py)
        self.assertIn("'s': 'x\\ty'", py)
        self.assertIn(", i=5 ", py)
        self.assertIn(", b=True ", py)
        self.assertIn(", c=Color.RED ", py)
        self.assertIn("'maximum': 10,", py)
        js = self.render(schema, "js")
        self.assertIn("s: 'x\\ty'", js)
        self.assertIn('None: "None",', js)
        self.assertIn('None: "None",', self.render(schema, "go"))

    def test_number_like_values_are_emitted_as_before(self):
        schema = {
            "definitions": {
                "A": {
                    "type": "object",
                    "properties": {
                        "i": {"type": "integer", "default": "0x10", "maximum": " 10 "},
                        "f": {"type": "number", "default": "-Infinity"},
                    },
                },
                "H": {
                    "type": "integer",
                    "enum": ["0x10", " 7"],
                    "javaEnumNames": ["SIXTEEN", "SEVEN"],
                },
            }
        }
        py = self.render(schema)
        self.assertIn(", i=0x10 ", py)
        self.assertIn("'maximum': 10,", py)
        js = self.render(schema, "js")
        self.assertIn("f=-Infinity,", js)
        go = self.render(schema, "go")
        self.assertIn("SIXTEEN: 0x10,", go)
        self.assertIn("SEVEN: 7,", go)

    def test_escapes_keep_their_meaning_next_to_line_breaks(self):
        schema = {
            "definitions": {
                "A": {
                    "type": "object",
                    "properties": {
                        # a line continuation (backslash + newline) in Python and JS
                        "c": {
                            "type": "string",
                            "format": "x\\\ny",
                            "default": "d\\\ne",
                        },
                        # a raw CR, which Go allows in a string, next to an escape
                        "r": {"type": "string", "format": "tab\\tsep\rx"},
                        # U+2028 next to an escape
                        "u": {"type": "string", "format": "A\\x41 "},
                    },
                }
            }
        }
        py = self.render(schema)
        self.assertIn("'c': 'x\\\ny',", py)
        self.assertIn(", c='d\\\ne'", py)
        js = self.render(schema, "js")
        self.assertIn("c: 'x\\\ny',", js)
        self.assertIn("u: 'A\\x41\\u2028',", js)
        self.assertIn('"r": "tab\\tsep\rx",', self.render(schema, "go"))

    def test_js_string_defaults_are_strings(self):
        js = self.render(
            {
                "definitions": {
                    "A": {
                        "type": "object",
                        "properties": {
                            "s": {"type": "string", "default": "pending"},
                            "u": {"type": "string", "default": "a\u2028b"},
                            "b": {"type": "boolean", "default": "true"},
                        },
                    }
                }
            },
            "js",
        )
        self.assertIn('s="pending",', js)
        self.assertIn('u="a\\u2028b",', js)
        self.assertIn("b=true,", js)

    def test_names_are_only_checked_when_emitted(self):
        schema = {
            "title": "Root",
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "definitions": {
                "my thing": {
                    "type": "object",
                    "properties": {"@id": {"type": "string"}},
                },
                "Color": {"type": "string", "enum": ["light-blue"]},
            },
        }
        for language in ("python", "js", "go"):
            with self.subTest(language=language):
                self.render(schema, language, generate_definitions=False)
                self.assertRaises(ValueError, self.render, schema, language)

    def test_custom_templates_are_not_name_checked(self):
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp)
        self.addCleanup(os.chdir, os.getcwd())
        os.chdir(tmp)
        with open("t.tmpl", "w") as f:
            f.write(
                "{% for m in models %}{% for p in m.properties %}{{ p.name }};{% endfor %}{% endfor %}"
            )
        out = self.render(
            {
                "title": "Doc",
                "type": "object",
                "properties": {"@id": {"type": "string"}},
            },
            custom_template="t.tmpl",
        )
        self.assertEqual("@id;", out)

    def test_docstring_with_escaped_quotes_and_trailing_backslash(self):
        description = 'Use \\"quoted\\" text, dir C:\\'
        py = self.render({"title": "Doc", "type": "object", "description": description})
        self.assertIn(description, py)

    def test_non_string_pattern(self):
        schema = {
            "title": "P",
            "type": "object",
            "properties": {"a": {"type": "string", "pattern": 5}},
        }
        self.assertIn("'pattern': '5'", self.render(schema))
        self.assertIn("'pattern': /5/", self.render(schema, "js"))
        self.assertIn('"pattern": "5"', self.render(schema, "go"))

    def test_js_pattern_with_unclosed_class(self):
        schema = {
            "title": "P",
            "type": "object",
            "properties": {"a": {"type": "string", "pattern": "[/"}},
        }
        self.assertIn("'pattern': new RegExp(\"[/\")", self.render(schema, "js"))


if __name__ == "__main__":
    unittest.main()
