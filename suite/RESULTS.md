# Retained results, 2026-10-28

Built and exercised clean upstream default-branch heads gstyle `e4cdf52` and
rstyle `419c20a`. Rust used its pinned nightly compiler, not an installed stale
driver. See `IMPLEMENTATION.md`, `pins.json` and archived manifest/commands.
The harness exit status is **1: observed compatibility failures**.

## Passes

| Case | Go vs independent oracle | Rust vs independent oracle | Exact Go/Rust equivalence | Shared-input execution |
|---|---|---|---|---|
| branch | FAIL | PASS | FAIL | PASS |
| identity | PASS | PASS | PASS | PASS |
| chain | PASS | PASS | PASS | PASS |
| overwrite | PASS | PASS | PASS | PASS |
| early | PASS | PASS | PASS | PASS |
| short_circuit | FAIL | PASS | FAIL | PASS |

All twelve original fixture sources type-check through their actual producer.
All twelve runtime wrappers compile. Both languages produce the independent
expected result on all 39 shared input vectors (78 observed results). This is a
smoke check, not an exhaustive integer proof. All 12 per-producer source
renaming/formatting invariance checks pass, including invariance of the two
failing Go graphs. Original and renamed graph-oracle results agree.

All six original Go exports pass the current shared PDG schema. Existing schema
and static-contract tests: **35 passed**. Comparator and adapter tests: **11 passed**, covering
six ID/collection permutation cases, 14 deliberately corrupted graphs, exact
parallel-edge multiplicity, invalid references, a same-count/degree nonisomorphic
pair, self-loops, and 80 comparisons with independent exhaustive small-graph
bijection enumeration. Adapter checks also reject missing required positions, missing loop evidence, conflicting types/bindings, unavailable edge evidence, and unexpected guards; duplicate dependencies remain distinct. Source metamorphisms additionally exercise the real
extractors, not only the in-memory comparator.

## Failures

**Branch reassignment:** Go n14 is an extra merge with an extra x definition d6.
Its reaching-definition edges are n5/n7 -> n14 -> n13. The oracle requires the
original two definitions directly at n13. The merge-input positions are
unrecorded. Compare `branch/original/go.source-correspondence.json`,
`go.mismatch.json`, `cross-language.mismatch.json`, and `go.raw.json` in the
archive. `BRANCH.md` gives the source-derived proof and forbidden dependencies.
The next implementation decision is whether to implement the selected direct
reaching-definition contract in Go; collapsing the merge inside this suite
would evade the contract.

**Short circuit:** Go uses n6 -> n5 [value_operand 0] and n7 -> n5
[value_operand 1], without alternative outcome/controller labels. Required
edges are right -> merge [value_alternative, true, slot 0, controller p] and
saved-left -> merge [value_alternative, false, slot 1, controller p]. The CFG's
conditional RHS and control edge are not a substitute for guarded value
selection in the exported PDG. See `short_circuit/original/go.mismatch.json`
and raw exports. The adapter must not invent the missing selection evidence.

**Rust transport:** all six original and six renamed PDGs fail the current
shared schema. Original error counts are branch 108, identity 33, chain 81,
overwrite 62, early 76, short circuit 62. Repeated errors are obsolete per-record
`policy` fields and list-form conformance, while the current shared schema
requires a single conformance object. See each `rust.schema-errors.json` for
JSON paths and errors. Update the producer transport separately; passing semantic
graph checks do not make these documents valid interchange documents.

## Incomplete producer evidence

All Go graphs declare root `non_conformant`, with `node_extraction=approximated`
and the incomplete-dependencies diagnostic, despite supported scalar dependency
capabilities for these bodies. The runner records this as `evidence_status:
incomplete` for all six cases. Four exact observed graph passes do not upgrade
that claim. Rust reports R0 conformance and supported required semantic
capabilities; its transport migration failure remains separate.

The double-negation chain uses a stated nonoverflow input precondition. Rust's
raw CFG/evidence also retains its bounded normal-flow scope and arithmetic
limitations. No exceptional-flow or purity claim is made.

## Unsupported / invalid pairings

None of the six original or renamed cases is rejected as unsupported. All are
valid source pairings with compatible concrete types. Published graph failures
above are implementation/contract gaps, not invalid pairings. Unknown types,
missing required facts and unsupported refinements would produce explicit
unsupported results rather than a pass; setup failures exit 2.

## Not run

No selected fixture, source metamorphism, runtime check, or comparator check was
skipped. Loops and language-specific mechanisms are outside this initial corpus.
No clone scoring, WL/hash comparison, quality benchmark, full analyzer unit-test
suite, Lean proof suite, or exhaustive integer execution was run. Those are not
acceptance evidence for this bounded extraction test.

## Retained evidence

`evidence/latest-run.tar.gz` contains a `latest-run/` tree with raw producer unit
bundles (including Rust CFGs/facts), PDGs, exact sources and runtime wrappers,
normalized graphs, bijections/source maps, schema errors, full mismatch graphs,
command records/stdout/stderr, compiler identities/configuration, revision and
binary digests, and the exact harness/oracle/contract/schema snapshots used.
`evidence/tests.txt` retains the focused and shared test results. Executables and
Cargo build products are excluded from the portable archive; their digests and
build commands are recorded, and they remain in ignored local artifacts.
