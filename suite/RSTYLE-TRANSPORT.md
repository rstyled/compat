# Historical Rust projection candidate

Superseded by the [native PDG model candidate](RSTYLE-NATIVE-PDG.md), which deletes
the legacy internal format and projection rather than maintaining two grammars.

On 2026-10-28, upstream rstyle main was verified at
`419c20a7d2322de9b976c6c2f2f856ad0ce68e98` and compat main at
`3e191191a1cf67f9cbcacb270d9ab28d16410284`. The shared schema used here and
rstyle's top-level vendored schema are byte-identical to that compat revision,
SHA256 `d2ce26b478c2c01620d50f08ac7aea32036fa105424fb73f6b9adbf68c4f3291`.
The old Rust transport tests selected a different, older `rust-r0` schema.

Rust candidate `fa52e01fec86472f3e1fd098111a9abf26c7ed67`
([branch](https://github.com/rstyled/rstyle/tree/fix/current-pdg-transport))
was built from a clean checkout and compared with clean gstyle
`15f168134328241a7c5347b5a16a0b740f3a649e`, the **unmerged**
[Go PR #296](https://github.com/rstyled/gstyle/pull/296) head. Go's upstream
master remained `e4cdf52713c33ed40cd55c6d351a24dacc3661fb`.
Original failing pins, fixtures, expectations and the comparator are unchanged.

The Rust patch uses a typed, borrowed transport at paired exports, shared unit
bundles and standalone serialized PDGs. It emits one root profile, omits
historical record policies and emits one conformance object. It checks internal
policy agreement and exactly one matching assessment before serialization;
conflicting claims cannot be erased. The reader rejects obsolete fields and
inherits the root profile for the existing strict verifier. Semantic graph
attributes, evidence statuses/reasons and opaque namespaced proof records are
preserved. The historical internal model and normative snapshots remain pinned.
Old exported wire documents require an explicit migration.

| Check | Result |
| --- | --- |
| Independent graph expectations | 24/24 pass: six cases, two producers, two source variants |
| Exact labeled, directed multigraph comparison | 12/12 pass |
| Real renaming/formatting graph invariance | 12/12 pass |
| Rust shared schema | 12/12 pass, previously 12/12 fail |
| Go shared schema | 12/12 pass |
| Compilation and shared-input execution | All six pairs pass; 39 vectors, 78 observed results |
| Branch source correspondence | 3/4 pass; renamed Rust fails |
| Rust selected evidence checks | 12/12 pass |
| Go producer evidence | 12/12 incomplete |
| Full compatibility harness | Exit 1 |
| Rust workspace nextest | 2,338 passed, zero failed, five existing ignored tests skipped |
| Rust doctest commands | Pass; zero runnable doctests |
| Format and workspace/all-target Clippy with warnings denied | Pass |
| Rstyle and patterns | Zero style violations; zero active abstraction candidates |
| Comparator/adapter regression tests | 13 pass, including deliberately corrupted graphs |
| Existing shared schema/static fixture tests | 35 pass |

**Remaining failure:** the renamed Rust branch's `input_value` token begins at
byte 61, while its exported formal-input span is `[15,26)`, shifted by the
46-byte leading formatting comment. `branch/renamed/result.json` reports
`Source correspondence ambiguous/missing for fa`; compare its `f.rs` and
`rust.raw.json`. The exact semantic graph still matches its independent oracle.
No span correction is applied by the comparator or adapter.

**Incomplete evidence:** Go continues to report approximated node extraction,
nonconformance and its incomplete-dependencies diagnostic. Exact observed graph
matches do not upgrade that claim. Rust transport now validates, and its
bounded normal-flow evidence is retained without strengthening it.

**Unsupported cases:** none of the six pairs or their source variants was
rejected as unsupported. No selected case, shared input or comparator check was
skipped.

**Not run:** the five repository-ignored Rust tests (three release benchmarks,
a supplemental analyzer comparison and a CFG evidence printer); remote PR CI
and its other platforms; loops and language-specific corpus expansion. The
suite independently asserts source-to-node spans for the worked branch case;
it does not assert full source-span correspondence for the other five cases.
The patterns gate retains the repository's 15 existing ignored candidates.
No new ignore entry, schema relaxation or regenerated graph expectation is used.

Reproduce with clean producer checkouts at the pinned revisions:

```sh
uv run --no-project --with jsonschema python suite/run.py \
  --pins suite/candidates/rstyle-current-transport.json \
  --gstyle /path/to/gstyle --rstyle /path/to/rstyle \
  --rust-target /path/to/rust-build --out /path/to/new-results
```

`suite/evidence/rstyle-current-transport.tar.gz` retains the complete textual
run, including exact fixture sources and wrappers, raw PDGs/unit bundles,
configuration and compiler identities, binary digests, command logs/exit codes,
independent expectations/comparator snapshots, graph bijections and separate
mismatch records. It also includes the exact Rust commit patch and successful
local check logs. Executables/build products are excluded from the portable
archive and remain in the ignored local artifacts. The actual run is retained
at `suite/artifacts/rstyle-transport-fa52e01`.
