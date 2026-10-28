package fixture

func F(a int32, b bool) int32 {
	x := a
	if b {
		x = 1
	} else {
		x = 2
	}
	return x
}
