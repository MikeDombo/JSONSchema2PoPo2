//+build test_jsonschema2popo.test_root_integer_enum

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
	assertEquals(generated.AbcdOptions.A, 0)
	assertEquals(generated.AbcdOptions.B, 1)
	assertEquals(generated.AbcdOptions.C, 2)
	assertEquals(generated.AbcdOptions.D, 99)
}
