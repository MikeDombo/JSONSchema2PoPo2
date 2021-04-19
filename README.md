# JSONSchema2PoPo2

*Forked from [github.com/frx08/jsonschema2popo](https://github.com/frx08/jsonschema2popo)*

A converter to extract 'Plain Old Python Object' classes from JSON Schema files. Similar to the Java
project [JSONSchema2PoJo](https://github.com/joelittlejohn/jsonschema2pojo/).

[![PyPI version](https://badge.fury.io/py/JSONSchema2PoPo2.svg)](https://pypi.org/project/JSONSchema2PoPo2/) [![Python package](https://github.com/MikeDombo/JSONSchema2PoPo2/workflows/Python%20package/badge.svg?branch=master)](https://github.com/MikeDombo/JSONSchema2PoPo2/actions?query=workflow%3A"Python+package")

## Generated Code Compatibility

| Language | Feature | Version Compatibility | Reason |
| -------- | ------- | --------------------- | ------ |
| Python | Basic generation | Any Python | N/A |
| Python | Using Enums | \>= Python  3.4 | Uses [Enum](https://docs.python.org/3/library/enum.html) type |
| Python | Using Extends | \>= Python  3.0 | Uses new style Python class for inheritance |
| Python | Using Types | \>= Python  3.5 | Uses Python [type hints](https://www.python.org/dev/peps/pep-0484/) in code
|  |  |  |
| JavaScript | Basic Generation | \>= ES2019 (\>= NodeJS 12.x) | Uses ES [classes](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Classes) and [private fields](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Classes/Private_class_fields)
|  |  |  |
| Go | Basic Generation | Any Go | N/A |

## Installation

```
pip install jsonschema2popo2
```

## Usage

### Basic:

```
jsonschema2popo2 -o /path/to/output_file.py /path/to/json_schema.json
```

### Options:

- -o, --output-file - Generated file path.
- -jt, --custom-template - Path to custom Jinja template file (relative to CWD).
- -t, --use-types - Add MyPy typings. (Python only)
- -ct, --constructor-type-check - Validate provided types in constructor. Default only type checks when setting property
  values and not when setting them in the constructor. (Python and JavaScript only)
- -s, --use-slots - Add a `__slots__` to each generated class to be more memory efficient. (Python only)
- --no-generate-from-definitions - Don't generate any classes from the "definitions" section of the schema.
- --no-generate-from-root-object - Don't generate any classes from the root of the schema.
- -tp, --translate-properties - Translate property names to be snake_case. With this enabled, inner classes will no
  longer be prefixed by "_" since their names won't collide with the property name.
- -l, --language - Language to generate in. Choose "python", "js", "go", a python file, or a python module. When 
  using a python file or module, the module must expose `Plugin` as a class which extends and implements `CodeGenPlugin`.
- --namespace-path - Namespace path to be prepended to the @memberOf for JSDoc. (JavaScript only)
- --package-name - Package name for generated code. Default is "generated". (Go only)
- --version - Show the current version number.

### Encode Generated Object to JSON:

**Python**

```python
import json

g = GeneratedClass()
json.dumps(g.as_dict())
```

**JavaScript**

```javascript
g = new GeneratedClass();
JSON.stringify(g.asMap());
```

**Go**

```go
g := generated.GeneratedClass{};
str, err := json.Marshal(g)
```

### Decode JSON into Generated Object:

**Python**

```python
import json

g = GeneratedClass.from_dict(json.loads(data))
```

**JavaScript**

```javascript
const g = GeneratedClass.fromMap(JSON.parse(data));
```

**Go**

```go
var g generated.GeneratedClass
err := json.Unmarshal(data, &g)
```

### JSON Schema Format

This library is largely compatible with JSONSchema2PoJo and how that library reads the JSON Schema to generate Java.
Specifically, for enumerations, this library supports setting the `javaEnumNames` array in JSON Schema for an enum to
give names to the enum values that will be generated in the Python output.

If you want to generate an object with a property that accepts any map/dictionary, then simply have `"type": "object"`in
the schema and do not add any properties to that definition. In this case, no new class will be generated, instead that
property's type will be `dict` in Python, `Object` in JavaScript, and `map[string]interface{}` in Go (`encoding/json` in
Go doesn't support `map[interace{}]interface{}`).

#### Example JSON Schema Documents

**Schema with references and enum**

```json
{
  "definitions": {
    "Enum1": {
      "description": "My favorite Enum!",
      "type": "integer",
      "enum": [
        1,
        2,
        3
      ],
      "javaEnumNames": [
        "First",
        "Second",
        "Third"
      ]
    },
    "Obj1": {
      "type": "object",
      "properties": {
        "prop1": {
          "type": "string"
        },
        "prop2": {
          "$ref": "#/definitions/Enum1"
        }
      }
    },
    "Obj2": {
      "type": "object",
      "properties": {
        "obj1": {
          "$ref": "#/definitions/Obj1"
        }
      }
    }
  }
}
```

#### Generated Documentation

When you provide a `"description"` in the JSON Schema, then that description will be applied in docstrings in the
generated code. For example, in the example above, the enum will have a docstring which says `My favorite enum!`.

You can also choose to add documentation for yourself in the schema document using the `"$comment"` key, which is simply
ignored by this tool. In this way, you can have public documentation in the `description`, and anything you want to keep
private can go in the `$comment`.

### Customizing Generated Code

There are two ways to customize the output code which this project generates: you may use your own code generation 
template, or you may implement a code generation plugin _and_ code generation template. I would suggest that you go 
the whole way to implementing a code generation plugin since it isn't much additional work and can give you great 
benefits.

#### Example Code Generation Plugin

Take as an example our 
[builtin Go plugin](https://github.com/MikeDombo/JSONSchema2PoPo2/blob/468ea0881557dd98c831cae173f0bcd2ea73ac72/jsonschema2popo/go/go.py).
This plugin is simply a single Python file along with a template file. The Python code implements the 
`CodeGenPlugin` interface which allows it to add more arguments to the command line options and then make those new 
values available to the template file. The plugin can also provide more functions to be called from the Jinja 
template which makes developing a template far simpler.
