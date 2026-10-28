# compat

## Current focus: CCGraph first

Implement a **CCGraph-compatible clone-detection base in both `gstyle` and `rstyle`**, backed by a shared, versioned **PDG contract**. Then build additional analyses around that foundation as optional graph/fact consumers, clone-pair consumers, or named extension profiles.

The initial goal is shared behavior and graph/stage conformance, not a shared runtime or repository merge. Paper ambiguities need explicit, versioned decisions; Go/Rust agreement alone is not original-CCGraph reproduction.

- [CCGraph strict matching profile and machine settings](schemas/ccgraph-profile.md)
- [Rust HIR R0 extraction profile](schemas/rust-extraction-profile.md)
- [Fixture expectations and contract checks](schemas/README.md)
- [Implementation plan and milestone gates](ALGORITHM_UNIFICATION.md)
- [Focused phase-one PDG/CCGraph audit prompt](PHASE_ONE_INVENTORY_PROMPT.md)
- [Partial inventory checkpoint and resumption guide](inventory/README.md)
- [Paper contracts and current fidelity gaps](inventory/ccgraph.md)

The audit remains historical documentation-only evidence. The initial matching and Rust extraction profiles are now specified as version `0.1.0`, with hand-authored fixtures and static contract checks; this is not engine conformance or measured clone quality. Implementation follows these contracts.

The shared PDG root `profile: {id, version}` is the sole versioned extraction contract for counts, capability meanings, provenance rules and edge semantics; per-record evidence remains, but separate `policy` fields do not. `extraction_evidence.conformance` is a single `{status, reasons}` assessment of that extraction profile, while matching retains a separate profile. Registered extraction counting rules must satisfy the matching profile's reference-count requirement. This is a contract-only development simplification: neither `gstyle` nor `rstyle` is updated, schema/profile versions are unchanged, and no backward compatibility or legacy representation is provided.

Abstraction mining stays parked until conformance and a bounded labeled quality evaluation pass; broader detectors and rewriting remain separate scopes.

## Tiny extraction compatibility suite

See [suite/README.md](suite/README.md) for six paired Go/Rust fixtures, an exact
pre-mining multigraph comparator, independent expectations, and retained runs.
The initial run exposes compatibility gaps; semantic graph matches, transport
schema validity, producer evidence, and runtime checks are reported separately.
