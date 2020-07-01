//+build test_jsonschema2popo.test_bytes_type

package test

import (
	"../generated"
)

func Test() {
	slic := make([]byte, 1024)
	_ = generated.B{
		Prop1: &slic,
	}
}
