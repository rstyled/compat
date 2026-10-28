package fixture

func F(a int32, b bool) int32 {
	if b {
		return a
	}
	return 2
}
