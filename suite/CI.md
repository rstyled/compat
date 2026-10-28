# Compatibility CI

[The workflow](../.github/workflows/compat.yml) runs the independent suite and
shared-schema tests, builds both producers, compiles and executes all six paired
programs, and requires exact graphs, schemas, evidence and source checks.
Every nonpassing required check fails the job, including incomplete evidence,
unsupported extraction and checks not run. No warning-only mode or baseline
exemption is used.

## Triggers and revisions

In `rstyled/compat`, the workflow runs on pull requests, pushes to `main`
(including merges), and **Actions → Go/Rust compatibility → Run workflow**.
Manual inputs `gstyle_ref` and `rstyle_ref` accept branches, tags or commits;
defaults are Go `master` and Rust `main`. Automatic runs use those defaults.

The same workflow supports `workflow_call`. Small caller workflows in gstyle
and rstyle run on their pull requests, pushes to their default branches and
manual dispatches. Each caller tests its triggering commit (the merge candidate
on a pull request) against the other producer's current default branch, with
manual overrides available for both refs. Callers pin both the reusable workflow
and the suite checkout to the same immutable compat commit. Update those two
references together when adopting a newer suite.

GitHub resolves selected producer refs during checkout; `ci_pins.py` records
the resulting immutable SHAs and the compiler identified by the selected Rust
checkout's `rust-toolchain.toml`. The runner still requires clean producer
checkouts and exact revision matches. CI writes separate pins rather than
modifying the original reviewed `suite/pins.json` or graph expectations.
The source-pinned Rust toolchain and its declared components are installed;
Go is selected from the checked-out producer's `go.mod`.

The workflows use read-only repository permissions and public checkouts; deploy
keys and write tokens are not required to run them. Reusable workflows must be
accessible under the repositories' GitHub Actions settings. Automatic merge
triggers and the manual UI become available when the respective workflow files
reach their default branches. A red check fails the workflow; making it a
required merge check is a separate branch-protection setting, not changed here.

## Failure list and evidence

Every completed extraction run now produces:

| File | Contents |
| --- | --- |
| `failures.json` | Every nonpassing required check, with case, variant, producer, status, reason and detail path |
| `report.md` | Readable failure table, totals and exact producer revisions |
| `summary.json` | Full per-case results and original producer evidence |
| `outcome.json` | Strict overall status and counts |

The console prints the readable report. CI appends it to the job summary and
always attempts to upload raw results and logs, including on a failing gate.
The artifact includes fixture and wrapper sources, identified source bytes,
raw PDGs/unit bundles, graph correspondences/mismatches, schema errors, command
logs, exact harness/expectations, configuration and revision/compiler/binary
identities. Compiled binaries and Cargo build products are excluded. Artifacts
are retained for 30 days; the repository's older evidence archives remain
unchanged.

Setup failures inside the runner produce `fatal.json`, a failure report and
exit 2; ordinary compatibility failures return 1. Setup/unit-test failures
before extraction remain red workflow steps and appear in the job summary;
the summary explicitly says when no extraction report was produced.

The goal is zero nonpassing checks. Until Go's evidence boundary is completed,
the known incomplete evidence remains visible as failing checks on every run.
CI does not change either analyzer's claims to obtain a green build.
