# Native Rust PDG model candidate

**Correction:** the source-span failure recorded below was a harness error,
not a Rust extractor defect. Rust spans correctly reference the identified
function fragment. The [corrected source checks and rerun](SOURCE-SPANS.md)
supersede that diagnosis; the historical archive remains unchanged.

Rust candidate [`f7d4586`](https://github.com/rstyled/rstyle/commit/f7d45862df5ac7278c4684656e56075e9bde118b)
on `fix/current-pdg-transport` directly models the current shared schema.
Ordinary serde handles standalone PDGs, pairs, borrowed views, shared unit
bundles and serialized verification. The legacy model/projection modules,
record-policy fields, profile inheritance and conformance arrays are deleted.
Paired manifests use only the current checksum field and XXH3; the SHA alias
and fallback are deleted. There is no migration adapter or backwards
compatibility requirement. Compatibility-specific rejection tests are removed.

Live upstream refs were checked at 2026-10-28 04:36 UTC: rstyle main
`419c20a7d2322de9b976c6c2f2f856ad0ce68e98`, compat main
`3e191191a1cf67f9cbcacb270d9ab28d16410284`, Go master
`e4cdf52713c33ed40cd55c6d351a24dacc3661fb`. The comparison uses Go
`15f168134328241a7c5347b5a16a0b740f3a649e`, still the **unmerged**
[PR #296](https://github.com/rstyled/gstyle/pull/296) branch.
Both producer checkouts were clean. Rust's vendored PDG schema and the shared
schema have SHA256 `d2ce26b478c2c01620d50f08ac7aea32036fa105424fb73f6b9adbf68c4f3291`.

| Check | Result |
| --- | --- |
| Independent graph expectations | 24/24 pass |
| Exact labeled directed multigraph comparison | 12/12 pass |
| Real renaming/formatting graph invariance | 12/12 pass |
| Rust / Go shared schema | 12/12 pass each |
| Compilation and shared-input execution | All six pairs pass; 39 vectors, 78 results |
| Branch source correspondence | 3/4 pass; renamed Rust fails |
| Rust selected evidence | 12/12 pass |
| Go producer evidence | 12/12 incomplete |
| Full compatibility harness | Exit 1 |
| Rust workspace nextest | 2,332 pass; zero fail; five existing ignored tests skipped |
| Doctest commands | Four pass; zero runnable doctests |
| Format and workspace/all-target Clippy, warnings denied | Pass |
| Rstyle / patterns | Zero violations / zero active candidates; 15 existing ignores |

The first native-model test run had 364 failures from obsolete fixture fields.
The final run passes after removing 42 pointer-width policy members from 11
captured frontend fixtures and obsolete policy members from one hand-authored
edge helper. A structural check verified that all other JSON values in those
11 fixtures stayed identical. Source programs, graph nodes/edges and independent
compat expectations were not regenerated. Both test logs are retained.

**Historical harness failure (diagnosis corrected above):** renamed Rust branch source correspondence reports
`Source correspondence ambiguous/missing for fa`. The `input_value` token starts
at file byte 61; its exported formal-input span is `[15,26)` in the captured
function beginning at file byte 46. These are consistent coordinates. See
`branch/renamed/f.rs`, `rust.raw.json` and `result.json` in the archive.
Semantic graph comparisons pass; the producer needs no offset correction.

**Incomplete evidence:** Go retains approximated node extraction,
nonconformance and its incomplete-dependencies diagnostic. Observed graph
matches do not strengthen these claims.

**Unsupported cases:** none of the six selected pairs or source variants.

**Not run:** the five existing ignored Rust tests (three benchmarks, a
supplemental analyzer comparison and a CFG evidence printer); remote CI and
other platforms; loops/language-specific corpus expansion. Python comparator/adapter and shared-schema
unit tests were not rerun because their code and expectations are
unchanged; their prior results remain in the earlier archive. Complete
independent source-span mapping is asserted only for the worked branch case.
No legacy-rejection test suite or migration path is maintained.

Reproduce with clean producer checkouts at the revisions in
`candidates/rstyle-native-pdg.json`:

```sh
uv run --no-project --with jsonschema python suite/run.py \
  --pins suite/candidates/rstyle-native-pdg.json \
  --gstyle /path/to/gstyle --rstyle /path/to/rstyle \
  --rust-target /path/to/rust-build --out /path/to/new-results
```

`suite/evidence/rstyle-native-pdg.tar.gz` retains exact fixture sources,
wrappers, raw outputs, schema errors, graph correspondences, mismatch reports,
compiler/configuration/binary identities, independent harness/expectations,
local check logs, live upstream refs, vendored schema and Rust patches against
both the previous candidate and upstream base. Its checksum is recorded in
`evidence/SHA256SUMS`. Executables/build products are excluded.
The local run is `suite/artifacts/rstyle-native-f7d4586`; the harness implementation is
compat revision `6d7ab6234ad17228ab377746874b0af5f290773c`.
The prior projection-candidate archive remains a historical record.
