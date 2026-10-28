# Extraction contract: compat.tiny-pdg/1

This is an exact comparison of **normal-flow extraction**, before CCGraph
projection, clone admission/scoring, slicing, WL, or hashing. It is a bounded
suite contract, not a claim that the producers implement the same full profile.
The independently authored oracle is `expectations.py`; the runner cannot update
it. The six paired functions are deliberately eligible scalar programs. Loops,
calls, memory, concurrency, macros, destructuring, shadowing and implicit returns
are deferred. A behavioral pairing can be valid while extraction fails.

## Equality

There must be one bijection of operations, bindings, definitions and dependency
occurrences preserving all labels and all directed incidence edges, including
parallel occurrences. Binding and definition IDs are references in that same
bijection, never free text to erase independently. Collections and opaque IDs
have no order. Input/output positions, operand positions and outcome lists do.
The comparator searches the bijection and verifies the entire mapped edge
multiset. Label/degree counts only prune this search. No hash or similarity
threshold establishes equality.

`graph.py` represents a dependency as a labeled vertex with `source` and `target`
incidence edges, and, when applicable, `symbol`, `definition`, and `controller`
incidence edges. This lossless incidence encoding makes those references part of
the same graph isomorphism. Two identical dependencies remain two vertices.
Ordinary directed access/definition relations retain multiplicity too.

The compared labels/relations are:

| Entity | Required facts |
|---|---|
| Binding | parameter/local role, resolved `i32`/`bool` type; identity through every read, write, definition and dependency |
| Definition | unique identity, defining operation and binding; reciprocal operation `defines` relation |
| Formal input | category, interface position, resolved type, variadic flag, definition/binding |
| Output metadata | category `output`, position, return role, resolved type, variadic flag |
| Declaration/assignment | category, initialization/reassignment form, write binding and position, produced definitions |
| Read | category, read binding and position; redundant frontend type/binding lists must agree |
| Computation | category, exact operator, exact literal value if present, resolved scalar type |
| Predicate | category, `if` or `short-circuit-and`, ordered true/false outcomes |
| Return | category, normal exit kind, value dependencies and operand positions |
| Merge | category, scalar type, every definition, access, incoming dependency and alternative guard that is actually exported |
| Dependency | family, refinement, direction, multiplicity; data operand position; reaching-definition symbol/definition and loop-carried flag; control outcome; alternative position/outcome/controller |

Only data edges have value operand positions. Go's control ordinal is checked
against its outcome, then represented by the outcome, because Rust exports no
redundant ordinal. Execution edges are **nearest dominating executable
operation**, not source order, all dominance pairs, or CFG successors. Control
edges are normal-flow postdominance dependence, not lexical nesting.

Required reaching-definition edges go directly from each reaching source
definition's operation to the read. This contract deliberately chooses the
existing R0 hand-authored fixture's representation. A different SSA/merge
representation is a compatibility gap under this contract; it is not evidence
that SSA itself is wrong. An adapter must not splice such a merge away.

## Permitted conversions (closed list)

* Alpha-rename IDs and bound source names jointly; ignore function/package/file
  names, formatting, spans and display text as matching labels. Retain their raw
  provenance. Scope IDs use different frontend granularities; preserve binding
  identity and all its incidence rather than compare textual scope IDs. This
  corpus has one binding scope and no shadowing.
* Go `int32` equals Rust `i32`; `bool` equals `bool`. Constants 1 and 2 have the
  enclosing explicit scalar type. No platform-sized `int`/`isize` conversion.
* `:=`/Rust initialization map to `initialization`; `=`/Rust reassignment map to
  `reassignment`. The assignment operator must agree. Literal computations have
  operator `literal` even where Rust encodes it through `original_kind=expr_lit`.
* Go `scalar-value`, `reaching-definition`, `nearest-operation-dominator`, and
  `post-dominator-control` map respectively to Rust `value_operand`,
  `reaching_definition`, `nearest_dominating_operation`, and `postdominance`.
  No other dependence refinement is collapsed.
* Go short-circuit predicate `construct=short-circuit, operator=&&` equals Rust
  `construct=&&`. Neither is interchangeable with eager conjunction.
* A singleton scalar read/write in this corpus has exactly one access slot: omitted access
  position denotes that slot 0 in this suite. A Go reaching-definition edge into
  such a read also has only slot 0. This conversion is narrowly guarded; a
  missing value-operand or alternative position is never filled. Missing
  positions on binding-merge inputs remain `unrecorded` and fail the oracle.
  For these acyclic sources only, omitted Go `loop_carried` equals false.
* Remove the Go unnamed, binding-free `formal_output` node with exactly
  `attributes={position:0}` and its checked return-to-slot edges. Retain the
  complete output interface as an `output` vertex. Do not splice edges. This is
  an administrative boundary convention, following the shared fixtures'
  boundary-removal rule. No entry/exit graph nodes occur in these PDG exports.
* Source/analysis origin, frontend `original_kind`, and `synthetic` are provenance,
  not comparison labels: Go extracts some reads/predicates as analysis entities
  while Rust uses source HIR operations. A synthetic **merge category**, its
  definitions and edges remain semantic and cannot disappear through this rule.

No graph edges are reconstructed from source, CFG, dominance, or expectations.
The adapter checks known redundant facts rather than use conflicting values.
Rust `compat.rust.hir-r0:guards` and Go `gstyle.go:guards` short-circuit
guard DNF must be exactly one matching controller/outcome
atom for this corpus; general DNF equivalence is outside this contract. Exported merge availability must be unconditional for these expressions; conflicting availability/type facts are rejected. Go's
unconditional value operands are not reinterpreted as guarded alternatives.

The raw schema/profile IDs, support claims, configuration, diagnostic messages,
all extension fields, original types/kinds and byte spans are retained. Producer
policy objects, source metadata, explanation strings, operation-effect and
value-operand inventory extensions are not graph labels. The operation/edge
contract above selects their relevant scalar semantic facts. The suite does not
compare clone reference counts, counts used for scoring, or matching labels.

## Evidence and failure handling

Source spans are half-open **UTF-8 byte** ranges into the exact content identified
by their source ID and content identity, as required by the shared schema. A
source path is navigation information; it does not imply whole-file coordinates.
Go currently identifies the complete fixture file. Rust identifies captured
function text: the harness verifies the compiler snapshot against the exact
fixture bytes, slices its recorded function range, and checks the capture digest,
CFG embedded text/identity and PDG identity against those bytes. It retains the
identified bytes and checks all published function/node span bounds and source
references. Branch token anchors are converted from character to byte offsets in
that content. No exported span or graph is rewritten. Missing/ambiguous branch
anchors, shifted spans, split UTF-8 code points or inconsistent source evidence
fail separately from graph equivalence. Full token-to-node correspondence for
the other five cases is not asserted.

Graph conformance, current-schema validity, producer evidence/conformance,
compiler/runtime checks, and source metamorphisms are separate results. An exact
observed graph match cannot upgrade `non_conformant`, approximated or unsupported
producer claims. No claim of complete full-language extraction is made.

Missing required facts, unsupported types/categories/refinements, unresolved
accesses, or failed publication are reported with a reason; they cannot silently
produce an empty graph or a pass. Producer command failures are `not_run` for the
graph check with retained exit codes/stdout/stderr. A published but wrong graph
is `fail`, not an invalid language pairing. A missing merge-input position is
retained as `unrecorded`, reported as an issue, and cannot equal a known slot.
Current-schema failure is not repaired by deleting obsolete producer fields.

The runner exits 0 only if graph expectations, cross-source invariance, schema,
producer conformance and shared-input execution checks pass. Exit 1 means an
observed compatibility failure; exit 2 means setup/infrastructure failure.
Graph checks still run when independent transport validation fails, making
semantic progress visible without claiming full interoperability.
