//+build test_jsonschema2popo.test_root_string_enum

package test

import (
	"../generated"
	"fmt"
	"os"
)

func assertEquals(a interface{}, b interface{}) {
	if fmt.Sprint(a) != fmt.Sprint(b) {
		fmt.Printf("%+v did not equal %+v\n", a, b)
		os.Exit(1)
	}
}

func Test() {
	assertEquals(generated.AbcdOptions.A, "A")
	assertEquals(generated.AbcdOptions.B, "B")
	assertEquals(generated.AbcdOptions.C, "C")
}
