pub fn f(a: i32, b: bool) -> i32 {
    let mut x: i32 = a;
    if b {
        x = 1;
    } else {
        x = 2;
    }
    return x;
}
