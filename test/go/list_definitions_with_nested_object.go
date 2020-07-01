//+build test_jsonschema2popo.test_list_definitions_with_nested_object

package test

import (
	"../generated"
)

func Test() {
	_ = generated.A{Sub1: []generated.A_sub1{{Prop1: 0, Prop2: 1.2}}}
}
