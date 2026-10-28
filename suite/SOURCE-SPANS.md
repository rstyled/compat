# Source-span diagnosis and correction

The renamed Rust branch fixture's exported spans are correct. The earlier
failure was in `run.py`: it searched the complete file and compared character
indices with byte spans into a captured function fragment. No Rust producer,
exported span, graph comparator or independent graph expectation was changed.
The correction is compat commit `fd3847304cb1f9559222de76c8ae72cefa536888`.

## Exact correspondence

For `branch/renamed/f.rs`, the retained fixture is 262 bytes. The compiler bundle
records the selected function at file bytes `[46,260)`. The embedded CFG source
is exactly those 214 bytes; its identity agrees with the PDG and capture digest:

`sha256:15efe238b0ee753301ddcc9def7f2b6fc4e1d8802c72d059324ce4f8621d3328`

The PDG formal-input node `n0` has span `[15,26)` in that identified content.
It covers `input_value`, which begins at file byte `46 + 15 = 61`. Comparing
`15` directly with `61` was the harness error. The shared
[span schema](../schemas/pdg.schema.json) specifies offsets into identified
source content; the [Rust profile](../schemas/rust-extraction-profile.md)
requires exact UTF-8 bytes and their SHA256 identity. A navigation path does
not require the content to be an entire file.

`source_correspondence.py` now resolves and verifies the identified bytes before
checking anchors. For Rust it verifies the exact fixture snapshot, captured
range, function span, digest and embedded CFG source. For Go it verifies the
whole fixture identity. It checks published function/node span bounds and source
references, then computes branch anchor positions as UTF-8 byte offsets.
Raw PDGs and offsets are never rewritten. Both producers' exact identified
source bytes and source-to-node maps are retained.

## Verified results

The rerun uses clean Rust `f7d45862df5ac7278c4684656e56075e9bde118b` on
`fix/current-pdg-transport` and Go `15f168134328241a7c5347b5a16a0b740f3a649e`
on the **unmerged** [PR #296](https://github.com/rstyled/gstyle/pull/296) branch.
Remote refs were checked again on 2026-10-28; upstream main/master remained
Rust `419c20a` and Go `e4cdf52`. Full refs and configuration are archived.

| Check | Result |
| --- | --- |
| Independent graph expectations | 24/24 pass |
| Exact cross-language multigraph equivalence | 12/12 pass |
| Real renaming/formatting graph invariance | 12/12 pass |
| Shared schema validation | 24/24 pass |
| Identified content, source references and published span bounds | 24/24 pass |
| Branch token-to-node correspondence | 4/4 pass, including renamed Rust |
| Compilation and shared-input execution | Six pairs pass; 39 vectors, 78 results |
| Comparator, adapter and source unit tests | 17 pass |
| Shared schema/static fixture unit tests | 35 pass |
| Deliberately corrupted real Rust source evidence | Five rejected as required |
| Rust selected extraction evidence | 12/12 pass |
| Go extraction evidence | 12/12 incomplete |
| Full harness | Exit 1, solely because Go evidence remains incomplete |

Synthetic independent tests also cover Unicode, BOM and CRLF prefixes, offsets
incorrectly measured in characters, shifted spans, split UTF-8 code points,
invalid bounds/references, inconsistent snapshots/digests/captured ranges/CFG
content, missing spans and ambiguous anchors. Real renamed-branch corruption
reports include the modified span and the expected token interval/candidate
spans, or the specific identity/reference disagreement. The old erroneous
whole-file offsets are explicitly rejected.

**Failures:** no graph, schema, source, execution or unit-test failure remains
in this run. **Incomplete:** Go still reports approximated node extraction,
nonconformance and `pdg.incomplete-dependencies`; observed graph matches do not
upgrade those claims. **Unsupported:** none of the selected pairs/variants.
**Not run:** remote CI, other platforms, loops/language-specific cases, and full
token correspondence for the other five cases. Rust workspace/style tests were
not rerun because the producer did not change; their earlier results remain in
the [native-model evidence](RSTYLE-NATIVE-PDG.md).

Reproduce with the command in [RSTYLE-NATIVE-PDG.md](RSTYLE-NATIVE-PDG.md), choosing
a new `--out` directory. The local rerun is
`suite/artifacts/source-spans-f7d4586`. The portable
[source-span archive](evidence/source-spans-f7d4586.tar.gz) retains exact
sources/wrappers, raw producer outputs, identified source content, identity
proofs, source/graph correspondences, summaries, command logs, revisions,
configuration and the exact harness/independent expectations used. Checksums
are in `evidence/SHA256SUMS`; compiled products are excluded. Historical
archives remain unchanged, with their incorrect span diagnosis annotated in
the corresponding reports.
