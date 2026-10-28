# Tiny Go/Rust extraction compatibility suite

Six explainable paired functions, independent exact expectations, and a runnable
pre-mining PDG harness. Start with [the contract](CONTRACT.md), then the fully
worked [branch reassignment](BRANCH.md). [CASES.md](CASES.md) lists every case's
expected structure and assumptions; [IMPLEMENTATION.md](IMPLEMENTATION.md) records
the verified producer paths and source evidence.

The pinned **latest upstream default heads checked on 2026-10-28** are Go
`e4cdf52` and Rust `419c20a`. Build from clean checkouts at the full revisions in
[pins.json](pins.json); Rust must use its source-pinned nightly compiler.

```sh
uv run --no-project --with jsonschema python -m unittest discover -s suite -p 'test_*.py'
uv run --no-project --with jsonschema python -m unittest discover -s schemas -p 'test_*.py'
uv run --no-project --with jsonschema python suite/run.py \
  --gstyle /path/to/clean/gstyle --rstyle /path/to/clean/rstyle
```

The runner rebuilds both producers. It requires Go, rustup with rstyle's pinned
rustc-dev toolchain, and each project's build dependencies. It uses existing Go
`patterns --format pdg-json` and Rust `RSTYLE_HIR_DOCUMENT_DIR` publication,
without analyzer edits or clone scoring. Its Python comparator uses only the
standard library; jsonschema validates the existing shared transport separately.
Commands assume the compat repository root as cwd. `--out` must name a new run
directory. `--rust-target` optionally reuses a Cargo build directory.

This suite is expected to exit **1 on the pinned producers**, because it exposes
real compatibility gaps. Exit 0 is reserved for full conformance; exit 2 reports
setup/infrastructure failure. It never updates expectations. Every run produces
`failures.json` and `report.md`, listing each nonpassing required
check, including incomplete evidence. The console prints the failure report.
See [CI.md](CI.md) for automatic merge/PR checks, manual runs against selected
producer refs, job summaries and downloadable raw results.

Retained [results](RESULTS.md) separate graph passes/failures, producer evidence,
transport failures, unsupported cases and work not run. Raw outputs, exact
original/renamed/wrapper sources, harness sources, schema/fixture snapshots,
compiler configuration, revision/binary digests, command stdout/stderr,
correspondences and complete mismatch reports are in
[evidence/latest-run.tar.gz](evidence/latest-run.tar.gz). Extract it with
`tar -xzf suite/evidence/latest-run.tar.gz -C /tmp` and inspect
`latest-run/summary.json` and each case's `original/result.json`.
The original executable/build artifacts remain in ignored `suite/artifacts/`;
the archive excludes compiled binaries and records their digests in manifest.json.

Renaming/formatting checks run both producers on changed source text. Comparator
tests additionally reject altered literals, types, positions, outcomes, binding
and definition references, direction, edge multiplicity, extra merges, and a
six-cycle versus two triangles having the same labels, counts and degrees.
The official [Go Specification and Rust Reference](references/README.md) resolve
the relevant language semantics; no guide or existing snapshot is treated as
producer proof.

The [native PDG model candidate](RSTYLE-NATIVE-PDG.md) compares unmerged Go PR
#296 at `15f1681` with Rust `f7d4586`. The legacy transport machinery and
its compatibility tests are deleted. All independent graphs, cross-language
comparisons, runtime checks and shared schemas pass. The full harness still
reports incomplete Go evidence. The previously reported renamed Rust span
failure was a harness coordinate error: spans reference identified function
bytes, not the full file. See the [source-span correction](SOURCE-SPANS.md) for
the verified correspondence, corruption checks and retained rerun.
Original failing pins and expectations remain unchanged.
