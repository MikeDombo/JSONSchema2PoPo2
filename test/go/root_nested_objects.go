//+build test_jsonschema2popo.test_root_nested_objects

package test

import (
	"../generated"
)

func Test() {
	_ = generated.Abcd{generated.Abcd_Child1{0, generated.Abcd_Child1_Child2{0, []string{"0"}}}}
}
