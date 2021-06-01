//+build test_jsonschema2popo.test_special_character

package test

import (
	"generated"
)

func Test() {
	_ = generated.B{
	    Test_hyphen: "1",
        Test_dot: "2",
	}
}
