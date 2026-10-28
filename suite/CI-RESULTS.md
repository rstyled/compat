# CI integration validation, 2026-10-28

The reusable [compatibility workflow](../.github/workflows/compat.yml) and
producer caller workflows are implemented and pushed. They run on pull
requests, default-branch pushes (including merges), and manual dispatch.
The Action summary and logs display every nonpassing required check; JSON,
raw results and exact inputs are downloadable. There is no JUnit output.
See [CI.md](CI.md) for trigger, revision and retention details.

Both earlier producer fixes have merged. Validation builds clean upstream
gstyle `1a47d25c7d62c18bbfa429ec3baafbf6cf6b7691` and rstyle
`5b1b4e09ba4762ffe402338b65fa4fd472e652b6`, using harness revision
`952c016a592e2ab53a5e4b23b6e9046c9cabe182`. The original baseline pins and
independent graph expectations remain unchanged. CI resolves selected refs to
immutable SHAs in a separate pins file and records the source-pinned compiler.

| Check | Result |
| --- | --- |
| Required extraction/runtime checks | 118/130 pass; 12 incomplete evidence failures |
| Independent graph expectations | 24/24 pass |
| Exact cross-language multigraph equivalence | 12/12 pass |
| Renaming/formatting graph invariance | 12/12 pass |
| Shared schema validation | 24/24 pass |
| Source identities, references and published span bounds | 24/24 pass |
| Worked branch source correspondence | 4/4 pass |
| Compilation and shared-input execution | Six pairs pass; 39 vectors, 78 results |
| Rust selected evidence | 12/12 pass |
| Go selected evidence | 12/12 incomplete; blocks the gate |
| Suite unit tests, including corrupted graphs and strict reporting | 20 pass |
| Shared schema/static fixture tests | 35 pass |
| Python used for final validation | 3.12; jsonschema 4.26.0, matching CI |
| actionlint 1.7.12, all three workflows | Pass |
| Hosted Ubuntu 24.04 workflow | Setup and both unit-test steps pass; compatibility gate exits 1; summary and artifact publication pass |
| Go `make check` and `make quality-gate` | Pass |
| Go required quality-baseline refresh | Timestamp/revision only; all metrics unchanged |
| Infrastructure negative control | Exit 2; explicit fatal error and blocked/not-run checks |

**Remaining failures:** the twelve entries in the generated `failures.json`
are Go's `evidence` check for each of six cases and both source variants.
Each records `node_extraction=approximated` and `conformance=non_conformant`
with the producer's reason and a path to the full raw evidence. Its
`pdg.incomplete-dependencies` warning remains in the producer evidence.
This is a failing build; no allowlist, warning-only policy or evidence upgrade
is applied. No semantic graph expectation or producer analysis was changed.

**Unsupported:** none of the selected fixture pairs or variants.
**Not run:** the producer-repository caller jobs (their new branches have no
open PRs yet), other platforms, Rust workspace tests for these workflow-only
changes, and corpus expansion. Local extraction validation ran on Linux ARM64
with Go 1.27.2; hosted CI selects Go from the producer's `go.mod` and runs on
Ubuntu 24.04 x86-64.

The existing [compat PR #10](https://github.com/rstyled/compat/pull/10) triggered
a real [hosted run](https://github.com/rstyled/compat/actions/runs/40643680312)
at workflow revision `7366049`. Setup, suite tests and schema tests passed;
the strict compatibility step failed with exit 1. Both failure-summary
publication and artifact upload succeeded. Current Node 24 cache/artifact
actions removed the earlier deprecation warning. Public job status,
annotations and artifact metadata are retained. Downloading the hosted logs
and raw artifact requires account authentication, which is unavailable here
(HTTP 403/401); the exact 118/130 breakdown above is established by the retained
local run. The hosted Action summary and downloadable artifact contain its own
failure list.

The producer integration branches are:

- gstyle [`ci/compat-suite`](https://github.com/rstyled/gstyle/tree/ci/compat-suite), commit `079e95e`.
- rstyle [`ci/compat-suite`](https://github.com/rstyled/rstyle/tree/ci/compat-suite), commit `31f7c0b`.

Both call the reusable workflow and check out its harness at the same exact
compat workflow revision `7366049` (executable harness unchanged from `952c016`).
The checks activate for future default-branch pushes
after the caller workflows merge. The manual Actions UI requires the workflow
on the default branch. Branch protection has not been changed. Git deploy keys
can push these branches; creating PRs or dispatching workflows through GitHub's
API requires account authentication, which is unavailable in this environment.

The retained local run is `suite/artifacts/ci-final-20261028`. The portable
[CI validation archive](evidence/ci-integration-20261028.tar.gz) includes the
generated failure list/report, exact sources, raw outputs, harness/expectations,
configuration/revision/compiler/binary identities, command logs, workflow
files, caller patches and validation logs. Compiled products are excluded;
its checksum is in `evidence/SHA256SUMS`. Earlier archives are unchanged.
