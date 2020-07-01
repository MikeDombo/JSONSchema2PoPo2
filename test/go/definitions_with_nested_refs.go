//+build test_jsonschema2popo.test_definitions_with_nested_refs

package test

import (
	"../generated"
)

func Test() {
	_ = generated.ABcd{
		generated.ABcd_Child1{
			0, generated.ABcd_Child1_Child2{0, []string{"1"}},
		},
	}
	_ = generated.Ref{0, []string{"1"}}
	_ = generated.AAAA{0, generated.ABcd_Child1_Child2{0, []string{"1"}}}
}
