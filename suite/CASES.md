# Six paired cases and their independent expectations

All functions use Go `int32` / Rust `i32` or `bool` explicitly at their interfaces;
Go locals inherit the exact typed RHS, and Rust locals have explicit `i32`
annotations. Return statements are explicit in both languages. Only the chain
uses arithmetic. Its allowed domain is `a != -2147483648`; both negations are
then representable, so checked Rust arithmetic and Go arithmetic agree. Other
integer cases accept every i32 input. Nothing here assumes that general signed
integer overflow is equivalent across the languages.

The selected scalar-normal/R0 producers admit all six bodies: primitive named
parameters and locals, direct reads/writes, if, explicit return and short-circuit
boolean evaluation. The current outputs confirm selection/publication, not just
a documentation claim. The producer limitations are assessed separately.

`expectations.py` constructs exact multisets from these manually chosen lists.
The helper functions only encode labels/relations; they do not calculate edges
from a producer, CFG, or snapshot. Formal inputs define their own parameter
binding; declaration/assignment nodes define the indicated local binding. Each
read/write slot is 0. Every result is one scalar output port at position 0.

## Parameter to return (`identity`)

Sources: `return a` / `return a;`.
Operations: fa (formal input), ra (read a), ret (return).
Definitions: a@fa.
Data: fa -> ra (reaching definition a@fa), ra -> ret (value slot 0).
Execution: ra -> ret. Control: none.
Forbidden: direct fa -> ret bypassing ra; execution from fa; any merge.

## Straight-line dependency chain (`chain`)

Sources: `x := -a; y := -x; return y` / typed Rust equivalents.
Operations: fa, ra, neg1, dx, rx, neg2, dy, ry, ret.
Definitions: a@fa, x@dx, y@dy.
Data reaching: fa -> ra (a), dx -> rx (x), dy -> ry (y).
Data values, all slot 0: ra -> neg1 -> dx; rx -> neg2 -> dy; ry -> ret.
Execution: adjacent pairs of `ra, neg1, dx, rx, neg2, dy, ry, ret`.
Control: none. Both computations are unary `-`, result type i32.
Forbidden: fa -> rx, dx -> ry, any transitive execution edge or merge.
The two unary operations avoid Go's unspecified order between independent
ordinary binary operands while retaining a useful dependency chain.

## Overwritten definition (`overwrite`)

Sources: `x := a; x = 1; return x` / typed mutable Rust equivalent.
Operations: fa, ra, d0 (declaration), one, w1 (assignment), rx, ret.
Definitions: a@fa, x@d0, x@w1.
Data reaching: fa -> ra (a@fa), w1 -> rx (x@w1).
Data values, slot 0: ra -> d0, one -> w1, rx -> ret.
Execution: adjacent pairs of `ra, d0, one, w1, rx, ret`.
Control: none. Literal one is i32 1.
Forbidden: d0 -> rx (killed definition); target read at w1; deleting the
reachable initialization merely because its result is later overwritten.

## Branch join (`branch`)

Fully derived in `BRANCH.md`, including CFG, source correspondence, reaching sets,
postdominance, all three edge families and forbidden dependencies. No phi.

## Early return (`early`)

Sources: `if b { return a }; return 2` / Rust equivalent.
Operations: fa, fb, rb, p, ra, ret1, two, ret2.
Definitions: a@fa, b@fb.
Data reaching: fb -> rb (b), fa -> ra (a).
Data values, slot 0: rb -> p, ra -> ret1, two -> ret2.
Execution: rb -> p, p -> ra, ra -> ret1, p -> two, two -> ret2.
Control: p -> ra/ret1 [true]; p -> two/ret2 [false].
Both returns lead to the one administrative normal CFG exit X, so
ipdom(p)=X. The statement after the if is controlled by **false**, despite
being outside the lexical then block. No ret1 -> two/ret2 edge is allowed.
Literal two is i32 2.

## Short circuit (`short_circuit`)

Sources: `return a && b` / `return a && b;`, with bool inputs/output.
Operations: fa, fb, ra, p (short-circuit-and), rb, m (bool merge), ret.
Definitions: a@fa, b@fb.
Normal CFG: E -> ra -> p; p --true--> rb -> ret;
p --false--> ret; ret --return--> X. Formal inputs and m are not executable.
Data reaching: fa -> ra (a), fb -> rb (b).
Data values: ra -> p [slot 0], m -> ret [slot 0].
Data alternatives: rb -> m [slot 0, true, controller p];
ra -> m [slot 1, false, controller p]. The false path reuses the saved left
value; no invented false-literal operation or second left read is permitted.
Execution: ra -> p, p -> rb, p -> ret.
Control: p -> rb [true]. ret postdominates p, so p does not control ret.
Forbidden: eager binary conjunction, unconditional ra/rb value operands into m,
a missing false alternative, unguarded RHS, or execution through m.

## Compilation and shared inputs

The driver type-checks each exact Rust fixture while extracting it. Go's export
loads and type-checks each exact Go fixture. Runtime wrappers retain the full
function source; Go changes only the package header and adds fmt/main, Rust
appends main. Those exact wrapper sources and compiler commands are retained.
No runtime wrapper enters the extraction comparison.

Identity/chain/overwrite execute a in {-100,-1,0,1,100}. Branch/early execute the
Cartesian product of that set with both b values. Short circuit executes all
four boolean pairs. Each language is checked against the independently written
result function as well as the other language: respectively a, a, 1,
`b ? 1 : 2`, `b ? a : 2`, and `a && b`. These are smoke checks, not an exhaustive
integer equivalence proof or proof of conditional evaluation. The PDG oracle
is what tests short-circuit structure.
