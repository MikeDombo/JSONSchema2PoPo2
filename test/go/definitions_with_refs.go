//+build test_jsonschema2popo.test_definitions_with_refs

package test

import (
	"../generated"
)

func Test() {
	_ = generated.ABcd{0, "2"};
	_ = generated.SubRef{generated.ABcd{}};
	_= generated.DirectRef{0, "2"};
}
