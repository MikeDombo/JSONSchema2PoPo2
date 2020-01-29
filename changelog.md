# Changelog

## 2.0.22

-  Fix JS generation for enums to use `includes` instead of `in`

## 2.0.21

-  Fix class level comment spacing (JS)

## 2.0.20

-  Add `--namespace-path` for Javascript to prepend to members of a namespace

## 2.0.19

-   Fix generation in JS of pattern validation to make it a regex instead of plain string

## 2.0.18

-   Some changes to make eslint happier with the output

## 2.0.17

-   Support for JavaScript generation by using `-l js`

## 2.0.16

-   Add comments to properties

## 2.0.15

-   Bugfix for `as_dict` and `from_dict` when translating property names so that the output dictionary has the original property names for `as_dict` and
    using original property names from the input dictionary for `from_dict`

## 2.0.13

-   Add option to translate property names into snake_case which is more Pythonic
    -   -tp, --translate-properties - Translate property names to be snake_case. With this enabled, inner classes will no longer be prefixed by "\_" since their names won't collide with the property name.

## 2.0.12

-   Add option for which sections of the schema to generate code from
    -   --no-generate-from-definitions - Don't generate any classes from the `definitions` section of the schema.
    -   --no-generate-from-root-object - Don't generate any classes from the root of the schema.

## 2.0.11

-   Properly generate code for list types in the schema which declare new embedded object types

## 2.0.10

-   Indent generated docstring

## 2.0.9

-   Added `required` to the `_validations_map` for all properties

## 2.0.8

-   Generate `_validations_map` property of classes so that users can write validators based on the schema requirements

## 2.0.7

-   Bugfix for MyPy typings for lists

## 2.0.6

-   Support for class inheritance when using `extends` in the schema

## 2.0.5

-   Added comments to classes and properties based on the `description` field of the schema

## 2.0.2

-   Enabled generating classes with `bytes` type properties when the schema has `media.binaryEncoding: "base64"` set

## 2.0.1

-   Increased version of Jinja2 for CVE

## 2.0.0

-   Forked project from from [github.com/frx08/jsonschema2popo](https://github.com/frx08/jsonschema2popo)
-   Added proper usage of Python 3.4's enum classes
-   Enum names can be given in the schema as `javaEnumNames`
-   Added option to use `__slots__`
-   Added option to enable MyPy typings
-   Added option to check types in the constructor
-   Added a test suite
-   Enabled usage of nested schemas through the use of inner classes
-   Added proper `$ref` support to either copy or embed the referenced type depending on the usage
