//+build test_jsonschema2popo.test_nested_enum

package test

import (
	"generated"
)

func Test() {
	_ = generated.Test{
	    Prop1: "1",
	    Prop2: generated.Test_prop2Options.First,
	}
}
