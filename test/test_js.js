"use strict"
const args = process.argv.slice(2);

const assertTrue = (b) => {
    if (!b) {
        throw new Error(`${b} was expected to be true`);
    }
}

const assertEquals = (a, b) => {
    if (a !== b) {
        if (JSON.stringify(a) === JSON.stringify(b)) {
            return;
        }
        throw new Error(`${a} != ${b}`);
    }
}

const assertThrows = (exType, exMessage, callable) => {
    let fallThrough = false;
    try {
        callable();
        fallThrough = true;
    } catch (e) {
        if (exType === null) {
            console.log(e);
        }
        if (!(e instanceof exType)) {
            throw new Error(`Exception ${e} is not of type ${exType}!`);
        }
        assertEquals(exMessage, e.message);
    }
    if (fallThrough) {
        throw new Error(`Exception ${exType} ${exMessage} was not thrown!`);
    }
};

const f = {};

f.test_jsonschema2popo_test_root_basic_generation = (filename) => {
    const foo = require("./" + filename);

    const a = foo.Abcd.fromMap(
        {
            "Int": 0,
            "Float": 0.1,
            "ListInt": [0, 1, 2],
            "String": "ABC",
            "Object": {"A": "X"},
        }
    );
    assertEquals(a.Int, 0);
    assertEquals(a.Float, 0.1);
    assertEquals(a.ListInt, [0, 1, 2]);
    assertEquals(a.String, "ABC");
    assertEquals(a.Object, {"A": "X"});

    assertThrows(
        Error, "Int must be Number", () => foo.Abcd.fromMap({"Int": true})
    )
    assertThrows(
        Error,
        "Float must be Number",
        () => foo.Abcd.fromMap({"Float": true}),
    )
    assertThrows(
        TypeError,
        "d.ListInt.reduce is not a function",
        () => foo.Abcd.fromMap({"ListInt": true}),
    )
    assertThrows(
        Error,
        "ListInt array values must be Number",
        () => foo.Abcd.fromMap({"ListInt": ["0.2"]}),
    )
    assertThrows(
        Error, "String must be String", () => foo.Abcd.fromMap({"String": 0})
    )
}

f.test_jsonschema2popo_test_root_string_enum = (filename) => {
    const foo = require("./" + filename);

    assertTrue(foo.Abcd.A instanceof foo.Abcd);
    assertEquals(foo.Abcd.A.asMap(), "A");
    assertEquals(foo.Abcd.B.asMap(), "B");
    assertEquals(foo.Abcd.C.asMap(), "C");
}

f.test_jsonschema2popo_test_root_integer_enum = (filename) => {
    const foo = require("./" + filename);

    assertTrue(foo.Abcd.A instanceof foo.Abcd);
    assertEquals(foo.Abcd.A.asMap(), 0);
    assertEquals(foo.Abcd.B.asMap(), 1);
    assertEquals(foo.Abcd.C.asMap(), 2);
    assertEquals(foo.Abcd.D.asMap(), 99);
}

f.test_jsonschema2popo_test_root_nested_objects = (filename) => {
    const foo = require("./" + filename);

    new foo.Abcd(new foo.Abcd._Child1(0, new foo.Abcd._Child1._Child2(0, ["0"])));

    assertThrows(
        Error, "Child1 must be Abcd._Child1", () => new foo.Abcd(0)
    );
    assertThrows(
        Error,
        "Child2 must be Abcd._Child1._Child2",
        () => new foo.Abcd._Child1(0, 0),
    )
}

f.test_jsonschema2popo_test_definitions_basic_generation = (filename) => {
    const foo = require("./" + filename);

    new foo.ABcd();
    new foo.RootObject();
}

f.test_jsonschema2popo_test_definitions_basic_generation_no_generation = (filename) => {
    const foo = require("./" + filename);

    new foo.RootObject();
    assertThrows(
        TypeError, "foo.ABcd is not a constructor", () => new foo.ABcd()
    );
}

f.test_jsonschema2popo_test_definitions_with_refs = (filename) => {
    const foo = require("./" + filename);

    new foo.ABcd(0, "2");
    new foo.SubRef(new foo.ABcd());
    new foo.DirectRef(0, "2");
}

f.test_jsonschema2popo_test_definitions_with_nested_refs = (filename) => {
    const foo = require("./" + filename);
    new foo.ABcd(
        new foo.ABcd._Child1(
            0, new foo.ABcd._Child1._Child2(0, ["1"])
        )
    );
    new foo.Ref(0, ["1"]);
    new foo.AAAA(0, new foo.ABcd._Child1._Child2(0, ["1"]));
}

f.test_jsonschema2popo_test_list_definitions_with_nested_object = (filename) => {
    const foo = require("./" + filename);
    new foo.A([new foo.A._sub1(0, 1.2)]);
}

f.test_jsonschema2popo_test_list_definitions_with_ref = (filename) => {
    const foo = require("./" + filename);
    new foo.A([new foo.B(0)]);
};

f.test_jsonschema2popo_test_bytes_type = (filename) => {
    const foo = require("./" + filename);
    new foo.B(Buffer.alloc(1024));
}

const functionName = args[0].replace(/\./g, "_");
if (functionName in f) {
    f[functionName](...args.slice(1))
} else {
    console.error(`${functionName} is not a function!`)
    process.exit(1);
}
