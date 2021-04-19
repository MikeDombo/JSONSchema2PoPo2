# Changelog

## 3.0.0rc2

- Fixed command line usage

## 3.0.0rc1

- Rewrote internal data models to be strongly typed for easier development of templates and supporting future 
  enhancements
- Created a plugin interface allowing developers to extend functionality by loading in their own code.
  - Developers should extend the [`CodeGenPlugin`](https://github.com/MikeDombo/JSONSchema2PoPo2/blob/master/jsonschema2popo/classes.py#L276) class
  - Users can then use `--language <name of python module>` to load the plugin as a module
  - Plugins can use their own templates, add more command line options, and modify the definitions prior to code 
    generation
  
### BREAKING CHANGES

The format of data provided to templates has changed rather significantly, though I hope this is an improvement.
See `classes.py` for the models which are provided and what their fields are.

The generated code is supposed to be entirely unchanged. Please open an issue if you find any differences.

## 2.2.3

- Fix for [#8](https://github.com/MikeDombo/JSONSchema2PoPo2/issues/8) 
  with [#9](https://github.com/MikeDombo/JSONSchema2PoPo2/pull/9). 
  Enum generation now works in the root object

## 2.2.2

- Added `--version` option
- Use lexicographical topological sort so the output class order should be deterministic

## 2.2.1

- Added support for custom template file (PR #4)

## 2.2.0

- Added *beta* Go generation. Interface of generated code should not yet be considered stable. Please create a GitHub
  issue to provide feedback on the generated code.

## 2.1.0

- Python generation properly typechecks required properties, now if a prop isn't required, you can set it to `None`.
- Updates to testing to not just do a file output comparison
- Generation of nested objects without properties now generates nothing. The property is instead treated as a `dict`.
- The `$ref` in `extends` can now take a path to a json file with a definition for schema inheritance.
- Fix JavaScript generation for nested objects which caused a redeclaration error.

## 2.0.23

- Limit the \_\_repr__ length in Python to prevent OOM
- Bump networkx version to latest stable (2.4) for Python 3.8 compatibility

## 2.0.22

- Fix JS generation for enums to use `includes` instead of `in`

## 2.0.21

- Fix class level comment spacing (JS)

## 2.0.20

- Add `--namespace-path` for Javascript to prepend to members of a namespace

## 2.0.19

- Fix generation in JS of pattern validation to make it a regex instead of plain string

## 2.0.18

- Some changes to make eslint happier with the output

## 2.0.17

- Support for JavaScript generation by using `-l js`

## 2.0.16

- Add comments to properties

## 2.0.15

- Bugfix for `as_dict` and `from_dict` when translating property names so that the output dictionary has the original
  property names for `as_dict` and using original property names from the input dictionary for `from_dict`

## 2.0.13

- Add option to translate property names into snake_case which is more Pythonic
    - -tp, --translate-properties - Translate property names to be snake_case. With this enabled, inner classes will no
      longer be prefixed by "\_" since their names won't collide with the property name.

## 2.0.12

- Add option for which sections of the schema to generate code from
    - --no-generate-from-definitions - Don't generate any classes from the `definitions` section of the schema.
    - --no-generate-from-root-object - Don't generate any classes from the root of the schema.

## 2.0.11

- Properly generate code for list types in the schema which declare new embedded object types

## 2.0.10

- Indent generated docstring

## 2.0.9

- Added `required` to the `_validations_map` for all properties

## 2.0.8

- Generate `_validations_map` property of classes so that users can write validators based on the schema requirements

## 2.0.7

- Bugfix for MyPy typings for lists

## 2.0.6

- Support for class inheritance when using `extends` in the schema

## 2.0.5

- Added comments to classes and properties based on the `description` field of the schema

## 2.0.2

- Enabled generating classes with `bytes` type properties when the schema has `media.binaryEncoding: "base64"` set

## 2.0.1

- Increased version of Jinja2 for CVE

## 2.0.0

- Forked project from from [github.com/frx08/jsonschema2popo](https://github.com/frx08/jsonschema2popo)
- Added proper usage of Python 3.4's enum classes
- Enum names can be given in the schema as `javaEnumNames`
- Added option to use `__slots__`
- Added option to enable MyPy typings
- Added option to check types in the constructor
- Added a test suite
- Enabled usage of nested schemas through the use of inner classes
- Added proper `$ref` support to either copy or embed the referenced type depending on the usage
