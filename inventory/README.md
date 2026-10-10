# Inventory checkpoint — CCGraph-first

**Status: partial.** Existing source/reference records are retained. They are audit evidence, not proof of conformance, a finalized PDG schema, or completed implementations. The immediate scope is now **M0: PDG/CCGraph implementation-gap audit**, not exhaustive review of every analysis in both projects.

## Current direction

See the [CCGraph-first plan](../ALGORITHM_UNIFICATION.md) for layers and M0–M5 acceptance gates, and the [focused phase-one prompt](../PHASE_ONE_INVENTORY_PROMPT.md) for audit execution.

1. Establish a versioned PDG/evidence contract and a separately derived CCGraph graph view.
2. Implement the CCGraph feature/filter/WL/verification/**clone-pair** pipeline in both Go and Rust against shared graph and stage fixtures.
3. Build additional scopes as optional PDG/fact consumers, clone-pair consumers, or explicitly named extension profiles. Do not let them silently change base results.

This is a target direction, not a description of existing wiring. Sharing a contract does not require a shared runtime library. Effects, slicing and other analyses can use the PDG without first running clone detection; source-only style rules need not use the PDG at all.

## Recorded implementation snapshots

| Project | Independently versioned revision | State at source inspection |
| --- | --- | --- |
| `gstyle` | `598c7b03366caa0fef70f66aa58e76222eefb8fa` | Clean |
| `rstyle` | `2c4752ca9c7b992e66d21380600a69f597133687` | Clean |

The parent repository does not identify child contents: both directories were untracked from its perspective. Source line references in the existing reports refer to the child snapshots above. Reports may record hashes of the **previous** plan/prompt; those are historical input identities, not hashes of the revised CCGraph-first instructions. Do not silently update them and thereby misrepresent the original review scope.

The [reference audit](ccgraph.md) records the PDF/dependency identities, inspected source and observed read-only commands. The source slices below have their own scope and limitations. **No analyzer tests, conformance runs or benchmarks have been executed as part of this checkpoint.**

## Preserved evidence and how to use it

| Record | Use in the focused audit |
| --- | --- |
| [CCGraph contracts and fidelity gaps](ccgraph.md) | Primary reference-stage evidence, paper ambiguities, current Go/Rust comparison and fixture designs |
| [Reflection claim ledger](claims.md) | Distinguish current behavior from reported history and unsupported fidelity/safety/measurement claims |
| [Page-preserving PDF text](paper-pages.txt) | Discovery/citation aid; the original PDF remains the primary reference |
| [Go patterns](algorithms/go-patterns.md) | PDG extraction/conversion, clone stages and extension contamination; defer unrelated detector/rewrite internals |
| [Rust core](algorithms/rust-core.md) | Graph schema, normalization/WL/mining and production boundaries; do not mistake existing mining for a full CCGraph detector |
| [Rust frontend](algorithms/rust-frontend.md) | Target selection, compiler extraction, serialization and PDG producer limitations; evaluation tooling is deferred |
| [Go quality/extraction](algorithms/go-quality.md) and [slice coverage](go-quality-coverage.md) | Source/fact and effect/ownership dependency evidence where relevant; unrelated quality-rule internals are deferred |

These records were produced under the broader audit request. They are not centrally reconciled into a complete P0 coverage ledger. Some slice records refer to coverage sidecars that were not present at this checkpoint; recover those or reconstruct denominators before relying on their local coverage claims. Review depth, test existence and test execution must remain distinct.

## Most important base gaps already recorded

From the [source/reference audit](ccgraph.md#decisive-findings), not runtime observations:

- Go's detector uses seven numerical features and a name-only string filter rather than the paper's nine numerical/three string fields. Neither inspected graph schema has execution-dependency edges.
- Rust currently provides WL-based abstraction mining, not an independently wired full CCGraph clone-pair pipeline.
- Go production reporting enables an AST bypass that skips both numerical and name filtering; candidate-retrieval LSH and connected grouping also change the reference-stage contract.
- Current scoring is not a direct implementation of every printed paper formula. The paper itself leaves competing filtering, multiplicity, normalization and depth interpretations.

These are reasons to specify and test the base, not permission to silently choose a paper reading or change defaults.

## Prioritized resumption / handoff

### Finish M0 — focused audit

1. Reconcile existing Go/Rust/paper records into a **P0 module and stage ledger**, including production callers, absent stages, semantic branches and relevant test families. Recover missing sidecars where possible. Leave unreviewed P2 scopes deferred.
2. Produce `pdg-contract-gaps.md`: data/control/execution dependencies, taxonomy and feature inputs, source provenance/identity, rebinding/branches/loops, call/memory boundaries, known-zero versus unknown evidence, and information loss in conversions/caches.
3. Produce a base-readiness matrix: `reference stage → Go → Rust → producer/stage/evidence gap → distinguishing fixture → milestone`. Keep frontend adaptation separate from imported-graph matching.
4. Record P1 isolation requirements: extracted graph versus CCGraph view versus abstraction views, optional annotations, AST/LSH/kernel alternatives, pair output versus grouping/filtering. Create a dependency/backlog index for the remaining scopes.
5. Identify which paper decisions block M1 and which unsupported producer cases can be explicitly outside a bounded initial profile. Do not claim original-tool reproduction without pinned original artifacts.

### M1–M3 — specification and implementation, not yet performed

- **M1:** version the PDG interchange and selected reference interpretation; add independently specified graph-validation, extraction and stage fixtures. Resolve or explicitly block ambiguous paper policies.
- **M2:** bring both frontend producers into conformance for the supported graph profile, preserving unknowns and richer source evidence.
- **M3:** implement the complete CCGraph pair detector in both engines, compare intermediate traces on identical graphs, and verify extension toggles cannot mutate base results.

### M4–M5 — around the base

Reconnect additional analyses one scope at a time with their own contracts, then validate optimizations and measure labeled quality/scale. Clone matching does not establish safe extraction; grouping does not establish all pairwise matches; more groups do not establish recall.

**Completion claims remain separate:** focused M0 coverage, full-union inventory coverage, selected-profile conformance, frontend adaptation, original-tool reproduction, extension quality and rewrite safety.
