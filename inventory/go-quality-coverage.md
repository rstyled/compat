# Go quality source audit — coverage and resumption ledger

**Status: PARTIAL checkpoint.** All production and test files in the five requested directories were read. Fixture/support review is incomplete, compiler/package-loader internals are not audited, and Rust/CCGraph comparisons are not established. This is phase-one documentation only, not an implementation change or a completed whole-workspace audit.

Owned outputs:

- [inventory/algorithms/go-quality.md](algorithms/go-quality.md): **35 source-backed algorithm records**, with guards, numeric details, line-linked symbols, callers/activation, pseudocode, tests, limitations, costs and distinguishing fixture designs.
- This ledger: snapshot, per-file depth, tests, explicit unfinished files and prioritized handoff.

## Snapshot and provenance

| Item | Observed / boundary |
|---|---|
| Embedded Go repository | `gstyle`, clean `git status --short`, HEAD `598c7b03366caa0fef70f66aa58e76222eefb8fa` |
| Parent compat repository | HEAD `edbffe58846f8809d1244c7fa2ee5383b8e3b087`; initial status listed untracked `.gitignore`, `ALGORITHM_UNIFICATION.md`, `PHASE_ONE_INVENTORY_PROMPT.md`, `ccgraph-divergences.md`, `ccgraph_paper.pdf`, `gstyle/`, `rstyle/`. Parent HEAD does **not** identify child source; no reset/checkout was performed. |
| Host/toolchain | macOS, `go version go1.26.2 darwin/arm64`; module declares Go `1.25.0` |
| Module identity | `github.com/shanejonas/cyclo` |
| Prompt / instructions | `PHASE_ONE_INVENTORY_PROMPT.md` read in full; `gstyle/AGENTS.md` read in full. Baseline/golden update agreements do not authorize such updates for this explicitly source-only audit. |
| Supporting plan | `ALGORITHM_UNIFICATION.md` L1–160 read as discovery/context, not proof; remainder unreviewed by this slice. |
| Audit input evidence | Source and test assertions inspected, not executed; no observed algorithm outputs or performance measurements. |

### Snapshot content identifiers

The five Git tree object IDs (all at the recorded clean child HEAD):

```text
adapters/gocyclo          fa9a66165b9a607b8ab12cb8e36530f40565ac1e
adapters/goquality        ee7018f9a3ece568087b6d6018fd55be62265bd4
application/qualitycheck  ffb538d8c162f6fced50c74001e8e9e474312f09
application/qualitygate   9151c8d8d62c2933cbe5d84f71767a2465cf3fcb
domain/quality            e22de5e3296bdb05ddba25485c29aeb9b729a63a
```

SHA-256 inputs:

```text
go.mod                        fd2a6d6efea5a2a2941286e993c76157766d0f378aa9ce6a70bfe37c0fa37524
go.sum                        da397e994a67a4ac36550c9e9add6d32eec6d8fdd59d3e0b9ac769ac869d03e8
PHASE_ONE_INVENTORY_PROMPT.md  a9eb84a87ee9a0a874d4b7911f34010dcbfb41d592c51ae36fc97deea4a1f2c5
gstyle/AGENTS.md               d57ef18d01a54a8175292c64f505f85c3d713c6aef2f2f82a3c44acdaa0def37
scope content manifest        680eafde98d49bb71400852f058c82548119b828495c5676276b3b57ee52cc17
```

Manifest construction: all **90 files** recursively under the five scoped directories, sorted by `gstyle`-relative path; each row is `path + NUL + sha256(file bytes).hexdigest() + LF`; SHA-256 of the concatenated UTF-8 rows. This hash covers unreviewed fixture bytes as snapshot identification, **not evidence of review**. No manifest file was written outside the two owned outputs.

## Counts and depth definitions

- **Full source**: every line in that production file read and meaningful branches traced into records. This is not a proof of behavior under every compiler input.
- **Full test assertion**: every line in that test file read, assertions/fixture dependencies mapped; no test execution.
- **Fixture source**: file text read and related to producer/test assertion; original reducer process or runtime result not reproduced.
- **Boundary region**: only listed source lines/test symbols inspected outside the requested directory scope.
- **Enumerated only**: path/hash counted; contents not reviewed. Explicitly unfinished, not silently excluded.

| Scope (`gstyle/` prefix) | Production full / denominator | Test files full / denominator | Top-level `func Test` symbols inspected / denominator | Fixtures full-source / denominator |
|---|---:|---:|---:|---:|
| `domain/quality` | 10/10 | 6/6 | 50/50 | 0/0 |
| `adapters/goquality` | 7/7 | 10/10 | 28/28 | 17/40 |
| `adapters/gocyclo` | 4/4 | 6/6 | 14/14 | 0/0 |
| `application/qualitycheck` | 3/3 | 2/2 | 11/11 | 0/0 |
| `application/qualitygate` | 1/1 | 1/1 | 11/11 | 0/0 |
| **Total** | **25/25** | **25/25** | **114/114** | **17/40** |

**67/90 scoped files had full content review; 23/90 are enumerated-only unfinished fixture/support files.** Non-fixture Go source+test lines total **8,120**, as measured by `wc -l`. Fixture `sample_test.go` is counted in the fixture denominator, not the 25 test-file/114-symbol denominator. Subtests/table rows are described but not counted as separate top-level symbols. Boundary reviews below are additional and do not inflate these counts. **Tests executed: 0/114**; fixtures/reducers executed: 0.

## Production-file ledger (25/25 full source)

Paths link to the audited file; algorithm names are stable IDs in the companion report. All rows are **full source**, no unreviewed production region remains inside these five directories.

| File | IDs / decisive regions |
|---|---|
| [domain/quality/facts.go](../gstyle/domain/quality/facts.go#L1-L241) | `facts.go-quality-schema`, `facts.go-parameter-arguments`, `facts.go-report-join`, `effects.go-density`, `refactor.go-parameter-plan`; all raw/report/helper/DDD/plan fields and JSON omissions |
| [domain/quality/config.go](../gstyle/domain/quality/config.go#L1-L186) | `quality.go-config`, `effects.go-prefix-classification`; defaults and all validators, including missing DDD limit checks |
| [domain/quality/evaluate.go](../gstyle/domain/quality/evaluate.go#L1-L383) | `facts.go-function-identity`, `quality.go-guardrails`, `effects.go-density`, `effects.go-prefix-classification`, all three `quality.go-ddd-*`; entire orchestration, rule guards, target keys, normalization and summary math |
| [domain/quality/validate.go](../gstyle/domain/quality/validate.go#L1-L72) | `facts.go-quality-schema`; missing parameter/Args/DDD validators explicitly recorded |
| [domain/quality/helper_validate.go](../gstyle/domain/quality/helper_validate.go#L1-L31) | `facts.go-quality-schema`; normalized helper uniqueness and body validation |
| [domain/quality/local_calls.go](../gstyle/domain/quality/local_calls.go#L1-L135) | `effects.transitive-summary`, `effects.go-prefix-classification`; prefix priority, depth32/effects4096, cache, cycles, truncation, Via |
| [domain/quality/stdlib.go](../gstyle/domain/quality/stdlib.go#L1-L531) | `effects.go-prefix-classification`; **entire table** L28–492 plus prefix expansion/cached public API L495–531 read; policy correctness not established by reading |
| [domain/quality/suppression.go](../gstyle/domain/quality/suppression.go#L1-L88) | `quality.go-suppression`, `quality.go-guardrails`; all 12 registered strings, lint parser, reason and unsuppressible guard |
| [domain/quality/groups.go](../gstyle/domain/quality/groups.go#L1-L265) | `refactor.go-call-graph`, `refactor.go-fix-groups`, `refactor.go-stack-order`; public API, position/name indices, reverse graph, hops, DSU, fallback |
| [domain/quality/stacking.go](../gstyle/domain/quality/stacking.go#L1-L432) | `refactor.go-call-graph`, `refactor.go-parameter-plan`, `refactor.go-pass-through`, `refactor.closed-parameter-bundles`; all helpers including unused `setKey`, one-round candidate closure, singleton production activation |
| [adapters/goquality/analyzer.go](../gstyle/adapters/goquality/analyzer.go#L1-L250) | `extraction.go-package-selection`, `extraction.go-function-discovery`, `facts.go-function-identity`, `effects.go-helper-evidence`; entire selection/error/physical/discovery flow |
| [adapters/goquality/function.go](../gstyle/adapters/goquality/function.go#L1-L351) | `quality.go-counts`, `facts.go-parameter-arguments`, `mutation.go-place-events`, `effects.go-intrinsic`, `effects.go-call-resolution`, `quality.go-suppression`, three `quality.go-ddd-*`; closures, globals, names, scanners, docs |
| [adapters/goquality/mutation.go](../gstyle/adapters/goquality/mutation.go#L1-L333) | `mutation.go-binding-provenance`, `mutation.go-place-events`, `mutation.go-value-array`; all place/projection/alias/allocation/field cases |
| [adapters/goquality/array_type.go](../gstyle/adapters/goquality/array_type.go#L1-L38) | `mutation.go-value-array`; arrays, interfaces/intersections, union all-terms guard |
| [adapters/goquality/call.go](../gstyle/adapters/goquality/call.go#L1-L195) | `effects.go-call-resolution`, `facts.go-parameter-arguments`, `effects.go-intrinsic`; all call-type/builtin/dynamic/peeling paths |
| [adapters/goquality/helpers.go](../gstyle/adapters/goquality/helpers.go#L1-L42) | `effects.go-helper-evidence`; normalized-name last-wins index and LIFO reachability |
| [adapters/goquality/report.go](../gstyle/adapters/goquality/report.go#L1-L89) | `facts.go-report-join`; status/error demotion, absolute input paths, positional attachment and facts-index assumption |
| [adapters/gocyclo/analyzer.go](../gstyle/adapters/gocyclo/analyzer.go#L1-L414) | `extraction.go-syntax-selection`, `extraction.go-physical-mapping`, `quality.go-cyclomatic`, `quality.go-cognitive`; raw traversal, dependency calls, score diagnostics, summary and ordering |
| [adapters/gocyclo/literal.go](../gstyle/adapters/gocyclo/literal.go#L1-L41) | `extraction.go-physical-mapping`; parenthesized ValueSpec AST normalization and per-variable names |
| [adapters/gocyclo/position.go](../gstyle/adapters/gocyclo/position.go#L1-L12) | `extraction.go-physical-mapping`; rebuilt FileSet drops line remaps |
| [adapters/gocyclo/diff.go](../gstyle/adapters/gocyclo/diff.go#L1-L144) | `extraction.go-physical-mapping`; branch-tip selection, literal source diff, deletion+1 anchoring, inclusive span variants |
| [application/qualitycheck/cli.go](../gstyle/application/qualitycheck/cli.go#L1-L275) | `facts.go-saved-facts`, `quality.go-config`, `quality.go-changed-filter`, `refactor.go-parameter-plan`; modes/options/evaluation/export/filter/error order. Rendering fully read but secondary, no separate rendering algorithm ID |
| [application/qualitycheck/config.go](../gstyle/application/qualitycheck/config.go#L1-L46) | `quality.go-config`; default retention, appended prefixes and unknown TOML keys |
| [application/qualitycheck/gitchanged.go](../gstyle/application/qualitycheck/gitchanged.go#L1-L40) | `quality.go-changed-filter`; source newline span, path+name identity, diagnostic-only rebuild |
| [application/qualitygate/main.go](../gstyle/application/qualitygate/main.go#L1-L332) | `quality.go-excess-ratchet`; entire supporting command source, aggregate/rate bands, current-only rule loop, IO decoding and baseline writer (not run) |

## Test-family ledger (25/25 full assertion review)

Every symbol named below was inspected; **none executed**. Inline source fixtures in these files were read in full. The IDs map families to the algorithm records, not to an asserted passing status.

### Domain tests: 6 files, 50 top-level tests

| File / depth | Exact symbols and established assertions | IDs |
|---|---|---|
| [evaluate_test.go L1–332](../gstyle/domain/quality/evaluate_test.go#L1-L332), full | `TestMutationBudgetsAndProvenance` (root/field, local density0), `TestPurePrefixesClassifyAsNone`, `TestPureStdlibCallsScoreZero`, `TestRealEffectsStillFail` (2300 milli), `TestDensityFindingExplainsItself` (weight6/statements10/milli600), `TestClassificationLongestPrefixAndUnknownCoverage`, `TestCalleeNormalizationPreservesPlainAndMalformedNames`, `TestStrictLimitsAndMinimumStatements`, `TestSuppressionsRequireReasonAndKnownRules`, `TestDeterminismDeduplicationAndInputImmutability`, `TestShadowedRootsRemainDistinct`, `TestInvalidBoundaries`, `TestMeanUsesExactIntegerMath` | `quality.go-guardrails`, `quality.go-counts`, `quality.go-suppression`, `quality.go-config`, `facts.go-function-identity`, `facts.go-quality-schema`, `effects.go-density`, `effects.go-prefix-classification`, `mutation.go-place-events` |
| [local_calls_test.go L1–233](../gstyle/domain/quality/local_calls_test.go#L1-L233), full | `TestHelperResolutionPreservesPolicyAndCallsiteEvidence`, `TestHelperResolutionKeepsMissingAndDynamicBodiesUnknown`, `TestHelperSummaryLimitsStayUnknown` (depth32/effects4096), `TestHelperFactsRejectInvalidAndConflictingBodies`, `TestGenericHelperNamesShareLookupAndPolicy`, `TestCombinedCallLimitPreservesEarlierEvidence`, `TestCallLimitReservesRoomForUnknownEvidence` (4096 exact vs overflow), `TestRecursiveHelperKeepsKnownEffects`, `TestInheritedEffectsNameImmediateHelper`, `TestNestedHelperViaNamesImmediateCallee`, `TestViaUsesShortPackageQualifiedName` | `effects.transitive-summary`, `effects.go-prefix-classification`, `facts.go-quality-schema`, `effects.go-density` |
| [groups_test.go L1–222](../gstyle/domain/quality/groups_test.go#L1-L222), full | `TestBuildFixGroups` (10 table cases: unrelated, caller signature, non-signature, configured rule, shared clean hub, one-hop, two-hop, cycle, empty, dynamic/external); `TestBuildFixGroupsRejectsConflictingFacts`; `TestGroupingConfigValidation` | `refactor.go-call-graph`, `refactor.go-fix-groups`, `refactor.go-stack-order`, `quality.go-config`, `facts.go-function-identity` |
| [stacking_test.go L1–319](../gstyle/domain/quality/stacking_test.go#L1-L319), full | `TestClosedSetsDropSubsetsWithEqualSupport`, `TestClosedSetsKeepSmallerSetWithMoreSupport`, `TestClosedSetsIgnoreSingletonsAndEmpty`, `TestForwardsPairCallerAndCalleePositions`, `TestForwardsIgnoreOutOfRange`, `TestStackSitesSkipDynamicAndUnresolved`, `TestNoPlanWithoutFnParamsViolation`, `TestPlanListsCalleeSignatureThenCallSiteEdits`, `TestPlanOrdersViolatingCallersAfterCallees` (internal helper only), `TestBundleIsParamsForwardedTogether`, `TestConstantsAndFieldsDoNotBundle`, `TestBundleSupportCountsSitesAcrossCallers`, `TestOnlyForwardedParamIsPassThrough`, `TestUnusedParamIsNotPassThrough`, `TestPlanIsDeterministicUnderCallerOrder` (by input index, not lexical name), `TestPlanFindingsOnlyForFnParams` | All five `refactor.go-*` IDs and `refactor.closed-parameter-bundles` |
| [ddd_test.go L1–94](../gstyle/domain/quality/ddd_test.go#L1-L94), full | `TestDDDAggregateRule`, `TestDDDAggregateRuleSingleTypeOK`, `TestDDDRepositoryRule`, `TestDDDMutableIdentityRule`, `TestDDDRulesSuppressible`; hand-built facts test evaluation, **not frontend extraction** | `quality.go-ddd-aggregate`, `quality.go-ddd-repository`, `quality.go-ddd-mutable-identity`, `quality.go-suppression` |
| [stdlib_test.go L1–64](../gstyle/domain/quality/stdlib_test.go#L1-L64), full | `TestStdlibCoverage`: `go list std`, exclude internal/vendor packages, require **any** prefix for each package; not all APIs. `TestImportable`: path eligibility predicates | `effects.go-prefix-classification`; supporting toolchain-dependent coverage method |

### Typed adapter tests: 10 files, 28 top-level tests

| File / depth | Exact symbols / assertions / external fixture dependency | IDs |
|---|---|---|
| [analyzer_test.go L1–215](../gstyle/adapters/goquality/analyzer_test.go#L1-L215), full | `TestTypedWritesAndAliasProvenance` (11 writes, shadow/capture IDs), `TestCallsUseTypesRatherThanMutatorNames`, `TestFixtureGoldenAndDoubleRun` (golden file **unreviewed**, update flag exists but not used), `TestSelectionTagsAndIncompletePackages`, `TestCodeLinesIgnoreCommentsAndPreserveStrings`, `TestTupleAliasesAndTemporaryTargetsStayVisible`, `TestUnsafeUsesTypesAndExcludesSizeof`, `TestSelfCheckProducesValidReport` (skips under Short; self-source package extraction); sample fixtures listed below | extraction IDs, `facts.go-function-identity`, `mutation.go-binding-provenance`, `mutation.go-place-events`, `effects.go-call-resolution`, `effects.go-intrinsic`, `quality.go-counts` |
| [aliasing_test.go L1–68](../gstyle/adapters/goquality/aliasing_test.go#L1-L68), full | `TestReducedAliasingMutationsRemainVisibleInQuality`: indirect/range/allocated-wrapper reduced sources, unknown density and 2 write events. `TestAliasingProvenancePreservesOwnedStorage`:10 inline cases covering owned arrays/append, address, range and wrappers | `mutation.go-binding-provenance`, `mutation.go-place-events`, `facts.go-report-join`, `effects.go-density` |
| [args_test.go L1–100](../gstyle/adapters/goquality/args_test.go#L1-L100), full | `TestArgProvenanceClassification`, `TestArgFieldThroughReceiver`, `TestParamListNamesTypesAndUses`; args source fixture read; no StarExpr dereference assertion | `facts.go-parameter-arguments`, `quality.go-counts`, `refactor.go-call-graph` |
| [closure_parameter_test.go L1–61](../gstyle/adapters/goquality/closure_parameter_test.go#L1-L61), full | `TestReducedClosureParameterMutationIsExternal`; `TestClosureParametersAndOwnedLocalsKeepTheirProvenance`: nested/closure reference parameters stay external even with dead owned reassignment; value parameters and owned locals local | `extraction.go-function-discovery`, `mutation.go-binding-provenance`, `mutation.go-place-events`, `effects.go-density` |
| [generic_array_test.go L1–79](../gstyle/adapters/goquality/generic_array_test.go#L1-L79), full | `TestGenericArrayStorageUsesValueOwnership`:9 inline constraint cases; `TestReducedGenericArrayCopyIsEffectFree`; `TestParenthesizedAllocationsKeepOwnedStorage`:4 inline callee-parenthesis cases | `mutation.go-value-array`, `mutation.go-binding-provenance`, `effects.go-call-resolution` |
| [local_helpers_test.go L1–134](../gstyle/adapters/goquality/local_helpers_test.go#L1-L134), full | `TestLocalHelpersClassifyEffectsConservatively`: pure chain/generic/method, mutation/IO/global, direct/mutual recursion, callback unknown; `TestHelperFactsSurviveFileSelectionAndPolicyReevaluation`: generated helper in unselected file preserved through JSON then policy override, immutability | `effects.go-helper-evidence`, `effects.transitive-summary`, `extraction.go-package-selection`, `facts.go-saved-facts`, `effects.go-prefix-classification` |
| [parenthesized_place_test.go L1–64](../gstyle/adapters/goquality/parenthesized_place_test.go#L1-L64), full | `TestReducedParenthesizedAssignmentKeepsMutationEffect`; `TestParenthesizedPlacesMatchUnwrappedPlaces`:7 inline cases, shared pointer/slice, owned, dead branch, tuple, blank discard/mixed blank | `mutation.go-binding-provenance`, `mutation.go-place-events`, `effects.go-density` |
| [promoted_pointer_test.go L1–77](../gstyle/adapters/goquality/promoted_pointer_test.go#L1-L77), full | `TestReducedPromotedPointerMutationHasQualityEvidence`; `TestSelectorMutationProvenanceRespectsPointerIndirection`:7 cases including nested promotion, field address, explicit pointer field, type alias, value copy, parameter | `mutation.go-place-events`, `mutation.go-binding-provenance`, `facts.go-report-join`, `effects.go-density` |
| [report_test.go L1–60](../gstyle/adapters/goquality/report_test.go#L1-L60), full | `TestReportJoinsTypedEvidenceToComplexityFunctions`: Writes typed positional join/11 MutationEvents; `TestTypeErrorsKeepComplexityReportAvailable`: ready complexity + quality error, no false clean typed success | `facts.go-report-join`, `extraction.go-syntax-selection`, `extraction.go-package-selection` |
| [suppression_comment_test.go L1–72](../gstyle/adapters/goquality/suppression_comment_test.go#L1-L72), full | `TestReducedSuppressionStringIsNotAComment`; `TestSuppressionReadsParsedDeclarationComments`:7 source-prefix cases, docs after directive, missing reason, block comment, raw/ordinary strings, blank-separated and trailing comments | `quality.go-suppression`, `extraction.go-function-discovery` |

### Syntax adapter tests: 6 files, 14 top-level tests

| File / depth | Exact symbols / assertions | IDs |
|---|---|---|
| [analyzer_extra_test.go L1–137](../gstyle/adapters/gocyclo/analyzer_extra_test.go#L1-L137), full | `TestAnalyzerCapturesFunctionSource`: EndLine8, cognitive1/diagnostic line4, cyclo diagnostic count; `TestAnalyzerCapturesTheWorkingTreeDiffFromMainOrMaster`: two temporary Git branch scenarios; `TestDeletionOnlyHunksStayBetweenTheirCurrentLines`: deletion new anchor4; `TestAnalyzerScoresFunctionLiteralReproducer`:cyclo2/cognitive1/zero-nesting literal | `quality.go-cyclomatic`, `quality.go-cognitive`, `extraction.go-physical-mapping`, `extraction.go-syntax-selection` |
| [diff_boundary_test.go L1–42](../gstyle/adapters/gocyclo/diff_boundary_test.go#L1-L42), full | `TestMixedHunkPositionsIncludeContextLines`; `TestDeletionOnlyHunkBoundaries`: before first/inside/after last line, ignored no-newline marker | `extraction.go-physical-mapping` |
| [literal_test.go L1–62](../gstyle/adapters/gocyclo/literal_test.go#L1-L62), full | `TestFunctionVariableNames`: tuple/group/nonfunction-first names; `TestNestedLiteralCognitiveNesting`: nested literal adds nesting, score4, inner increment3 at nesting2 | `extraction.go-physical-mapping`, `quality.go-cognitive` |
| [pathspec_test.go L1–47](../gstyle/adapters/gocyclo/pathspec_test.go#L1-L47), full | `TestGitDiffTreatsSourceFilenameLiterally`:4 special names (`[ab].go`, `*.go`, `?.go`, `:(glob)*.go`); unrelated file diff excluded | `extraction.go-physical-mapping`; contrasts changed-filter pathspec boundary |
| [source_repro_test.go L1–53](../gstyle/adapters/gocyclo/source_repro_test.go#L1-L53), full | `TestParenthesizedFunctionLiteral`, `TestLineDirectiveUsesPhysicalSourceLocations`, `TestMinimizedSourceReproducers`, `TestParenthesizedLiteralNamesAndIgnore` | `extraction.go-physical-mapping`, `quality.go-cyclomatic`, `quality.go-cognitive` |
| [textconv_test.go L1–44](../gstyle/adapters/gocyclo/textconv_test.go#L1-L44), full | `TestGitDiffUsesSourceInsteadOfTextConversion`: temporary Git textconv configured, raw before/after source asserted | `extraction.go-physical-mapping` |

### Application tests: 3 files, 22 top-level tests

| File / depth | Exact symbols / assertions | IDs |
|---|---|---|
| [qualitycheck/cli_test.go L1–234](../gstyle/application/qualitycheck/cli_test.go#L1-L234), full | `TestSavedFactsCanBeReevaluatedWithoutCompiler`, `TestConfigDefaultsOverridesAndValidation`, `TestCLIHelpAndInvalidInput`, `TestOutputErrorsAreOperationalFailures`, `TestMissingSavedFactsIsAnOperationalFailure`, `TestFactsVersionsKeepHelperEvidenceAndLegacyUncertainty`, `TestFactsExportIncludesSelectedFunctionHelperBodies`, `TestWriteTextRendersFixGroups`, `TestGroupingConfigTOML` | `facts.go-saved-facts`, `quality.go-config`, `effects.go-helper-evidence`, `effects.transitive-summary`, `refactor.go-fix-groups`; output rendering secondary |
| [qualitycheck/gitchanged_test.go L1–160](../gstyle/application/qualitycheck/gitchanged_test.go#L1-L160), full | `TestTouchedFunctions`; `TestChangedEndToEnd`: temp repository clean/dirty, explicit HEAD/unknown base; scoped adapter reports only touched finding | `quality.go-changed-filter` |
| [qualitygate/main_test.go L1–181](../gstyle/application/qualitygate/main_test.go#L1-L181), full | `TestAggregateSumsExcess`, `TestAggregateRejectsInconsistentLimits`, `TestCheckBaselinePassesOnIdenticalReport`, `TestCheckBaselineTripsOnNewFinding`, `TestCheckBaselineTripsOnWorsenedFinding`, `TestCheckBaselineTripsOnImprovement`, `TestCheckBaselineIgnoresNoise`, `TestCheckBaselineScalesWithGrowth`, `TestCheckBaselineTripsOnUnbaselinedRule`, `TestCheckBaselineRejectsPolicyChange`, `TestWorstOffendersOrderedByExcess` | `quality.go-excess-ratchet`; reduced excess still present tested, vanished rule not tested |

## Fixture/support file ledger (17 reviewed, 23 explicitly unfinished)

All paths below are relative to `gstyle/adapters/goquality/testdata/`. No fixture or support script was run or rewritten. All 40 files are accounted for. Reviewed reducer outputs are test inputs; their filenames do not prove the historical reduction or cross-engine result.

### Reviewed fixture sources (17/40)

| Exact file | Depth / related algorithms / inspected meaning |
|---|---|
| [aliasing/allocated-wrapper-reduced.go.txt](../gstyle/adapters/goquality/testdata/aliasing/allocated-wrapper-reduced.go.txt) | Entire7 lines; local new embedded-pointer wrapper assigned shared then promoted Count++; `mutation.go-place-events`, `mutation.go-binding-provenance` |
| [aliasing/indirect-reduced.go.txt](../gstyle/adapters/goquality/testdata/aliasing/indirect-reduced.go.txt) | Entire8 lines; address of local pointer then indirect shared assignment; provenance poisoning |
| [aliasing/range-reduced.go.txt](../gstyle/adapters/goquality/testdata/aliasing/range-reduced.go.txt) | Entire7 lines; range assignment aliases existing local pointer; unknown binding |
| [args/args.go](../gstyle/adapters/goquality/testdata/args/args.go) | Entire27 lines; explicit literal/named-constant/parameter/&parameter/field/computed args, receiver field and Uses; `facts.go-parameter-arguments` |
| [closure-parameters/reduced.go.txt](../gstyle/adapters/goquality/testdata/closure-parameters/reduced.go.txt) | Entire9 lines; dead owned reassignment inside closure does not erase external parameter origin |
| [closure-parameters/treesitter-reduced.go.txt](../gstyle/adapters/goquality/testdata/closure-parameters/treesitter-reduced.go.txt) | Entire file; same syntactic shape with spacing; no treesitter/original reducer executed |
| [generic-array-copy/reduced.go.txt](../gstyle/adapters/goquality/testdata/generic-array-copy/reduced.go.txt) | Entire file; `T ~[1]int` local indexed value copy; `mutation.go-value-array` |
| [parenthesized-places/blank-reduced.go.txt](../gstyle/adapters/goquality/testdata/parenthesized-places/blank-reduced.go.txt) | Entire file; parenthesized `_` discarded; `mutation.go-place-events` |
| [parenthesized-places/reduced.go.txt](../gstyle/adapters/goquality/testdata/parenthesized-places/reduced.go.txt) | Entire file; parenthesized LHS pointer rebind+field write; binding collection |
| [promoted-pointer/reduced.go.txt](../gstyle/adapters/goquality/testdata/promoted-pointer/reduced.go.txt) | Entire6 lines; local anonymous embedded shared pointer promotion; unknown storage |
| [sample/edge.go](../gstyle/adapters/goquality/testdata/sample/edge.go) | Entire13 lines; tuple-return alias, temporary `boxResult().Count++`, slice projection copy; call/provenance/events |
| [sample/generated.go](../gstyle/adapters/goquality/testdata/sample/generated.go) | Entire5 lines; generated marker plus global increment; typed emission exclusion vs syntax inclusion |
| [sample/ignored.go](../gstyle/adapters/goquality/testdata/sample/ignored.go) | Entire5 lines; build tag `cyclo_fixture`; typed tag selection |
| [sample/sample.go](../gstyle/adapters/goquality/testdata/sample/sample.go) | Entire75 lines; aliases, reference/value mutation, compound writes, shadow/capture, globals, imported alias, dynamic calls, suppression, initializer literal |
| [sample/sample_test.go](../gstyle/adapters/goquality/testdata/sample/sample_test.go) | Entire9 lines; fixture `TestPure` participates in typed Tests variant; not part of114 audit-test denominator |
| [sample/unsafe.go](../gstyle/adapters/goquality/testdata/sample/unsafe.go) | Entire11 lines; unsafe alias conversion/Add vs Sizeof |
| [suppression-strings/reduced.go.txt](../gstyle/adapters/goquality/testdata/suppression-strings/reduced.go.txt) | Entire3 lines; directive text in ordinary string, not declaration Doc |

### Enumerated-only, unreviewed files (23/40)

These are **unfinished files**, not evidence-backed exclusions. Their paths and content hashes contribute to snapshot enumeration; no semantic conclusions are drawn from their contents.

| Exact file | Why unfinished / next classification |
|---|---|
| [aliasing/README.md](../gstyle/adapters/goquality/testdata/aliasing/README.md) | Historical/support claims not reviewed |
| [aliasing/allocated-wrapper-input.go.txt](../gstyle/adapters/goquality/testdata/aliasing/allocated-wrapper-input.go.txt) | Original reducer input not read |
| [aliasing/indirect-input.go.txt](../gstyle/adapters/goquality/testdata/aliasing/indirect-input.go.txt) | Original reducer input not read |
| [aliasing/range-input.go.txt](../gstyle/adapters/goquality/testdata/aliasing/range-input.go.txt) | Original reducer input not read |
| [args/go.mod](../gstyle/adapters/goquality/testdata/args/go.mod) | Fixture module metadata not read; loader contract unresolved |
| [closure-parameters/README.md](../gstyle/adapters/goquality/testdata/closure-parameters/README.md) | Historical/support claims not reviewed |
| [closure-parameters/check.py](../gstyle/adapters/goquality/testdata/closure-parameters/check.py) | Reduction/oracle supporting algorithm not audited |
| [closure-parameters/input.go.txt](../gstyle/adapters/goquality/testdata/closure-parameters/input.go.txt) | Original reducer input not read |
| [generic-array-copy/README.md](../gstyle/adapters/goquality/testdata/generic-array-copy/README.md) | Historical/support claims not reviewed |
| [generic-array-copy/check.py](../gstyle/adapters/goquality/testdata/generic-array-copy/check.py) | Reduction/oracle supporting algorithm not audited |
| [generic-array-copy/input.go.txt](../gstyle/adapters/goquality/testdata/generic-array-copy/input.go.txt) | Original reducer input not read |
| [parenthesized-places/README.md](../gstyle/adapters/goquality/testdata/parenthesized-places/README.md) | Historical/support claims not reviewed |
| [parenthesized-places/blank-check.py](../gstyle/adapters/goquality/testdata/parenthesized-places/blank-check.py) | Reduction/oracle supporting algorithm not audited |
| [parenthesized-places/blank-input.go.txt](../gstyle/adapters/goquality/testdata/parenthesized-places/blank-input.go.txt) | Original reducer input not read |
| [parenthesized-places/input.go.txt](../gstyle/adapters/goquality/testdata/parenthesized-places/input.go.txt) | Original reducer input not read |
| [promoted-pointer/README.md](../gstyle/adapters/goquality/testdata/promoted-pointer/README.md) | Historical/support claims not reviewed |
| [promoted-pointer/check.py](../gstyle/adapters/goquality/testdata/promoted-pointer/check.py) | Reduction/oracle supporting algorithm not audited |
| [promoted-pointer/input.go.txt](../gstyle/adapters/goquality/testdata/promoted-pointer/input.go.txt) | Original reducer input not read |
| [sample/go.mod](../gstyle/adapters/goquality/testdata/sample/go.mod) | Fixture module metadata not read |
| [sample/report.golden.json](../gstyle/adapters/goquality/testdata/sample/report.golden.json) | Entire golden report contents unreviewed; only test comparison code inspected; no regeneration |
| [suppression-strings/README.md](../gstyle/adapters/goquality/testdata/suppression-strings/README.md) | Historical/support claims not reviewed |
| [suppression-strings/check.py](../gstyle/adapters/goquality/testdata/suppression-strings/check.py) | Reduction/oracle supporting algorithm not audited |
| [suppression-strings/input.go.txt](../gstyle/adapters/goquality/testdata/suppression-strings/input.go.txt) | Original reducer input not read |

## Registry / configuration / reachability reconciliation

| Surface | Enumerated activation and coverage |
|---|---|
| Typed source selection | `Root`, `Tests`, `BuildFlags`; CLI `--tests` false, `--tags`; file vs directory vs no paths; package errors; generated exclusion with helper inclusion. `extraction.go-package-selection` |
| Syntax source selection | Nonempty paths; skip nonroot vendor/testdata/./_ dirs; tests/generated/build-inactive files not excluded. `extraction.go-syntax-selection` |
| Function variants | FuncDecl body guard; declaration initializer first literal subtrees; nested closure evidence; receiver/name normalization; test variants dedup. `extraction.go-function-discovery`, `facts.go-function-identity` |
| Core policy measurements | `fn_length`, `fn_params`, `mutation_per_target`, `mutated_targets`, `side_effect_density`: each implemented/default enabled; Enabled bypass, strict limits, MinStatements, CountSelf, Granularity traced. `quality.go-guardrails`, `quality.go-config`, `effects.go-density` |
| DDD measurements | `aggregate`, `repository`, `mutable_identity`: frontend producer/dependency implementation/evaluator/defaults/suppression traced; path/name/type negative guards recorded. Three distinct source records, not one placeholder |
| Suppression registry |12 strings total;8 policy detectors + `invalid_suppression`; `nilerr`, `forcetypeassert`, `typednil` recognized names only in this evaluator scope. Their external detector implementations/activation are not audited here. `quality.go-suppression` |
| Intrinsic effects |9 recognized non-none kinds; builtin mutations, IO/Panic/Unsafe, global reads/writes, goroutine/channel unknown; direct effect consumers traced. `effects.go-intrinsic`, `effects.go-call-resolution` |
| Prefix policy | Whole stdlib table read, three third-party defaults, appended user overrides, longest/later tie, unknown/none semantics, exported default-only cached API. `effects.go-prefix-classification` |
| Local helper expansion | Static same-package guard, generated/unselected body capture, cycles, missing/dynamic, depth32, effect4096 and cache/truncation. `effects.go-helper-evidence`, `effects.transitive-summary` |
| Planning | Graph/site variants, caller-rules and hops, overlap DSU, ordering cycles, per-fn_params singleton plan, pass-through, one-round bundles. All six `refactor.*` records cover production and tested internal multi-member variant |
| Saved facts | versions1/2 readable,2 exported,1 report; strict document/field shape but incomplete metadata validators; no version migration. `facts.go-saved-facts`, `facts.go-quality-schema` |
| Changed mode | evaluate whole first; only diagnostic subset; unchanged summaries/plans; rebuild groups. `quality.go-changed-filter`; boundary Git adapter read |
| Complexity dependencies | Pinned versions and active implementations inspected; directives/literal/nesting/logical/post-statement variants; adapter has no threshold. `quality.go-cyclomatic`, `quality.go-cognitive` |
| Quality ratchet | Separate supporting command, write/check exclusive, stored tolerance rate compare, current-rule-only loop. `quality.go-excess-ratchet`; no write operation executed |

## Outside-scope boundary reviews and unresolved dependencies

These reads establish callers/producer semantics needed by this slice. They do not claim coverage of whole neighboring modules.

| Boundary file/package | Depth and remaining unreviewed regions |
|---|---|
| [gstyle/main.go L60–150](../gstyle/main.go#L60-L150) | Region read: check dispatch, TUI configuration, wrapper construction Tests=true. Outside this range not reviewed; option parser/body and exit routing beyond boundary remain separate audit work |
| [adapters/gopatterns/ddd.go L1–253](../gstyle/adapters/gopatterns/ddd.go#L1-L253) | Aggregate/repository producers and all called local helpers read. L254 onward **unreviewed/outside slice** (other factory/specification algorithms not part of these quality detectors) |
| [adapters/gopatterns/entity.go L1–23 and L525–620](../gstyle/adapters/gopatterns/entity.go#L551-L589) | ID-name table, mutable identity detector and all its local helpers fully traced. Other entity algorithms outside listed windows unreviewed; extra neighboring lines read do not establish coverage |
| [adapters/gopatterns/ddd_test.go L1–160](../gstyle/adapters/gopatterns/ddd_test.go#L44-L146) | Boundary assertion families fully reviewed: `TestFindAggregateMods`, `TestFindAggregateModsSkipsNonStruct`, `TestIsRepositoryFile`, `TestFindDbCallsHeuristic`, `TestFindDbCallsSkipsRepositoryFiles`; factory test prefix incidental, rest unreviewed |
| [adapters/gopatterns/entity_test.go L56–114](../gstyle/adapters/gopatterns/entity_test.go#L56-L114) | Two mutable-identity test bodies fully read: `TestFindMutableIdentitiesSkipsConstructors`, `TestFindMutableIdentitiesIgnoresNonID`; rest unreviewed |
| [adapters/gopatterns/builder.go L254–294](../gstyle/adapters/gopatterns/builder.go#L254-L294) | Exported ClassifyCallee call consumer read; surrounding PDG/type/argument machinery not inventoried here |
| [domain/patterns/effects_test.go L95–110](../gstyle/domain/patterns/effects_test.go#L101-L110) | `TestQualityClassifyCallee` full assertion read, other effect-compatibility tests/algorithms unreviewed |
| [adapters/gitchanged/gitchanged.go](../gstyle/adapters/gitchanged/gitchanged.go#L1-L270) | Full270 lines read because --changed delegates decisive semantics; not in90-file denominator |
| [adapters/gitchanged/gitchanged_test.go](../gstyle/adapters/gitchanged/gitchanged_test.go#L1-L132) | Full132 lines read;6 boundary tests: `TestChangedRangesWithCustomPrefixes`, `TestParseFileRanges`, `TestParseFileRangesQuotedPath`, `TestParseHunkRange`, `TestTouched`, `TestRootRelative`; not run/count-inflated |
| `github.com/fzipp/gocyclo v0.6.0` | Locally cached `complexity.go` L1–48, `analyze.go` L1–154, `directives.go` L1–39, active Go1.18+ `recv.go` L1–26 fully read via numbered terminal output; `stats.go`, dependency tests, pre1.18 receiver implementation and CLI internals unreviewed. Adapter uses AnalyzeASTFile, not dependency filesystem Analyze path |
| `github.com/uudashr/gocognit v1.2.1` | Cached `gocognit.go` L1–537 and active `recv.go` L1–25 fully read, including public scanning and visitor. Dependency tests, `rangeiter.go`, pre1.18 receiver variant not read. External analysis.Analyzer path is present but not the adapter's activated API |
| `golang.org/x/tools v0.47.0 go/packages` | API call/config read; internal loading/build/test-variant/completeness implementation **unreviewed** despite dependency available through environment; do not invent compiler pseudocode |
| `github.com/BurntSushi/toml v1.6.0` | Config integration call/Undecoded use read; library decoder internals **unreviewed** |
| Go stdlib at Go1.26.2 | AST traversal, parser/scanner/types/path/JSON contracts used; internal implementations not fully inspected. Static compiler API invariants are assumptions, not whole-toolchain audit |
| `gstyle/go.mod` / `go.sum` | go.mod full47 lines read and both files hashed. go.sum contents unreviewed. No install/download attempted |

Cached active complexity sources identified under `/Users/zcstarr/go/pkg/mod`; content SHA-256:

```text
github.com/fzipp/gocyclo@v0.6.0/complexity.go
  85c600d9da11c95b8ae642c3b6b7f04d0a4595c1b6ae61c8541b34242910d323
github.com/fzipp/gocyclo@v0.6.0/analyze.go
  f39d6bac440d47128c57499bca64567870187acabbd597b5199830e6d73b44bf
github.com/fzipp/gocyclo@v0.6.0/directives.go
  ce5905daee14ab87172bf85fbd0b4250a943011ef82807f78e339995bd84f2f0
github.com/uudashr/gocognit@v1.2.1/gocognit.go
  15d6e0951f56b9b7f3702339701e5727c4d8caae5cd76d77518df968ed1e9500
```

## Explicit scope exclusions / no overclaim

- Rust source, CCGraph PDF and `ccgraph-divergences.md` claims reconciliation are **unreviewed/outside this Go-quality delegation**. Each algorithm record explicitly marks Rust/reference pseudocode unresolved rather than absent/equivalent. Coordinator must supply parity/reference axes later.
- Other Go pattern/mining/clone/refactoring implementations, TUI presentation/control/cache, annotations, baseline artifacts and Makefile/CI wiring are outside scope. Boundary consumer/caller reads above do not audit these systems.
- CLI text/JSON layout is secondary: scoped rendering code was read, but no standalone rendering algorithm record; semantic selection/export/filter/error order is inventoried.
- No code rewriting exists in these advisory plan records. Safety/behavior preservation must not be inferred from “bundle”, “pass-through”, “independent” or “callee-first”.
- No benchmark/historical reducer result reverified. Golden-test existence is not golden-file inspection or a passing test.

## Commands actually run / validation boundary

Read-only observations:

- `git --no-optional-locks status --short` and `git --no-pager rev-parse HEAD` in both compat and gstyle.
- `find` / `wc -l` / `grep -n '^func Test'` plus read-only Python enumerators for files, fixture texts and symbol/file counts.
- `go version`, `go env GOMODCACHE GOPATH` (no package build/load command).
- `git --no-pager ls-tree HEAD` for the five directory tree IDs.
- `shasum -a 256` input/dependency files and read-only Python scope-manifest hash.
- Numbered terminal reads of locally cached complexity implementation files; no dependency download/install.
- Documentation ID check: **35 records, no duplicate IDs**. Final link/count/snapshot checks are documentation validation, not algorithm test execution.

**Not run:** `go test`, `go list std`, analyzer/check/qualitygate commands, golden updates, baseline writers, Python reducer/oracle scripts, expensive corpus tests. Some inspected tests themselves create temporary Git commits; none was executed. Source-only audit intentionally avoids presenting test assertions as observed results.

## Key gaps and prioritized handoff

### Finish phase-one evidence first (no implementation implied)

1. Read the23 enumerated-only fixture/support files, especially golden JSON and oracle scripts; separate current assertions from README historical claims. Inspect loader/compiler/type-printer boundaries or mark them explicitly unresolved in the coordinator inventory.
2. Reconcile this slice's35 IDs with sibling Rust/core inventories; do not concatenate into “equivalent”. The stable prefixes are `extraction.*`, `facts.*`, `quality.*`, `mutation.*`, `effects.*`, `refactor.*`.
3. Check wider entrypoints/consumers only where needed: suppression-only nilerr/forcetypeassert/typednil, baseline CI activation, PDG exported classifier versus configurable evaluation. Maintain disjoint ownership.

### Highest-value distinguishing fixtures (designed, not implemented/run)

| Priority / IDs | Gap / concrete discriminator |
|---|---|
| P1 `facts.go-quality-schema`, `refactor.go-call-graph` | Saved facts with negative Param index, unknown Arg kind, mismatched ParamList/Params and invalid Uses; validator currently omits all these checks |
| P1 `quality.go-excess-ratchet` | Last finding disappears: baseline rule omitted from current map, no improvement check; compare with present diagnostic of zero excess |
| P1 `quality.go-suppression` | Identical `//lint:ignore fn_params Reason` in Go Doc vs saved PrecedingLine; source omission vs parser activation. Lowercase reason token ambiguity separately |
| P1 `effects.transitive-summary` | Shared helper visited first at depth cap then shallow, reverse source call order; cache context-sensitive cutoff/recursion tests, not just output sort |
| P1 `mutation.go-binding-provenance`, `effects.transitive-summary` | `alias := append(shared,x)` indexed write vs reassignment through shared binding; mutating helper receiving new owned object vs inline mutation |
| P2 `facts.go-parameter-arguments` | `*ptr` uses StarExpr and is not peeled; qualified const vs bare named const; type package.Name collision; variadic Args metadata |
| P2 `facts.go-function-identity`, `refactor.go-call-graph`, `facts.go-report-join`, `quality.go-changed-filter` | Multiple init/name collisions, position-only attachment and path+name touched filtering; helper-only graph availability after file selection |
| P2 `refactor.closed-parameter-bundles` |3-input intersection ab absent from one-round candidates; equal comparator ties differing Params; support1/repeated caller parameter admission |
| P2 `quality.go-config`, three `quality.go-ddd-*` | Negative DDD maxima accepted; parenthesized targets, short type-name collisions, fake db receivers/aliases, constructor name exemption and ID++ omission |
| P2 `quality.go-cognitive` | Logical expression in for Post omitted; parenthesized logical-chain scoring; gocognit-ignore creates missing stat→zero while cyclo-ignore omits function |
| P2 `extraction.go-physical-mapping`, `quality.go-changed-filter` | Deletion anchor3 vs4, branch tip vs merge-base, literal pathspec vs wildcard, untracked handling |
| P2 `effects.go-prefix-classification` | Package “covered” with unlisted API still unknown; default-only exported classifier vs TOML Evaluate override; dynamic prefix precedence; normalizer non-idempotent colon chain |

## Completion statement

**Partial**: 35 substantive records, **25/25 production files**, **25/25 test files /114 tests inspected**, **17/40 fixture/support files reviewed**, **23 explicit unreviewed files**, plus bounded neighboring-source and locally cached dependency reads. No production file in the requested directories is unmapped; that does **not** establish all behavior, complete fixture coverage, Rust parity, CCGraph fidelity or refactoring safety. No implementation/baseline/golden/dependency/branch/commit changes were made.
