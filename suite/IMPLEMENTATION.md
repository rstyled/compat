# Verified implementation boundaries

Pins are the upstream default-branch heads checked on 2026-10-28:
gstyle `e4cdf52713c33ed40cd55c6d351a24dacc3661fb`, rstyle
`419c20a7d2322de9b976c6c2f2f856ad0ce68e98`. The original local checkouts were
older/different and one was dirty; neither was modified. Fresh clean detached
worktrees were built. No installed analyzer executable was assumed current.
`pins.json` and the run manifest record these choices; the runner rejects stale
or dirty source checkouts. Updating pins is an explicit source/contract review,
not expectation regeneration. Latest means these verified upstream heads at
that time, not a moving dependency on every rerun.

The current Rust source pins nightly-2026-09-30. Its compiler commit is
`5c543b0b8c73c7b72bc8284ced4fb22ead15734d`. Replacing it with a newer compiler
would not honor the producer's compiler-internal API boundary. The available Go
compiler is go1.27.2 linux/arm64; fixture modules select language version 1.26.0.
Rust uses edition 2021, no optimization, overflow/debug checks enabled, unwind
panics, no additional features/cfg; compiler target facts are retained.

## Go

Read and exercised at the above revision:

* `application/patterncheck/cli.go` selects `--format pdg-json`.
* `application/patterncheck/pdg_export.go:exportPDGs` calls
  `gopatterns.Extract`, validates native graphs, and exports **before mining**.
* `adapters/pdgjson/{export,operations,interface,evidence}.go` expands the native
  tables into the shared JSON shape. IDs refer to native definitions/bindings.
* `adapters/gopatterns/ir_reaching_subset.go` checks the whole scalar body and
  resolved types. `ir_scalar_order.go` excludes independent sibling orders;
  unary chains and short circuit are eligible here.
* `ir_scalar_cfg.go` expands operation order and conditional RHS flow;
  `ir_normal_flow.go` emits nearest-operation dominance and postdominance control.
* `ir_reaching.go:operation` and `ir_merges.go:joinedDefinition` create and cache
  the extra binding merge definition. This is visible in raw output.
* `ir_scalar_cfg.go:logicalValue` changes a logical computation into a merge,
  while its scalar-value edges remain unconditional operands. Actual exports
  lack selected-alternative/outcome/controller edges; the suite rejects them.
* The producer reports scalar-normal support for the exercised dependencies,
  but `node_extraction=approximated` and root conformance is `non_conformant`.
  This remains an evidence limitation even for the four exact observed graphs.

## Rust

* `crates/rstyle-driver/src/main.rs` uses `RSTYLE_HIR_DOCUMENT_DIR` to select the
  HIR fact/unit publication callbacks, overriding the legacy graph extraction
  path. Its default selection is R0. The legacy `src/pdg.rs` graph builder is
  not used by this suite.
* `hir_extraction/output.rs` publishes `unit.evidence.json`, its manifest, and
  eligible graph roots. The harness retains the entire unit including facts,
  CFG, PDG and eligibility/source diagnostics. It selects exactly one root.
* `rstyle-pdg/src/producer/mod.rs:produce` classifies, lowers, analyzes, emits and
  verifies a function. `producer/lower.rs` separates formal inputs, reads,
  predicates, explicit returns and nonexecuting short-circuit value sites.
* `producer/analysis.rs` uses per-binding reaching-definition sets with kills,
  nearest operation dominators, and postdominance control. `read_edges` emits
  every reaching definition directly to its consumer, with binding, definition
  and operand position. Short-circuit alternatives preserve selection guards.
* These actual outputs match all six independent semantic oracles. They still
  use an older shared transport revision: per-record policy fields and a list
  of conformance assessments. The current `schemas/pdg.schema.json` forbids
  those fields and requires one conformance object. All six Rust raw PDGs fail
  current-schema validation. No field is deleted to disguise this migration gap.

## Shared expectations and schemas

The suite reads and separately validates the **current** `schemas/pdg.schema.json`
from this compat checkout. The checked compat base revision was
`3e191191a1cf67f9cbcacb270d9ab28d16410284`.
`schemas/fixtures/rust-r0-extraction.json` supplies an existing independently
hand-authored branch-reassignment example and short-circuit alternative
contract. Its declared execution status is not_run. It is a useful specification
and cross-check, not producer proof. This suite authors its six explicit-return
fixtures and exhaustive oracle independently, and actually runs both producers.
The existing 35 schema/static-contract tests passed; they do not replace these
semantic extraction checks. No shared schema or either analyzer was redesigned.
