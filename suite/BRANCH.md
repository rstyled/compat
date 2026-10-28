# Branch reassignment, worked first

Exact files: `cases/branch/f.go` and `cases/branch/f.rs`.

```go
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
```

```rust
pub fn f(a: i32, b: bool) -> i32 {
    let mut x: i32 = a;
    if b {
        x = 1;
    } else {
        x = 2;
    }
    return x;
}
```

Go's inferred `x` is exactly `int32`, from the explicitly typed parameter. Rust's
`mut` permits reassignment; it adds no PDG value operation. All `i32`/`int32`
inputs and both boolean outcomes are valid here; no arithmetic or overflow
assumption is needed. The initial value is deliberately overwritten on both
arms. Rust's unused-assignment warning confirms compilation, not PDG correctness.

## Source-to-operation correspondence

Aliases are explanatory identities only. `correspondence.json` independently
anchors these operations by token occurrence and category. The harness checks
those anchors against actual spans and retains the resulting producer IDs even
when the graph fails. The table's observed IDs are from the pinned latest run;
they are **not** inputs to the oracle or comparator.

| Alias | Go source | Rust source | Category | Observed Go / Rust ID |
|---|---|---|---|---|
| fa | parameter `a int32` | parameter `a: i32` | formal_input, position 0 | n1 / n0 |
| fb | parameter `b bool` | parameter `b: bool` | formal_input, position 1 | n2 / n1 |
| ra | RHS `a` in declaration | same | read a | n11 / n2 |
| d0 | `x := a` | `let mut x: i32 = a;` | declaration, initializes x | n10 / n3 |
| rb | condition `b` | same | read b | n12 / n4 |
| p | `if b {…} else {…}` | condition `b` of if | control, true/false | n4 / n5 |
| one | literal `1` | same | computation, literal i32 1 | n6 / n6 |
| w1 | `x = 1` | same | assignment, reassigns x | n5 / n7 |
| two | literal `2` | same | computation, literal i32 2 | n8 / n8 |
| w2 | `x = 2` | same | assignment, reassigns x | n7 / n9 |
| rx | `x` in return | same | read x | n13 / n10 |
| ret | `return x` | same | return, normal | n9 / n11 |

The expected PDG has exactly these 12 operations. Output metadata is position 0,
return role, i32, nonvariadic; no executable formal output. Bindings are a:i32
and b:bool (parameters), x:i32 (local). There are exactly five definitions:
`da=(a,fa)`, `db=(b,fb)`, `dx0=(x,d0)`, `dx1=(x,w1)`, `dx2=(x,w2)`.
Every read/write has slot 0 and every defining operation retains its definition.
No assignment-target read exists for these simple scalar assignments.

## Independent CFG and dependence derivation

Administrative CFG boundaries E and X are not PDG operations. Exact CFG transfers:

```
E -> ra -> d0 -> rb -> p
p --true--> one -> w1 -> rx
p --false-> two -> w2 -> rx
rx -> ret --return--> X
```

All unmarked transfers are normal. Formal inputs are initial values, not
executable CFG operations. The read and predicate are separate operations.

For binding x, reaching definitions use
`IN[n] = union OUT[pred]`, `OUT[n] = GEN[n] union (IN[n] minus KILL[n])`.
Each write kills every earlier definition of the same binding.

| Operation | IN(x) | OUT(x) |
|---|---|---|
| d0 | {} | {dx0} |
| p | {dx0} | {dx0} |
| w1 | {dx0} | {dx1} |
| w2 | {dx0} | {dx2} |
| rx | {dx1, dx2} | {dx1, dx2} |

Thus the exhaustive **data** edges are:

| Producer -> consumer | Refinement | Binding/definition or operand position |
|---|---|---|
| fa -> ra | reaching_definition | a / da, slot 0, loop_carried=false |
| fb -> rb | reaching_definition | b / db, slot 0, loop_carried=false |
| w1 -> rx | reaching_definition | x / dx1, slot 0, loop_carried=false |
| w2 -> rx | reaching_definition | x / dx2, slot 0, loop_carried=false |
| ra -> d0 | value_operand | 0 |
| rb -> p | value_operand | 0 |
| one -> w1 | value_operand | 0 |
| two -> w2 | value_operand | 0 |
| rx -> ret | value_operand | 0 |

Strict postdominators of p are `{rx, ret, X}`, so `ipdom(p)=rx`. On the true
transfer, one and w1 postdominate that successor but do not postdominate p;
analogously two and w2 on false. The exhaustive **control** edges are
`p -> one [true]`, `p -> w1 [true]`, `p -> two [false]`, `p -> w2 [false]`.
The joined read rx executes on every path after p, so it is not controlled by p.

Each executable operation has its nearest strict executable dominator as its
**execution** predecessor (omit E). Exact edges:

```
ra -> d0, d0 -> rb, rb -> p,
p -> one, one -> w1, p -> two, two -> w2,
p -> rx, rx -> ret
```

Neither arm write dominates rx. This explains why execution dependency is not
the CFG predecessor relation at the join. No transitive dominance edges occur.

These 9 data, 4 control and 9 execution edges are the complete multiset.
The following dependencies/entities are forbidden:

* d0 -> rx as a reaching definition, or a surviving dx0 at rx;
* w1 -> w2, w2 -> w1, or reads of assignment targets;
* p -> rx/ret as control dependencies;
* w1 -> rx or w2 -> rx as execution dependencies (data edges are required);
* formal-input execution edges, any dominance transitive closure;
* a new definition or phi/merge node for x, or unguarded branch-value operands;
* any edge family/operation not in the exhaustive inventory.

## Verified observation

Rust matches this independently derived graph exactly. Go instead exports an
extra merge n14 and definition d6, with w1/w2 -> merge -> rx reaching-definition
edges. The merge inputs omit operand positions. This is an implementation
compatibility gap against the selected direct-reaching-definition contract,
not an invalid source pairing. `ir_merges.go:joinedDefinition` explains its
construction. The harness retains it and fails; it does not collapse it into
passing edges. Go's unnamed formal output slot is removed only by the explicit
administrative boundary rule, with output metadata still checked.
