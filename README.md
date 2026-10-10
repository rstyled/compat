# compat

## Current focus: CCGraph first

Implement a **CCGraph-compatible clone-detection base in both `gstyle` and `rstyle`**, backed by a shared, versioned **PDG contract**. Then build additional analyses around that foundation as optional graph/fact consumers, clone-pair consumers, or named extension profiles.

The initial goal is shared behavior and graph/stage conformance, not a shared runtime or repository merge. Paper ambiguities need explicit, versioned decisions; Go/Rust agreement alone is not original-CCGraph reproduction.

- [Implementation plan and milestone gates](ALGORITHM_UNIFICATION.md)
- [Focused phase-one PDG/CCGraph audit prompt](PHASE_ONE_INVENTORY_PROMPT.md)
- [Partial inventory checkpoint and resumption guide](inventory/README.md)
- [Paper contracts and current fidelity gaps](inventory/ccgraph.md)

The audit is documentation-only. Implementation follows contract/fixture work; broader detectors, abstraction mining and rewriting are subsequent scopes with separate acceptance criteria.
