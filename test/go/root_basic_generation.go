//+build test_jsonschema2popo.test_root_basic_generation

package test

import (
	"generated"
)

func Test() {
	_ = generated.Abcd{
		Int:     0,
		Float:   0.1,
		ListInt: []int64{0, 1, 2},
		String:  "ABC",
		Object:  map[string]interface{}{"A": "X"},
	}
}
