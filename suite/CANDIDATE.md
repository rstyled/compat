# Go scalar graph fix candidate

Candidate gstyle revision `e8e1baf5cd4b71325ae730bc69a66df02b3e0275`
([branch](https://github.com/rstyled/gstyle/tree/fix/scalar-pdg-compatibility))
was tested against rstyle `419c20a7d2322de9b976c6c2f2f856ad0ce68e98`.
Both base upstream heads were checked on 2026-10-28. The original failing run,
original pins and handwritten expectations remain unchanged.

| Check | Result |
| --- | --- |
| Independent graph expectations | 24/24 pass: six cases, two producers, original and renamed |
| Exact cross-language labeled directed multigraph comparison | 12/12 pass |
| Renaming/formatting graph invariance | 12/12 pass |
| Shared-input compilation/execution | All six pairs pass, 39 vectors |
| Go shared transport schema | 12/12 pass |
| Rust shared transport schema | 12/12 fail: obsolete policy fields and conformance array |
| Producer evidence | Go incomplete (approximate nodes/nonconformance); Rust passes selected capability checks |
| Branch source correspondence | Original Go/Rust and renamed Go pass; renamed Rust fails |
| Harness/comparator tests | 13 pass; includes deliberately corrupted graphs |
| Existing schema fixture tests | 35 pass |
| Gstyle export schema test (explicit schema configuration) | Pass |
| Gstyle repository checks | `make check`, `make cognitive`, `go vet -buildvcs=false ./...`, `make quality-gate` pass |

The source-correspondence failure already occurs in the original retained run.
For the renamed Rust branch, the first `input_value` occurs at byte 61, while
its exported formal-input span is `[15,26)`: exactly 46 bytes earlier, the
length of the leading formatting comment. The raw output is retained and no
span correction is applied. This source mapping failure is reported separately
from the matching semantic graph. No graph expectation was regenerated.

Go now exports direct source-definition edges at joined scalar reads, retaining
both arm definitions and excluding the killed initialization. Short-circuit
alternatives export the predicate/outcome explicitly in `gstyle.go:guards`.
The adapter recognizes that namespace using the same atom structure as Rust's
existing namespace; it does not infer guards, change slots, or splice merges.
The runner's optional `--pins` selects an explicit reviewed candidate while
keeping the original failing pins as the default.

Reproduce from clean producer checkouts at those revisions:

```sh
uv run --no-project --with jsonschema python suite/run.py \
  --pins suite/candidates/gstyle-scalar-fix.json \
  --gstyle /path/to/gstyle --rstyle /path/to/rstyle \
  --rust-target /path/to/cached-rust-build --out /path/to/new-results
```

Exit 1 remains expected because full compatibility includes schema validity,
source correspondence, and producer evidence. No selected case is unsupported;
no required six-case check was skipped. Loops, language-specific mechanisms,
race testing and Lean verification were not run for this candidate.

`suite/evidence/gstyle-scalar-fix.tar.gz` retains the complete textual run:
exact fixture sources, raw PDG/bundle exports, manifests with compiler versions,
configuration and binary digests, command stdout/stderr and exit codes,
normalized graphs, correspondences and separate result records. It also retains
the gstyle commit patch, repository check logs, required quality-baseline refresh,
and a review of gstyle findings for the changed routines. Full self-analysis
facts remain locally at `/tmp/gstyle-scalar-compat-quality/gstyle-facts.json`.
The original run remains in `suite/evidence/latest-run.tar.gz`.
