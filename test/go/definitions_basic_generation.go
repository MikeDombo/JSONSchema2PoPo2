//+build test_jsonschema2popo.test_definitions_basic_generation

package test

import (
	"../generated"
)

func Test() {
	_ = generated.RootObject{};
	_ = generated.ABcd{};
}
