//+build test_jsonschema2popo.test_list_definitions_with_ref

package test

import (
	"generated"
)

func Test() {
	_ = generated.A{Prop1: []generated.B{generated.B{Prop1: 0}}}
}
