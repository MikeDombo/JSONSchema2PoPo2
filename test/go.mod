module main

go 1.16

replace test => ./go

replace generated => ./generated

require generated v0.0.0-00010101000000-000000000000 // indirect

require test v0.0.0-00010101000000-000000000000
