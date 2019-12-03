# JSONSchema2PoPo2
*Forked from [github.com/frx08/jsonschema2popo](https://github.com/frx08/jsonschema2popo)*

A converter to extract 'Plain Old Python Object' classes from JSON Schema files.
Similar to the Java project [JSONSchema2PoJo](https://github.com/joelittlejohn/jsonschema2pojo/).
Currently compatible with Python 3.4+ (when using enums, otherwise any version should be fine).

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
- -t, --use-types - Add MyPy typings.
- -ct, --constructor-type-check - Validate provided types in constructor. Default only type checks when setting property values and not when setting them in the constructor.
- -s, --use-slots - Add a `__slots__` to each generated class to be more memory efficient.
- --no-generate-from-definitions - Don't generate any classes from the "definitions" section of the schema.
- --no-generate-from-root-object - Don't generate any classes from the root of the schema.
- -tp, --translate-properties - Translate property names to be snake_case. With this enabled, inner classes will no longer be prefixed by "_" since their names won't collide with the property name.
- -l, --language - Language to generate in. Either "js" or "python".

### Encode Generated Object to JSON:
```python
import json

g = GeneratedClass()
json.dumps(g.as_dict())
```

### Decode JSON into Generated Object:
```python
import json
g = GeneratedClass.from_dict(json.loads(data))
```

### JSON Schema Format
This library is largely compatible with JSONSchema2PoJo and how that library reads the JSON Schema to generate Java.
Specifically, for enumerations, this library supports setting the `javaEnumNames` array in JSON Schema for an enum to give names
to the enum values that will be generated in the Python output.
