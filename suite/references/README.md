# Language semantics consulted

Authoritative sources retrieved 2026-10-28 from the official language sites.
The compressed snapshot retains exact retrieved HTML and sha256 metadata, not
an introductory guide. The contract uses these relevant rules:

* [Go Specification: assignments](https://go.dev/ref/spec#Assignments) and
  [short variable declarations](https://go.dev/ref/spec#Short_variable_declarations):
  evaluating a scalar RHS precedes replacing the destination's stored value;
  a typed initializer determines the short-declared local's type.
* [Go if statements](https://go.dev/ref/spec#If_statements): true selects then,
  false selects else. [Return statements](https://go.dev/ref/spec#Return_statements)
  terminate the function and supply its results; these fixtures have no defer.
* [Go logical operators](https://go.dev/ref/spec#Logical_operators): evaluate the
  left operand, then the right only if needed; `p && q` is `if p then q else false`.
* [Go order of evaluation](https://go.dev/ref/spec#Order_of_evaluation): many
  ordinary operand orderings are unspecified. The chain therefore uses unary
  operations. Short circuit has specified conditional sequencing.
* [Go integer overflow](https://go.dev/ref/spec#Integer_overflow): signed overflow
  is defined and does not panic. It is not interchangeable with checked Rust
  overflow. Exclude i32::MIN in the double-negation chain.
* [Rust assignment expressions](https://doc.rust-lang.org/reference/expressions/operator-expr.html#assignment-expressions):
  evaluate the value operand before the place operand, then assign. The unit
  result of a statement assignment introduces no transferred scalar value.
* [Rust lazy boolean operators](https://doc.rust-lang.org/reference/expressions/operator-expr.html#lazy-boolean-operators):
  `&&` evaluates the RHS only if the LHS is true. An unconditional binary-value
  edge does not express that selection under our chosen extraction contract.
* [Rust overflow](https://doc.rust-lang.org/reference/expressions/operator-expr.html#overflow):
  checked integer operations panic on overflow, including negation of the most
  negative signed integer. The chain's input restriction avoids that path.
* [Rust if expressions](https://doc.rust-lang.org/reference/expressions/if-expr.html):
  the selected branch follows the boolean condition. Both branch assignments
  target the one mutable local binding, not a new branch-local variable.
* [Rust return expressions](https://doc.rust-lang.org/reference/expressions/return-expr.html):
  transfer the argument to the output location and control to the caller;
  the expression itself diverges and has type `!`. The semantic return operation
  is labeled by normal exit behavior, not by confusing `!` with its result type.

The specs determine language behavior. Reaching definitions, postdominance,
nearest-dominator execution dependencies and graph granularity are the suite's
explicit analysis contract, not claims made by either language specification.
