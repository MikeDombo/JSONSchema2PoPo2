//+build test_jsonschema2popo.test_special_values

package test

import (
	"fmt"
	"generated"
	"os"
)

func assertEquals(a interface{}, b interface{}) {
	if fmt.Sprint(a) != fmt.Sprint(b) {
		fmt.Printf("%+v did not equal %+v\n", a, b)
		os.Exit(1)
	}
}

func Test() {
	tricky := "a'b\"c\\d */ \"\"\" /e\nf"
	assertEquals(generated.AFormats["s"], tricky)
	assertEquals(generated.AValidations["s"]["pattern"], tricky)
	assertEquals(generated.AValidations["i"]["maximum"], "1 + 1")
	assertEquals(generated.EOptions.X, tricky)
}
