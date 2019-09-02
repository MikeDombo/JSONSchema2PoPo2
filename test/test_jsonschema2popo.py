import io
import json
import os
import unittest
from jsonschema2popo import jsonschema2popo
from jsonschema2popo.jsonschema2popo import format_file


class JsonSchema2Popo(unittest.TestCase):
    test_file = "test_output.py"

    def tearDown(self):
        os.remove(self.test_file)

    def test_root_basic_generation(self):
        loader = jsonschema2popo.JsonSchema2Popo(
            use_types=False, constructor_type_check=False
        )
        loader.process(
            json.loads(
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
                }
            }
        }"""
            )
        )
        loader.write_file(self.test_file)
        format_file(self.test_file)
        self.assertFileEqual(self.test_file, "valid/test_root_basic_generation.py")

    def test_root_string_enum(self):
        loader = jsonschema2popo.JsonSchema2Popo(
            use_types=False, constructor_type_check=False
        )
        loader.process(
            json.loads(
                """{
            "title": "ABcd",
            "type": "string",
            "enum": ["A", "B", "C"]
        }"""
            )
        )
        loader.write_file(self.test_file)
        format_file(self.test_file)
        self.assertFileEqual(self.test_file, "valid/test_root_string_enum.py")

    def test_root_integer_enum(self):
        loader = jsonschema2popo.JsonSchema2Popo(
            use_types=False, constructor_type_check=False
        )
        loader.process(
            json.loads(
                """{
            "title": "ABcd",
            "type": "integer",
            "enum": [0, 1, 2, 3],
            "javaEnumNames": ["A", "B", "C", "D"]
        }"""
            )
        )
        loader.write_file(self.test_file)
        format_file(self.test_file)
        self.assertFileEqual(self.test_file, "valid/test_root_integer_enum.py")

    def test_root_nested_objects(self):
        loader = jsonschema2popo.JsonSchema2Popo(
            use_types=False, constructor_type_check=False
        )
        loader.process(
            json.loads(
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
        )
        loader.write_file(self.test_file)
        format_file(self.test_file)
        self.assertFileEqual(self.test_file, "valid/test_root_nested_objects.py")

    def test_definitions_basic_generation(self):
        loader = jsonschema2popo.JsonSchema2Popo(
            use_types=False, constructor_type_check=False
        )
        loader.process(
            json.loads(
                """{
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
            )
        )
        loader.write_file(self.test_file)
        format_file(self.test_file)
        self.assertFileEqual(
            self.test_file, "valid/test_definitions_basic_generation.py"
        )

    def test_definitions_string_enum(self):
        loader = jsonschema2popo.JsonSchema2Popo(
            use_types=False, constructor_type_check=False
        )
        loader.process(
            json.loads(
                """{
            "definitions": {
                "ABcd": {
                    "type": "string",
                    "enum": ["A", "B", "C"]
                }
            }
        }"""
            )
        )
        loader.write_file(self.test_file)
        format_file(self.test_file)
        self.assertFileEqual(self.test_file, "valid/test_definitions_string_enum.py")

    def test_definitions_integer_enum(self):
        loader = jsonschema2popo.JsonSchema2Popo(
            use_types=False, constructor_type_check=False
        )
        loader.process(
            json.loads(
                """{
            "definitions": {
                "ABcd": {
                    "type": "integer",
                    "enum": [0, 1, 2, 3],
                    "javaEnumNames": ["A", "B", "C", "D"]
                }
            }
        }"""
            )
        )
        loader.write_file(self.test_file)
        format_file(self.test_file)
        self.assertFileEqual(self.test_file, "valid/test_definitions_integer_enum.py")

    def test_definitions_nested_objects(self):
        loader = jsonschema2popo.JsonSchema2Popo(
            use_types=False, constructor_type_check=False
        )
        loader.process(
            json.loads(
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
                }
            }
        }"""
            )
        )
        loader.write_file(self.test_file)
        format_file(self.test_file)
        self.assertFileEqual(self.test_file, "valid/test_definitions_nested_objects.py")

    def test_definitions_with_refs(self):
        loader = jsonschema2popo.JsonSchema2Popo(
            use_types=False, constructor_type_check=False
        )
        loader.process(
            json.loads(
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
        )
        loader.write_file(self.test_file)
        format_file(self.test_file)
        self.assertFileEqual(self.test_file, "valid/test_definitions_with_refs.py")

    def test_definitions_with_nested_refs(self):
        loader = jsonschema2popo.JsonSchema2Popo(
            use_types=False, constructor_type_check=False
        )
        loader.process(
            json.loads(
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
        )
        loader.write_file(self.test_file)
        format_file(self.test_file)
        self.assertFileEqual(
            self.test_file, "valid/test_definitions_with_nested_refs.py"
        )

    def assertFileEqual(self, filename1, filename2, message=""):
        with io.open(filename1) as f1:
            with io.open(filename2) as f2:
                self.assertListEqual(list(f1), list(f2), message)


if __name__ == "__main__":
    unittest.main()
