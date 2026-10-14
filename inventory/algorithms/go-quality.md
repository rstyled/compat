# Go quality/extraction algorithm inventory — phase-one source checkpoint

**Status: partial**, not a parity proof or a completed workspace-wide audit. Source snapshot: clean embedded `gstyle` HEAD **598c7b03366caa0fef70f66aa58e76222eefb8fa**. Scope and per-file/test/fixture depth: [coverage ledger](../go-quality-coverage.md). Only this file and that ledger are owned by this audit.

## Record conventions and evidence boundary

Every record below inherits these fields unless overridden:

- **Implementation / evidence:** Go implementation source reviewed at the snapshot above; pseudocode is source-derived, not executed. Tests are **inspected assertions, not observed passing results**. Examples and distinguishing fixtures are **unexecuted designs/inferences**.
- **Rust pseudocode / divergence:** unresolved, outside this Go-only slice. Do not infer Rust absence or equivalence. Differences stated below compare actual Go paths/variants or intended/commented behavior, not uninspected Rust.
- **Reference pseudocode:** not established here; CCGraph paper/reflection reconciliation is outside this quality slice. No CCGraph fidelity claim is made.
- **Status:** implemented; production reachability is separately stated. “Complete” in an output is the algorithm's flag, not proof of semantic purity. “Plan” is advisory data, not a verified safe source rewrite.
- **Units / cost:** Go `int` for counts/indices/positions, `int64` for policy/density arithmetic, `float64` for complexity means and ratchet rates. No randomness/seeds. Cost bounds exclude compiler, filesystem, and Git unless stated. N = emitted functions, A = AST nodes, B = bytes, C = calls, H = reachable helpers, E = effect events, M = mutations, P = parameters, S = resolved call sites, K = candidate itemsets.
- Links are relative to this report; `#Lx-Ly` is tied to this HEAD. Locally cached dependencies are linked to version-tagged upstream source and separately content-hashed in the ledger; those links are locators, not evidence of a network fetch.

## Pipeline / activation

```text
main.runSubcommand("check") → qualitycheck.Run
  parse/validate options → LoadConfig → inputFacts
    typed source: Analyzer.Extract → packages.Load → extractFile/function
      bindings + mutation/calls/intrinsics + DDD → reachable helper bodies → uniqueFacts
    saved input: readFacts (schema 1 or 2, same Go structs)
  format=facts: export schema 2; no Evaluate or changed filtering
  otherwise: Evaluate → canonical/validate → effects/density + rule checks
    → per-fn_params plan → summary + fix groups
    → optional changed diagnostic filtering + rebuild fix groups → output → ErrFindings
main.runTUI → ReportAnalyzer(Tests=true)
  syntax-only complexity scan → typed extraction/Evaluate
    typed failure becomes report.Quality.status=error, not returned Analyze error
    typed success joined to syntax functions by physical position
qualitygate.main (separate command)
  read evaluated report → aggregate excess → compare stored rates → exit
```

Call-site evidence: [main.runSubcommand L80–92](../../gstyle/main.go#L80-L92), [main.runTUI L116–146](../../gstyle/main.go#L116-L146), [qualitycheck.execute/checkFacts L61–96](../../gstyle/application/qualitycheck/cli.go#L61-L96), [ReportAnalyzer.Analyze L24–55](../../gstyle/adapters/goquality/report.go#L24-L55). Broader TUI/fixer/mining consumers are not audited beyond these boundaries.

## Extraction, identity and schemas

### extraction.go-package-selection — typed package selection

**Purpose / output:** type-checked package facts for selected physical files, respecting Go build configuration; errors abort the headless scan.

**Locations / helpers:** [Analyzer.Extract, loadPatterns, selection.addInput/includes, relativePath, packageErrors, extractPackage L27–192](../../gstyle/adapters/goquality/analyzer.go#L27-L192). **Callers / activation:** `qualitycheck.inputFacts`, `ReportAnalyzer.qualityReport`; default check (`Tests=false`), TUI (`Tests=true`), library overrides `Root`, `Tests`, `BuildFlags`; tags become `-tags=...`.

**Inputs / parameters:** root defaults to cwd, otherwise absolute path; empty paths become `.`. Explicit inputs must exist, be directories or regular `.go` files. Package-pattern syntax containing `...` is rejected, even within an otherwise plausible filename. **Outputs:** sorted/deduplicated facts via `facts.go-function-identity`; package errors sorted/compacted after root prefix removal. **Dependencies:** `golang.org/x/tools/go/packages v0.47.0`, active compiler/environment; loader internals unresolved.

```text
root := cwd if Root="" else Abs(Root); propagate error
for input in (paths or ["."]):
  reject if input contains "..."
  absolute := Clean(input if absolute else Join(root,input))
  require Rel(root,absolute) not ".." and not starting "../"
  Stat; directory → remember directory; load pattern Join(absolute,"...")
  else require regular && extension=".go"; remember file; pattern="file="+absolute
sort+compact patterns
Load(Context,Dir=root,Mode=LoadSyntax|NeedForTest,Tests,BuildFlags)
fail on Load error; collect returned pkgs.Errors (not a recursive dependency-error walk)
fail if any errors, or no packages
for each returned package, each Syntax file:
  filename := Fset.PositionFor(file.Pos,false).Filename
  relativePath failure → skip file
  extract all its functions into available, even unselected/generated files
  append to emitted only if selection.includes(filename) && !ast.IsGenerated(file)
attachHelpers(emitted,available); combine packages; uniqueFacts
```

**Invariants / limitations:** root containment is lexical `filepath.Rel`, not symlink canonicalization. Selection is exact file equality or directory-plus-separator prefix. Compiler excludes build-tag/OS-inactive source, but generated bodies can survive as helper evidence. No directory skip list is implemented here: loader decides traversal. No independent dependency package expansion. **Cost:** selection O(inputs × selected directories/files), plus loader unknown and extraction of all available package syntax.

**Tests:** [TestSelectionTagsAndIncompletePackages L137–154](../../gstyle/adapters/goquality/analyzer_test.go#L137-L154), [TestFixtureGoldenAndDoubleRun L99–135](../../gstyle/adapters/goquality/analyzer_test.go#L99-L135), [TestHelperFactsSurviveFileSelectionAndPolicyReevaluation L94–134](../../gstyle/adapters/goquality/local_helpers_test.go#L94-L134). **Examples / distinguishing fixture:** selected `caller.go` calling generated `helper.go` yields only caller as a function but retains helper IO; type-error package aborts; tag-selected `ignored.go` yields `Tagged`. First divergence from syntax scan is file selection (see `extraction.go-syntax-selection`). **Unknown:** loader internals and symlink/build-variant edge behavior not executed.

### extraction.go-function-discovery — declaration and initializer discovery

**Locations / symbols:** [extractDeclarations/extractInitializers L202–233](../../gstyle/adapters/goquality/analyzer.go#L202-L233), [extractFunction/resolvedName L29–49, L287–303](../../gstyle/adapters/goquality/function.go#L29-L49). **Callers / activation:** `extractFile` on all loaded package syntax; always in typed extraction. **Inputs:** AST/type info, physical source bytes. **Outputs:** one fact per body-bearing `FuncDecl` and first encountered literal subtree within each non-function declaration; nested closures are folded into that fact, not independently emitted.

```text
for decl in file.Decls in source order:
  if FuncDecl: skip nil Body; emit extractFunction
  else ast.Inspect(decl):
    on FuncLit:
      physical position := literal.Pos
      name := pkg.PkgPath+".<literal@line:column>"
      synthetic FuncDecl(Name=new identifier(name),Type=literal.Type,Body=literal.Body)
      emit extractFunction; do not descend into this literal
extractFunction:
  start/end := physical positions(fn.Pos/fn.End)
  name := fn.Name.Name; if TypesInfo.Defs[Name] is *types.Func → resolvedName
  resolvedName: receiver Unalias; strip one pointer + Unalias;
    if named, prepend receiver type object's Name + "."; prepend package Path if nonnil
  Source := source[start.Offset:end.Offset]; PrecedingLine := selected fn.Doc directive
  Params := parameterCount; HasSelf := Recv!=nil
  build parameter metadata; add outer/receiver parameters; collectBindings(body)
  inspect body without pruning nested closures; append DDD detector hits
```

**Parameters / dependencies:** no count cap at extraction; validation follows during evaluation, not facts export. `resolvedName` erases receiver generic instantiations and pointer spelling. **Limitations:** nil-body declarations differ from syntax complexity discovery; package literals embedded in nonliteral expressions are discoverable here but not necessarily in gocyclo. Multiple `init` declarations have distinct physical identities but the same name, affecting downstream name maps. **Cost:** O(A+B), excluding repeated provenance/DDD passes.

**Tests / fixtures:** [sample.go L23–46, L75](../../gstyle/adapters/goquality/testdata/sample/sample.go#L23-L46), [closure_parameter_test.go L11–61](../../gstyle/adapters/goquality/closure_parameter_test.go#L11-L61); typed fixture tests assert closure writes stay with the outer function. **Distinguishing design:** `var h = wrap(func(){...})` is discovered here, versus direct ValueSpec literals only in syntax complexity; `func f(){ closure:=func(){...} }` emits only f but includes closure events. **Unknown:** uncommon initializer/declaration/type-error recovery shapes; no executed completeness claim.

### facts.go-function-identity — physical identity and duplicate policy

**Locations / symbols:** [uniqueFacts/compareFacts L61–69, L235–249](../../gstyle/adapters/goquality/analyzer.go#L61-L69), [canonicalFacts/compareLocation/compareFunction L47–79](../../gstyle/domain/quality/evaluate.go#L47-L79). **Callers:** extraction after package combination; `Evaluate`, public `BuildFixGroups`. **Inputs:** function slices; identity tuple `(Path,Line,Column,Name)`. **Outputs:** sorted physical functions; equal tuple with unequal entire struct is an error. **Parameters:** stable sort in evaluator; extraction uses nonstable sort. No hash/stable semantic ID.

```text
extract: sort input in place by path, line, column, name
  for adjacent equal identity: if !reflect.DeepEqual → conflicting Go build variants error
  compact equal identity, retaining one
evaluate: shallow-clone slice; stable-sort same tuple
  validate each fact; append new identity
  equal identity: DeepEqual required else conflicting facts error; drop exact duplicate
```

**Dependencies / invariant:** Go reflect equality distinguishes nil from empty slices and compares Source, Helpers, Args, ParamList, DDD, etc.; it is not semantic merging. Nested evidence order is not canonicalized before duplicate equality. Evaluation does not mutate the input top-level slice; extraction does sort its locally constructed slice. **Cost:** O(N log N + total duplicate evidence compared), O(N) evaluator top-level clone.

**Tests:** [TestDeterminismDeduplicationAndInputImmutability L255–285](../../gstyle/domain/quality/evaluate_test.go#L255-L285), [TestBuildFixGroupsRejectsConflictingFacts L197–204](../../gstyle/domain/quality/groups_test.go#L197-L204), test-variant assertions in golden test. **Examples / distinguishing design:** same physical tuple with `Params+1` fails; exact test variant duplicate collapses; semantically equal nil/empty evidence can conflict (inference). Moving a function changes this identity. **Gap:** consumers use weaker keys (name or position without name); see report join/call graph/changed filter.

### facts.go-quality-schema — validation and significant field lifecycle

**Locations:** [Function/Helper/Mutation/Call/ArgSource/ParamFacts/DDDViolation L4–103](../../gstyle/domain/quality/facts.go#L4-L103), [Effect/report/plan types L104–241](../../gstyle/domain/quality/facts.go#L104-L241), [validateFact and validators L10–72](../../gstyle/domain/quality/validate.go#L10-L72), [validateHelpers L5–31](../../gstyle/domain/quality/helper_validate.go#L5-L31). **Callers / activation:** `canonicalFacts`; public `Evaluate` and `BuildFixGroups` validate facts. Raw export does not.

**Inputs / outputs:** policy-free function data; invalid facts reject whole report. Absent scalar fields decode as zero/false/empty; absent arrays decode nil. Producer→consumer: source/positions→identity, changed ranges and report join; Params/HasSelf→budget; Statements/CodeLines→density/length; mutations→target budgets and effects; calls/helpers→summaries and graph; ParamList/Args→planning only; DDD→three rule measurements; PrecedingLine→suppression. Report schema is version 1 while raw FactsFile exports version 2.

```text
in order: validateLocation, validateCounts, validateMutations, validateEffects,
          validateCalls, validateHelpers; return first error
path: nonempty, no backslash, not absolute, path.Clean(value)==value,
      not ".." and not prefix "../"
location: Line>=1 && Column>=1 && Name!=""
counts Params,Statements,CodeLines,len(Mutations),len(Calls),len(Effects): 0..1_000_000 inclusive
mutation: Root!="", Line>=1, Provenance in {local,external,unknown}
effect: recognized kind excluding none, Line>=1
call: Callee!="", Line>=1
helpers: len<=1_000_000; normalized name nonempty and unique, including not root's name
  validate body counts/mutations/effects/calls using enclosing Location
```

**Parameters / limitations:** no validation of RootID, FieldPath, effect Detail/Via, parameter-list length/name/type/Uses, Args kind/index, DDD kind/line/detail, source length/span or metadata consistency. Helper evidence positions need not lie inside caller's source. **Cost:** linear field/event count plus normalization bytes and hash-map space for helper names.

**Tests:** [TestInvalidBoundaries L295–318](../../gstyle/domain/quality/evaluate_test.go#L295-L318), [TestHelperFactsRejectInvalidAndConflictingBodies L79–94](../../gstyle/domain/quality/local_calls_test.go#L79-L94). **Distinguishing design:** saved fact with valid base fields and `ArgSource{Kind:"param",Param:-1}` passes these validators; downstream forwarding's upper-only guard admits it. DDD unknown IDs pass validation but are not measured. **Unknown:** no executed malformed-planning-fact test; schema acceptance is weaker than compiler-produced invariants.

### quality.go-config — defaults, overrides and validation

**Locations:** [DefaultConfig/Validate/weights/prefix defaults L59–186](../../gstyle/domain/quality/config.go#L59-L186), [LoadConfig/decodeConfig L12–46](../../gstyle/application/qualitycheck/config.go#L12-L46). **Callers:** check execution, TUI config loading, `Evaluate`; public `BuildFixGroups` does **not** call config validation. **Inputs:** default struct plus optional TOML; **outputs:** config or first error. **Dependency:** BurntSushi/toml v1.6.0; decoder internals not inspected.

```text
defaults enabled/max:
 fn_length=200; fn_params=4; mutation_per_target=3; mutated_targets=3;
 side_effect_density=500; aggregate=1; repository=0; mutable_identity=0
MinStatements=3; CountSelf=false; Granularity="root"
weights mutation/io/network/global/unsafe/time/random/panic/unknown = 1/3/3/2/4/1/1/0/1
Grouping.CallerRules=["fn_params"]; CallerHops=1
Prefixes := stdlibPrefixes then three third-party prefixes
LoadConfig("") → defaults directly
else save default prefixes; clear Prefixes; TOML-decode into otherwise default config
  error on undecoded/unknown TOML keys; append user prefixes after defaults; Validate
Validate: granularity root|field; MinStatements in 0..1_000_000
  first five metric Rule.Max in 0..1_000_000_000 (enabled or not)
  all nine weights in 0..1_000_000
  prefixes path nonempty, kind valid including none
  caller rules contained in suppression ruleIDs; CallerHops in 0..1_000_000
```

**Limitations / divergence:** Aggregate/Repository/MutableIdentity limits are omitted from `validateLimits`, so negative/huge DDD maxima are accepted; zero min statements is valid. User prefixes append, enabling equal-length last-wins overrides. Grouping can name suppression-only rule IDs. **Cost:** O(prefixes+caller rules); TOML parsing unresolved.

**Tests:** [TestConfigDefaultsOverridesAndValidation L55–69](../../gstyle/application/qualitycheck/cli_test.go#L55-L69), [TestGroupingConfigTOML L214–234](../../gstyle/application/qualitycheck/cli_test.go#L214-L234), [TestGroupingConfigValidation L206–222](../../gstyle/domain/quality/groups_test.go#L206-L222). **Boundary design:** set `aggregate.max=-1` with no DDD evidence: actual 0 exceeds -1; unlike `fn_params.max=-1`, config is not rejected. Not executed.

### facts.go-saved-facts — versioned export/re-evaluation

**Locations / symbols:** [FactsFile, execute, options.validate, inputFacts/readFacts L44–47, L61–74, L138–183](../../gstyle/application/qualitycheck/cli.go#L138-L183), [supportedFactsVersion L275](../../gstyle/application/qualitycheck/cli.go#L275). **Callers:** `Run`; opt-in `--format facts` and `--facts-in`. **Inputs:** source options or exactly one JSON document; **outputs:** raw facts schema 2 or evaluation report schema 1. **Parameters:** accepted input versions 1 and 2; no version-specific migration/defaulting.

```text
load+validate config first, even for facts export
facts-in != "" → reject if paths supplied || Tests || tags!="" || format="facts"
  JSON Decode with DisallowUnknownFields
  require schema_version in {1,2}, Functions != nil (empty [] accepted)
  second Decode must return io.EOF; otherwise fail
otherwise Analyzer(Tests, tags BuildFlags).Extract
format="facts" → encode FactsFile{2,facts}; do not Evaluate, suppress or --changed filter
other formats → Evaluate; optional changed filtering; write report;
  output error precedes ErrFindings; any diagnostic → ErrFindings
```

**Dependencies / limitations:** schema 1 is read into current structs, not explicitly deprived of helper evidence; old input lacking Helpers yields unknown local calls, not pure calls. Args/ParamList omissions remove planning evidence without changing Params budgets. A report JSON is not a FactsFile input. JSON decoder dependency is stdlib; no raw fact validation before export. **Cost:** O(JSON bytes + subsequent algorithms).

**Tests:** [TestSavedFactsCanBeReevaluatedWithoutCompiler L36–53](../../gstyle/application/qualitycheck/cli_test.go#L36-L53), [TestCLIHelpAndInvalidInput L71–86](../../gstyle/application/qualitycheck/cli_test.go#L71-L86), [TestFactsVersionsKeepHelperEvidenceAndLegacyUncertainty L111–142](../../gstyle/application/qualitycheck/cli_test.go#L111-L142), [TestFactsExportIncludesSelectedFunctionHelperBodies L144–179](../../gstyle/application/qualitycheck/cli_test.go#L144-L179). **Distinguishing design:** same local call without/with empty known helper → incomplete unknown / complete zero effects, independent of version number. Empty functions `[]` valid; `null` invalid. **Evidence:** tests inspected only.

### facts.go-report-join — syntax/typed report attachment

**Locations / symbols:** [ReportAnalyzer, qualityReport, attachQuality, qualityByPosition L15–89](../../gstyle/adapters/goquality/report.go#L15-L89). **Activation / callers:** default TUI constructs wrapper with Tests=true; library consumers can vary it. **Inputs:** syntax `domain.Report`, typed facts, config; **outputs:** global `QualityAnalysis` and per-syntax-function `FunctionQuality`.

```text
Complexity.Analyze(paths); returned error → propagate
make input paths absolute; typed Analyzer.Root := syntax report.Root
Extract(context.Background(),inputs); Evaluate
typed/extraction/config failure → report.Quality={status:"error",Error}; return report,nil
success → status="ready", Report=&result
for each result.Functions[index]:
  map[(relativePath,line,column)] := FunctionQuality(result,empty diagnostics,
                                                    MutationEvents=facts[index].Mutations)
append diagnostics into that map by same position (no nil guard)
for each syntax file/function: derive relative path; attach map[position] (possibly nil)
```

**Limitations / dependencies:** join ignores Name; relies on extractor order aligning with evaluator canonical order when indexing facts. The wrapper's Extract/uniqueFacts supplies this alignment for normal inputs; helper API itself does not enforce it. Whole typed report can contain functions with no syntax counterpart; syntax report can contain excluded/generated/tag-inactive functions with nil typed quality. Uses background context rather than incoming cancellation. **Cost:** O(N+diagnostics+syntax functions), map space O(N).

**Tests:** [TestReportJoinsTypedEvidenceToComplexityFunctions L13–40](../../gstyle/adapters/goquality/report_test.go#L13-L40), [TestTypeErrorsKeepComplexityReportAvailable L42–60](../../gstyle/adapters/goquality/report_test.go#L42-L60), aliasing/promoted-pointer wrapper tests. **Distinguishing design:** unresolved identifier in otherwise parseable function → headless error, but TUI complexity report retained with quality error. No evidence that nil quality means clean. **Unknown:** downstream UI interpretation not audited.

## Counting and syntax-only complexity

### quality.go-counts — code lines, statements and parameters

**Locations:** [parameterCount/buildParams/countParamUse L85–178](../../gstyle/adapters/goquality/function.go#L85-L178), [visit/countedStatement L188–231](../../gstyle/adapters/goquality/function.go#L188-L231), [codeLines/markLiteralLines L318–346](../../gstyle/adapters/goquality/function.go#L318-L346), [parameterBudget L161–166](../../gstyle/domain/quality/evaluate.go#L161-L166). **Callers / activation:** all typed function extraction; evaluation always measures, enabled guards govern findings. **Inputs:** function source slice and typed AST. **Outputs:** integer CodeLines/Statements/Params, HasSelf and ParamList.

```text
Params := sum(max(number of names,1) for each parameter field); receiver excluded
ParamList := source-order entries for named params; one unnamed entry per unnamed field
  Type := TypeOf(field.Type); nil→""; TypeString using package.Name (not package.Path)
  map each nonnil Defs parameter object to its list index
during ast.Inspect body, count every ast.Stmt except Block,Empty,CaseClause,CommClause,Labeled
  visit nested closures too; count parameter Uses for Ident in TypesInfo.Uses and paramIndex
CodeLines := number of distinct source lines with scanner tokens:
  scanner mode 0 (comments not emitted); skip EOF and auto-inserted semicolon literal "\n"
  mark each token's start line; for string token mark all embedded newline continuation lines
fn_params Actual := Params + (1 if CountSelf && HasSelf else 0)
```

**Limits / invariants:** physical byte-column positions, lexical tokens not raw nonblank lines. Explicit semicolon tokens count; braces/signature lines count; comments alone do not. Header statements (`if` init, loop post, declarations) and statements inside nested closures contribute; source length starts at fn.Pos, excludes declaration docs. `Uses` is syntactic, includes assignment LHS references, not liveness/role analysis. **Cost:** O(A+B+P), line-set space O(source lines).

**Tests / examples:** [TestCodeLinesIgnoreCommentsAndPreserveStrings L156–161](../../gstyle/adapters/goquality/analyzer_test.go#L156-L161) asserts 5 lines for mixed comments/raw multiline string; [TestParamListNamesTypesAndUses L81–100](../../gstyle/adapters/goquality/args_test.go#L81-L100) asserts Uses 4/6/1; strict-budget test covers receiver opt-in. **Distinguishing design:** uncalled closure with three statements increases outer Statements; multiline raw string counts continuation lines whereas multiline block comment does not. **Unknown:** Go scanner/type-printer internal behavior delegated to stdlib.

### extraction.go-syntax-selection — raw filesystem complexity selection

**Locations / symbols:** [Analyzer.Analyze/sourceFiles/collectSourcePath/collectGoFile/skipDirectory/commonRoot L25–38, L105–176, L378–414](../../gstyle/adapters/gocyclo/analyzer.go#L105-L176). **Callers:** wrapper's Complexity analyzer and direct library clients; default syntax/TUI scan, not headless quality check. **Inputs:** nonempty paths; **outputs:** sorted unique absolute `.go` filenames, common containing directory, syntax report. **Parameters:** no tests/build-tags/generated exclusions.

```text
require len(paths)>0
for path: Abs + Stat
  nondirectory: require extension .go; add (no regular-file guard)
  directory: WalkDir; add nondirectory entries with .go extension
    skip nonroot dirs named vendor/testdata or prefixed . or _
sort map filenames
commonRoot: directory(first root); climb parent until every next directory is inside via Rel
attempt newGitDiff(root), ignore failure boolean
parse/analyze every file; any parse/read error aborts; attach diff if available; summarize
```

**Divergence / limitations:** build tags, generated code and `_test.go` are all syntax-scanned, unlike typed selection. Explicitly naming a skipped directory scans it as root. No type checking or active package grouping; parser handles files individually. **Cost:** O(filesystem entries + F log F + analysis); filesystem errors stop the scan.

**Tests:** [TestAnalyzerCapturesFunctionSource L11–49](../../gstyle/adapters/gocyclo/analyzer_extra_test.go#L11-L49) and syntax reproducer families; selection skip branches have no direct scoped test assertion identified. **Distinguishing design:** directory contains malformed build-inactive `.go`; syntax analyzer fails parse while typed load can ignore it. **Unknown:** symlink traversal details delegated to WalkDir/Stat; no executions.

### extraction.go-physical-mapping — syntax literals, source spans and diff annotations

**Locations:** [physicalFileSet L7–12](../../gstyle/adapters/gocyclo/position.go#L7-L12), [normalizeFunctionInitializers/normalizeValueSpec/nameFunctionLiterals L12–41](../../gstyle/adapters/gocyclo/literal.go#L12-L41), [analyzeFile/functionRanges/sourceText L178–217, L299–312, L370–376](../../gstyle/adapters/gocyclo/analyzer.go#L178-L217), [newGitDiff/parseDiff/hunkLines/functionDiff L20–144](../../gstyle/adapters/gocyclo/diff.go#L20-L144). **Callers / activation:** every syntax scan; optional Git availability annotates without filtering functions. **Inputs:** parsed source and working-tree Git diff. **Outputs:** physical spans, initializer variable names, DiffLines.

```text
parse with comments; make fresh FileSet with same file base/size/physical Lines, no //line remaps
preorder AST: for each ValueSpec Values[i], if Unparen(value) is FuncLit and i<Names count:
  replace value with literal (AST-only mutation); names[literal physical offset]=Names[i]
external cyclo returns stats → overwrite FuncName by offset when names known
ranges := offset→(End.Offset,End.Line,node) for every FuncDecl/FuncLit
Source := bytes[start:end], or "" if start<0 || end<=start || end>length
Git: find toplevel; first verifiable main/master/origin/main/origin/master/HEAD is base
  no merge-base calculation; all Git errors → no diff evidence
  diff --literal-pathspecs --no-color --no-ext-diff --no-textconv --unified=0 BASE -- relativefile
parse hunk: old start,new start; omitted new count=1; zero new count→new start+1
  '-' emit at current old/new anchor then old++; '+' emit then new++; ' ' increments both
  ignore other lines; hunk state persists until new header
per function include additions if start<=NewLine<=EndLine;
  deletions if start<=NewLine<=EndLine+1
```

**Dependencies / limits:** AST normalization does not rewrite disk. Names collected for local ValueSpecs too, but external cyclo only emits eligible top-level declarations/direct literal initializers. No untracked-file special handling in this Git path. Raw changed-filter path uses different bases and deletion anchors (`quality.go-changed-filter`). **Cost:** O(A+B+diff lines × function count); names/ranges O(number of function nodes).

**Tests:** [TestLineDirectiveUsesPhysicalSourceLocations L18–30](../../gstyle/adapters/gocyclo/source_repro_test.go#L18-L30), [TestFunctionVariableNames L11–30](../../gstyle/adapters/gocyclo/literal_test.go#L11-L30), [TestParenthesizedLiteralNamesAndIgnore L48–53](../../gstyle/adapters/gocyclo/source_repro_test.go#L48-L53), [diff boundary tests L10–42](../../gstyle/adapters/gocyclo/diff_boundary_test.go#L10-L42), [literal pathspec test L8–33](../../gstyle/adapters/gocyclo/pathspec_test.go#L8-L33), [textconv test L9–36](../../gstyle/adapters/gocyclo/textconv_test.go#L9-L36). **Distinguishing design:** `@@ -4 +3,0 @@` yields syntax anchor 4 versus changed-filter anchor 3. Physical `//line` positions stay disk-relative for complexity.

### quality.go-cyclomatic — dependency score and local diagnostic mirror

**Locations:** [analyzeFile/cyclomaticDiagnostics/increments L190–211, L314–368](../../gstyle/adapters/gocyclo/analyzer.go#L314-L368); locally inspected dependency [gocyclo v0.6.0 Complexity L16–48](https://github.com/fzipp/gocyclo/blob/v0.6.0/complexity.go#L16-L48), [AnalyzeASTFile/analyzeDecl/directives L89–154](https://github.com/fzipp/gocyclo/blob/v0.6.0/analyze.go#L89-L154), [directive parser L27–38](https://github.com/fzipp/gocyclo/blob/v0.6.0/directives.go#L27-L38). **Activation:** syntax scan; score has no ceiling in this adapter. **Inputs:** AST after initializer normalization; **outputs:** `int Complexity` and diagnostic event list.

```text
dependency emits each top-level FuncDecl (even nil Body) and each direct FuncLit ValueSpec value
  skip when attached FuncDecl/GenDecl Doc contains comment with prefix //gocyclo:
    whose trimmed remainder == "ignore"
  function name := Name, or "(receiver).Name"; receiver printer strips generic indices,
    preserves *; unsupported receiver AST → BADRECV
Complexity(node): score=1; walk entire node including nested closures
  +1 each IfStmt,ForStmt,RangeStmt
  +1 each CaseClause with nonnil List; each CommClause with nonnil Comm
  +1 each BinaryExpr Op in {&&,||}
local diagnostics: initial "function" event at node.Pos;
  same walk/increments, at control-node Pos or logical OpPos; default cases ignored
sort functions: Complexity descending, Line ascending, Name ascending (stable sort)
fold integer totals and max peaks; means float64(total)/count; empty→0
```

**Invariants / limitations:** score is syntactic decision count, not CFG cycle rank computed from a graph; nested bodies contribute even when uncalled. gocyclo ignores cause function to vanish from syntax list, not just score=0; typed quality discovery does not honor this directive. **Cost:** O(A), plus O(N log N) sorting; unguarded Go int totals.

**Tests:** source capture asserts diagnostic count equals Complexity; [TestAnalyzerScoresFunctionLiteralReproducer L109–137](../../gstyle/adapters/gocyclo/analyzer_extra_test.go#L109-L137) asserts 2/1 for literal with if. **Examples / distinguishing design:** empty body→cyclo 1, cognitive 0; default-only switch does not add cyclo; `//gocyclo:ignore` declaration still can appear in full typed quality report. **Unknown:** dependency test suite not reviewed/run; inspected only active API implementation.

### quality.go-cognitive — dependency visitor, nesting and initializer adaptation

**Locations:** [cognitiveStatsByOffset/cognitiveLiteralStat/cognitiveDiagnostics L244–291](../../gstyle/adapters/gocyclo/analyzer.go#L244-L291); inspected [gocognit v1.2.1 L80–177, L191–489](https://github.com/uudashr/gocognit/blob/v1.2.1/gocognit.go#L191-L489). **Callers / activation:** syntax analyzeFile; no threshold in adapter. **Inputs:** AST/comments plus synthetic declaration for initializer literals. **Outputs:** `int` cognitive score and incremental nesting diagnostics; absent offset match defaults to zero stat.

```text
scan top-level FuncDecl; exact comment "//gocognit:ignore" skips that declaration stat
visit file separately: do not descend into FuncDecl;
  on first non-declaration FuncLit synthesize FuncDecl(Name="_",Type,Body), scan from nesting=0;
  map score by literal offset; do not descend (its nested literals already count)
visitor init score=0,nesting=0, elseNodes/calculatedExprs empty
ADD(text,pos): score+=1; diagnostic Inc=1 (Nesting=0)
NESTADD(text,pos): score+=nesting+1; diagnostic Inc=nesting+1,Nesting=nesting
if: ADD if marked else-if else NESTADD;
  walk Init,Cond; nesting++ for Body then --;
  else block: ADD("else"), walk at current nesting (not an extra nesting level)
  else if: mark node, recurse at current nesting
switch/type-switch: NESTADD("switch"); walk Init and Tag/Assign;
  nesting++ for Body then --
select: NESTADD("select"); nesting++ for Body then --
for: NESTADD("for"); walk Init,Cond; nesting++ for Body then --;
  implementation does not walk Post (custom visitor returns nil)
range: NESTADD("for"); walk X; nesting++ for Body then --;
  does not walk Key/Value
FuncLit: walk Type; nesting++ for Body then -- (no increment for literal itself)
BranchStmt with nonnil Label: ADD(Tok.String); unlabeled break/continue no increment
BinaryExpr &&/|| not yet calculated:
  recursively mark exprs and collect logical operators in X/op/Y order through BinaryExpr only
  parentheses/non-Binary stop flattening; nonlogical binary itself adds no operator
  ADD for first operator and every change from last; all diagnostics use outer expression OpPos
  return normal visitor so subexpressions behind flattening barriers are still visited
CallExpr with bare Ident Fun: if Ident.Obj==function Name.Obj AND names equal → ADD recursion
ordinary nodes use normal ast.Walk; no indirect/method/mutual-recursion detection
```

**Dependencies / limitations:** syntactic parser object identity, not go/types. Synthetic literal name `_` does not match variable-name recursion. `//gocognit:ignore` leaves cyclomatic function emitted with missing cognitive entry→0, unlike gocyclo ignore. Logical grouping depends on parentheses. **Cost:** ordinary visitor O(A); recursive operator-slice merging can be O(A²) for skewed binary trees; space O(A), recursion depth AST depth. **Tests:** [TestNestedLiteralCognitiveNesting L32–48](../../gstyle/adapters/gocyclo/literal_test.go#L32-L48) asserts 4 (outer if + nested closure if at nesting 2); literal and physical-position tests above. **Distinguishing design:** function with logical expression in `for` Post versus same expression in body yields omitted versus counted cognitive Post evidence; cyclomatic walks both. Unexecuted. Dependency tests/rangeiter analyzer internals not claimed audited.

## Mutation, provenance and direct effects

### mutation.go-binding-provenance — whole-body alias/provenance collection

**Locations / helpers:** [collectBindings/bindAssignments/assignmentValue/addressBinding/unknownBinding L13–89](../../gstyle/adapters/goquality/mutation.go#L13-L89), [origin/constructedOrigin/objectOrigin/bindingOrigin L226–333](../../gstyle/adapters/goquality/mutation.go#L226-L333). **Callers:** extractFunction before event walk; mutation place/storage consumers. **Activation:** every typed body, including nested closures. **Inputs:** type-object bindings; **outputs:** local/external/unknown classification, not compiler heap escape analysis.

```text
bindings := object→{values:[],unknown:false}; parameterObjects initially outer+receiver
ast.Inspect body including nested literals:
  literal → add all named literal parameters to parameterObjects
  AssignStmt → for Unparen(Lhs[i]) identifier with object, append assignmentValue
  ValueSpec → same for declared names/Values
  RangeStmt → mark identifier Key/Value bindings unknown (both := and =)
  Unary &: mark Unparen(X) identifier binding unknown
assignmentValue: no RHS→nil; equal RHS/LHS counts→RHS[i]; else every place gets RHS[0]
origin(nil)=local; Ident→objectOrigin; Paren→origin(X); Slice→mutation.go-value-array;
  &: placeProvenance(X); other unary→unknown
  CompositeLit→local (does not inspect reference-bearing fields)
  Call with unwrapped identifier builtin make/new/append→local; other calls→unknown
  Selector→fieldOrigin; other expressions including StarExpr→unknown
objectOrigin: nil→unknown; package var→external; parameter object→external
  seen cycle→unknown; missing binding→unknown
  mark seen (remove on return); binding.unknown→unknown; no values→local
  evaluate all retained values recursively; all same provenance→that value; any mismatch→unknown
fieldOrigin: root package var or any parameter→external; no root or other local root→unknown
```

**Parameters / invariants:** flow-insensitive union over all source assignments, even dead branches; no last-write wins, control-flow fixpoint, alias-target mutation propagation or parameter substitution. Address taking only poisons bare identifier bindings; still `&localScalar` has local place provenance. Parameters are always external origins even after reassignment to new owned storage, but writing their value copy is local. Composite/new ownership does not guarantee reference fields are owned; field/projection rules conservatively handle some cases. `append` call result is local by itself: shared+append assignments to same variable become unknown via conflicting bindings; alias initialized only from `append(shared,...)` lacks that first-argument provenance (gap).

**Cost:** binding collection O(A+assignments); recursive origin may revisit bindings for every event, no memoization, potentially exponentially many paths in alias DAGs; cycles terminated via seen. **Tests:** [TestTypedWritesAndAliasProvenance L38–78](../../gstyle/adapters/goquality/analyzer_test.go#L38-L78), [TestAliasingProvenancePreservesOwnedStorage L39–68](../../gstyle/adapters/goquality/aliasing_test.go#L39-L68), [TestParenthesizedPlacesMatchUnwrappedPlaces L34–64](../../gstyle/adapters/goquality/parenthesized_place_test.go#L34-L64), closure tests. **Examples / fixture design:** new then conditional shared assignment→unknown; pure chain of new aliases→local; cycle→unknown. Compare `local:=shared; local=append(local,x)` to `local:=append(shared,x); local[0]=...` for missing RHS storage propagation (source inference; not executed).

### mutation.go-place-events — write counting, root identity and observable storage

**Locations:** [assignment/rangeAssignment L233–251](../../gstyle/adapters/goquality/function.go#L233-L251), [mutate/discardedPlace/placeRoot/projectedBase/selectorProvenance/embeddedPointer/indexProvenance L91–224](../../gstyle/adapters/goquality/mutation.go#L91-L224), [objectID L348–351](../../gstyle/adapters/goquality/function.go#L348-L351). **Callers:** body visitor Assign/Range/IncDec and mutating builtins; **outputs:** ordered Mutation events or intrinsic Global effects. **Inputs:** AST place, event position, storage flag; provenance producer is binding record above.

```text
Assign LHS each: if bare Ident with TypesInfo.Defs nonnil → skip initialization;
  otherwise mutate(place, statement.Pos, storage=false)
Range: only Tok==ASSIGN; mutate nonnil Key/Value; := emits no writes
IncDec: mutate(X,Pos,false)
mutate:
  Unparen(place) bare "_" → return
  root := ObjectOf Ident; Selector: if Sel object package var→that root,
    else recurse X and append literal field name
  Index/Slice/Star/Paren: recurse X; unknown shape→nil root (indices are not encoded)
  package-variable root → append Global resolved-variable effect; no Mutation
  provenance := origin(place) if storage else placeProvenance(place)
  root present → Root=object.Name, RootID=physical object declaration "line:column"
  no root → Root="<temporary>", RootID=physical event "line:column"
  FieldPath=join collected selector names with '.'; Line=physical event line
placeProvenance:
  Ident→local; Paren→recurse; Star→origin(X)
  Selector: if any intermediate promoted field pointer in compiler Selection.Index:
      fieldOrigin(selector)
    else if underlying TypeOf(X) is pointer: origin(X)
    else placeProvenance(X)
  Index: value-array storage→placeProvenance(X), otherwise origin(X)
  other→unknown
embeddedPointer: strip one receiver pointer; traverse Selection.Index excluding final field;
  return true immediately when intermediate struct field's underlying type is pointer
```

**Parameters / limitations:** one write event per LHS syntax, not runtime iteration count. RootID disambiguates shadows within a function but contains no filename. Index values and explicit/promoted path identity do not normalize physical memory aliases; alias roots remain different budget targets. Bare parameter reassignment counts as local mutation. Package-global writes never enter mutation budgets. Global effect insertion here is unconditional; later identifier reads deduplicate against existing same-line detail. **Cost:** O(place depth+provenance cost) per event; promoted traversal compiler-dependent, no malformed-selection guards.

**Tests:** tuple/temporary test [L163–177](../../gstyle/adapters/goquality/analyzer_test.go#L163-L177), [promoted pointer tests L28–77](../../gstyle/adapters/goquality/promoted_pointer_test.go#L28-L77), parenthesized/blank and aliasing tests; [TestShadowedRootsRemainDistinct L287–293](../../gstyle/domain/quality/evaluate_test.go#L287-L293). **Distinguishing designs:** slice `p[0]` and `p[1]` share root target; `alias:=p` keeps alias target separate despite same external storage; `global++` adds Global but zero Mutation. Promoted pointer copied into local wrapper yields unknown while copied embedded value yields local. **Unresolved:** no proven complete ownership/escape model.

### mutation.go-value-array — generic/value-array ownership variant

**Locations:** [valueArray/arrayRestriction/arrayTerms L7–38](../../gstyle/adapters/goquality/array_type.go#L7-L38), [indexProvenance/sliceOrigin L219–224, L275–280](../../gstyle/adapters/goquality/mutation.go#L219-L224). **Callers / activation:** every index write and slice-origin query; generic constraints opt in through types, no config flag. **Inputs:** underlying go/types type. **Outputs:** boolean “value-array storage,” then local-place versus reference-origin provenance.

```text
valueArray(type): Array→true;
  Interface→true if ANY embedded type recursively valueArray (constraint intersection);
  Union→true iff nonempty and EVERY term type recursively valueArray;
  nil/Pointer/Slice/other→false
index X[i]: if valueArray(TypeOf(X)) use placeProvenance(X); else origin(X)
slice X[a:b]: if valueArray(TypeOf(X)) use placeProvenance(X); else origin(X,seen)
```

**Limits / dependencies:** uses compiler's underlying constraint representation, no compiler type-set expansion or recursion cache. Mixed array/slice union fails array guard; pointer-to-array is reference storage. **Cost:** recursive constraint size plus provenance, no explicit cap.

**Tests:** [TestGenericArrayStorageUsesValueOwnership L11–39](../../gstyle/adapters/goquality/generic_array_test.go#L11-L39): arrays, all-array unions/named/intersections local; pointer/slice/mixed external. [TestReducedGenericArrayCopyIsEffectFree L41–58](../../gstyle/adapters/goquality/generic_array_test.go#L41-L58). **Examples / distinguishing fixture:** `Copy[T ~[1]int]` local indexed copy vs `T ~[]int` external; direct array parameter write also local. **Gap:** general ownership of generic structs/reference fields not established.

### effects.go-call-resolution — typed static/dynamic calls and builtin side effects

**Locations / helpers:** [call/unwrappedCallee/calledObject/interfaceCall/builtin/conversion L12–35, L130–195](../../gstyle/adapters/goquality/call.go#L130-L195), [resolvedName L287–303](../../gstyle/adapters/goquality/function.go#L287-L303). **Callers:** AST visitor CallExpr, including nested closures; **outputs:** Call facts, mutation events, or intrinsic effects. **Inputs:** call AST/type objects; **activation:** all typed extraction.

```text
fun := strip Paren/Index/IndexList recursively from call.Fun
object := ObjectOf(fun Ident or Selector.Sel), else nil
Builtin → do not emit Call:
  append/copy/delete/clear → mutate first Arg if present, storage=true
  print/println → IO detail builtin.name
  panic/recover → Panic detail builtin.name
  close → Unknown detail channel close
  Add/Slice/SliceData/String/StringData → Unsafe detail unsafe.name
  other builtins→no effect
if original call.Fun Types entry IsType:
  result underlying Basic UnsafePointer→Unsafe "unsafe pointer conversion"; else nothing
  do not emit Call
else classify explicit Args (facts.go-parameter-arguments)
*types.Func → Callee=resolvedName, Local=(object.Pkg==current pkg.Types),
  Dynamic=(fun is selector && selection exists && selection.Recv.Underlying is Interface)
*types.Var → Callee=object.Name, Dynamic=true, Local=false
other → Callee="<dynamic>", Dynamic=true, Local=false
all recorded at physical call.Pos line
```

**Limitations / dependencies:** no mutator-name heuristic or receiver alias/effect substitution. Function variables/closures/IIFEs remain dynamic, even if body was folded into enclosing fact. Static calls across packages have no helper body here. Builtin `append` always records destination mutation regardless of possible fresh allocation. **Cost:** O(callee wrapper depth + arguments + provenance work).

**Tests:** [TestCallsUseTypesRatherThanMutatorNames L80–97](../../gstyle/adapters/goquality/analyzer_test.go#L80-L97), [TestUnsafeUsesTypesAndExcludesSizeof L179–189](../../gstyle/adapters/goquality/analyzer_test.go#L179-L189), local-helper tests. **Distinguishing fixture:** interface `io.Reader.Read` produces Dynamic=true but later prefix still classifies IO; `b.Bump()` is a Call, not name-derived mutation; `unsafe.Sizeof` is not unsafe effect, `unsafe.Add` is. **Unknown:** callback invocation counts/targets and actual builtin allocation behavior are not modeled.

### facts.go-parameter-arguments — syntactic forwarding metadata

**Locations:** [buildParams/paramType/countParamUse L117–178](../../gstyle/adapters/goquality/function.go#L117-L178), [classifyArgs/classifyArg/classifyIdentArg/peelArg/localFieldRoot/isFieldRoot L40–128](../../gstyle/adapters/goquality/call.go#L40-L128). **Callers / activation:** indexed once per typed outer function, explicit recorded-call arguments; consumed by refactor planning, not mutation provenance. **Outputs:** parameter positions/name/type/Uses and `{param,const,field,other}` ArgSource.

```text
build source-order receiver-excluded ParamList and object→index (quality.go-counts)
for each explicit call argument:
  peel ParenExpr and UnaryExpr Op=& or *; other Unary stops
  peeled Ident whose Uses object is outer parameter → param(index)
  peeled Ident whose Uses object is *types.Const → const
  BasicLit → const
  Selector with X recursively rooted via peelArg/Selector at:
    outer parameter, receiver object, or Var with nonnil Pkg and Parent!=Pkg.Scope → field
  otherwise other
nil Args → nil; callee receiver not inserted into Args
outer parameter Uses count increments every encountered matching Uses Ident, including captured uses
```

**Limitations / divergence:** actual dereference syntax is `ast.StarExpr`, which `peelArg` does **not** handle despite comment saying it strips `*`; `*p` is therefore other (source inference). Qualified named constant selectors normally classify other, not const. `nil` is other. Variadic Args is syntactic count; Ellipsis is not recorded, trailing callee-parameter positions limited downstream. Type qualifier is package name, permitting same-spelling types from different import paths to collide in bundle keys. **Cost:** O(A+argument wrapper depth), O(P) metadata.

**Tests:** [TestArgProvenanceClassification L34–60](../../gstyle/adapters/goquality/args_test.go#L34-L60), [TestArgFieldThroughReceiver L62–79](../../gstyle/adapters/goquality/args_test.go#L62-L79), [args fixture L14–27](../../gstyle/adapters/goquality/testdata/args/args.go#L14-L27). **Examples / distinguishing fixture:** `targetPtr(&p1,p2)`→param0,param1; `target(p1+1,...)`→other; add `target(*ptr,...)` to distinguish StarExpr from comment's promised stripping. **Unknown:** no execution of dereference or qualified-constant boundary fixture.

### effects.go-intrinsic — globals, channels, goroutines and conversions

**Locations:** [visitEffect/effect/globalRead/hasGlobalEffect/packageVariable L208–221, L253–285](../../gstyle/adapters/goquality/function.go#L208-L221); builtin/conversion record above. **Callers / activation:** all body visits including uncalled closure bodies. **Inputs:** AST and type variable objects. **Outputs:** ordered intrinsic Effect facts, no callee expansion required.

```text
GoStmt → unknown "goroutine launch"
SendStmt → unknown "channel send"
UnaryExpr Op=<− → unknown "channel receive"
Ident Uses *types.Var where Pkg!=nil && Parent==Pkg.Scope:
  detail=package.Path+"."+Name; physical line
  if existing Global effect same detail+line → skip, else append Global
package variable mutate → unconditional Global, not Mutation (mutation.go-place-events)
unsafe conversions/unsafe selected builtins; IO print; Panic panic/recover; unknown close as above
```

**Limitations / invariant:** unknown intrinsic effects make Complete=false but do not increment UnclassifiedCalls. Calls inside GoStmt are still independently visited, so launch unknown plus callee effect may coexist. Global reads and writes collapsed per line only for identifier reads; two same-line writes can produce duplicate Global effects. Constants/package funcs are not globals. **Cost:** global dedup linear scan of accumulated effects per identifier, worst O(AE); event space O(E).

**Tests / examples:** typed Writes fixture global write assertion, unsafe test, alias wrapper incompleteness tests. No dedicated scoped channel/goroutine assertion identified. **Distinguishing design:** one channel send → incomplete, unclassified calls=0; two `global++` on same line may retain two Global effects. `go fmt.Println(...)` contributes unknown launch + IO. Unexecuted. **Gap:** no scheduling/control-flow/escape analysis.

## Policy classification, helper summaries and detectors

### effects.go-prefix-classification — normalization and curated policy table

**Locations:** [NormalizeCallee/withoutGenericArguments L322–348](../../gstyle/domain/quality/evaluate.go#L322-L348), [prefixKind L117–125](../../gstyle/domain/quality/local_calls.go#L117-L125), [stdlibRules/prefixes/ClassifyCallee L28–531](../../gstyle/domain/quality/stdlib.go#L28-L531), [thirdPartyPrefixes L177–186](../../gstyle/domain/quality/config.go#L177-L186). **Callers:** transitive resolver with supplied config; exported `ClassifyCallee` uses cached defaults; external [gopatterns.builder.callExpr L267–268](../../gstyle/adapters/gopatterns/builder.go#L267-L268) uses exported classifier. **Inputs / outputs:** callee string→Kind+configured flag; unconfigured defaults Unknown. **Parameters:** byte-prefix matching, longest wins, later equal-length wins; no separator/end-of-symbol test.

```text
NormalizeCallee:
  if contains []<> OR invalid UTF8:
    depth=0; range runes
    [ or < → depth++; ] or > → decrement if >0, otherwise discard
    other rune → write only if depth=0 (invalid UTF8 range produces replacement rune)
  ReplaceAll("::::","::") once (not iterative)
prefixes: each stdlib rule with no names emits pkg+"."; otherwise pkg+"."+each name
  preserve declaration order; append three third-party defaults:
    charm.land/lipgloss; github.com/charmbracelet/lipgloss;
    github.com/charmbracelet/x/ansi. → none
prefixKind(name,prefixes): best=-1,kind=unknown
  for prefix: if len(Path)>=best && HasPrefix(name,Path): best=len(Path),kind=Kind
  return kind,best>=0
ClassifyCallee: sync.Once builds defaultPrefixes; normalize; prefixKind; return kind only
```

**Table variants reviewed:** [pure transformations/codecs/crypto L28–156](../../gstyle/domain/quality/stdlib.go#L28-L156), [buffered/core IO/OS/format/log L158–273](../../gstyle/domain/quality/stdlib.go#L158-L273), [time/network/database L275–358](../../gstyle/domain/quality/stdlib.go#L275-L358), [reflection/templates/images/MIME/toolchain/runtime/sync/testing/flag L360–491](../../gstyle/domain/quality/stdlib.go#L360-L491). Exact table entries are the linked policy input, not claims of actual purity. Important branches: json Marshal/Unmarshal/Decoder.Decode/Encoder.Encode→unknown; other JSON defaults none; sync/atomic/context and reflect blanket none; database/sql blanket none with IO method overrides; io/os/fmt/time/net largely enumerated prefixes (not universal coverage of all functions); unsafe blanket unsafe; panic weight separately zero. Three third-party defaults are raw prefixes without full package boundary for lipgloss.

**Limitations / divergence:** comment that all stdlib calls avoid Unknown is not enforced; coverage test accepts any one prefix within a package, not every API. Policy precedes dynamic check: interface-dispatched known IO/None is classified without body inspection. Generics stripping is delimiter-depth not balanced typed syntax; malformed closes discarded, unmatched opens drop suffix; mixed []<> accepted. Repeated colon normalization need not be idempotent (`::::::::`→`::::`→`::`, inference). Exported classifier ignores runtime TOML overrides. **Cost:** O(callee bytes + total prefix-match cost), no per-callee result cache; only table initialization cached.

**Tests:** [classification/normalization tests L50–112, L179–213](../../gstyle/domain/quality/evaluate_test.go#L179-L213), [TestStdlibCoverage L12–49](../../gstyle/domain/quality/stdlib_test.go#L12-L49), [TestQualityClassifyCallee L101–110](../../gstyle/domain/patterns/effects_test.go#L101-L110). **Distinguishing design:** known prefix `fmt.Print` matches `fmt.PrintXYZ`; only package coverage can pass while an unlisted method still Unknown; runtime override affects Evaluate but not exported classifier. **Unknown:** table correctness against real API side effects not proven.

### effects.go-helper-evidence — reachable same-package body capture

**Locations:** [attachHelpers/reachableHelpers L10–42](../../gstyle/adapters/goquality/helpers.go#L10-L42), [extractPackage L173–191](../../gstyle/adapters/goquality/analyzer.go#L173-L191). **Callers:** per-package extraction; every selected root fact. **Inputs:** selected functions plus all available same-package syntax bodies; **outputs:** flat sorted Helper list retaining only Name/Mutations/Calls/Effects. **Parameters:** no depth/effect cap at capture; normalize name for indexing and seen.

```text
index available functions by NormalizeCallee(Name), last encountered wins
for root function:
  seen={Normalize(root.Name)}; pending=clone(root.Calls); helpers=[]
  while pending nonempty: pop last Call
    skip !Local || Dynamic
    normalized target absent or seen → skip
    mark seen; append Helper(target.Name,Mutations,Calls,Effects)
    append target.Calls to pending
  sort Helpers by original Name; attach to emitted fact
```

**Limitations / dependencies:** generated/unselected helpers can contribute; source outside root was skipped before capture. No DDD, Source, Params, ParamList or suppression in Helper schema; helper's own suppression does not remove inherited effects, and DDD violations do not propagate. Normalized-name collisions silently overwrite; root name seeded seen avoids capturing root again (resolver separately includes it). **Cost:** each root O(H+reachable C), plus O(H log H); across N roots potentially repeated graph capture O(N(H+C)), evidence duplication in exported facts.

**Tests:** [TestHelperFactsSurviveFileSelectionAndPolicyReevaluation L94–134](../../gstyle/adapters/goquality/local_helpers_test.go#L94-L134), facts-export helper test. **Examples / design:** caller selected alone with generated helper retains IO; dynamic function variable body is not helper-resolved; two `init` names are not unique helper graph identities. **Unknown:** name collisions/build variant availability not tested here.

### effects.transitive-summary — bounded recursive expansion and unknown evidence

**Locations / helpers:** [localCalls/calls/call/classifiedCall/helper/atCall/prefixKind/limitedSummary L8–135](../../gstyle/domain/quality/local_calls.go#L8-L135). **Callers / activation:** `functionEffects` for every evaluated function; config prefix overrides can bypass expansion. **Inputs:** Function body plus flat Helpers and prefixes. **Outputs:** ordered effect multiset and UnclassifiedCalls, remapped to immediate call site. **Parameters:** active helper limit 32; local effect limit 4096; cache per root evaluation, keyed normalized helper name.

```text
helpers={Normalize(root.Name):root body}; add supplied Helpers by normalized name
resolver active={},cache={}; evaluate root.Calls (root not pre-marked active)
call(c): normalize; (kind,configured)=prefixKind
  configured → classified(c,kind), even if c.Dynamic or c.Local
  not(Local && !Dynamic) → unknown
  active[name] OR len(active)>=32 → unknown (before cache check)
  missing helper→unknown
  otherwise atCall(c,helperSummary(name))
classified none→no events/unclassified=0
  other→one Effect(kind,original Callee,call.Line); unknown→unclassified=1
helperSummary: cached name→return
  mark active; summarize helper.Calls; append helper.Effects then mutationEffects(helper.Mutations)
  if len(effects)>4096: clone first4095 + Unknown(name+" (local summary limit)",Line=1), count+=1
  cache summary; unmark active
calls list in order: for each c compute summary
  if accumulated effects+summary effects>4096:
    retain accumulated first min(len,4095); append Unknown(c.Callee+" (local summary limit)",c.Line)
    unclassified:=previous accumulated unclassified+1; return immediately
  append summary events; add summary unclassified
atCall: copy effects; Line:=call.Line; Detail:=call.Callee+" → "+old.Detail;
  Via:=Normalize(call.Callee) after last slash (immediate helper, overwrites inherited Via)
```

**Invariants / limitations:** recursion is not a least fixed point: cycles/depth produce Unknown plus preserved known effects. Multiple call sites multiply helper event counts; no invocation frequency/control-flow feasibility. Rewrites lines to caller, loses original effect positions except textual chain. No argument-sensitive ownership substitution: helper parameter mutation remains external even if caller passes a newly owned object. Top-level direct effects/mutations are appended outside resolver cap; 4096 is not total per-function effect cap. During aggregate truncation previously accumulated unclassified counts can include discarded events, whereas overflowing call's summary count is not added. Cached summaries can depend on active/depth context; source inference is that call traversal order may affect bounded/cyclic graph summaries despite stable output sorting.

**Cost:** bounded event lists per summary but detail strings can grow with depth; per-root cache O(H×4096) event storage; prefix scan per call. Cyclic/depth context not part of cache key. **Tests:** [local_calls_test.go L10–233](../../gstyle/domain/quality/local_calls_test.go#L10-L233), exact limit test L142–165, recursion L167–185, immediate Via L187–233; typed local helpers L15–81. **Positive/negative/boundary:** pure known helper→complete zero; missing/dynamic helper→unknown; exactly4096 call effects stays complete,4097 truncates to4095 known+unknown. **Distinguishing fixture design:** deep first visit to a shared helper near depth32 then shallow visit, and reversed call order; check cached truncated summary. Also local new pointer passed to mutating helper versus inline write. Both unexecuted; no universal determinism/purity proof.

### effects.go-density — event weights, completeness and integer summary

**Locations:** [functionEffects/mutationEffects/compareEffects/effectWeight/summarize/effectCounts L267–320, L350–383](../../gstyle/domain/quality/evaluate.go#L267-L320), [densityDiagnostic/summarizeDensity L182–249](../../gstyle/domain/quality/evaluate.go#L182-L249). **Callers:** evaluateFunction, Evaluate report summary; **inputs:** direct/inherited events, mutations, statements and weights; **outputs:** ordered effects, density milli, Complete and UnclassifiedCalls, explanatory diagnostics.

```text
effects := copied f.Effects
for mutation: local→skip; external→mutation; unknown→unknown;
  Detail=Root + optional "."+FieldPath, Line=mutation.Line
append localCalls result (effects.transitive-summary); retain its unclassified count only
stable-sort effects by Line,Kind,Detail (Via not tie key)
weight=int64 sum of configured weight per event; complete=false iff any event.kind==unknown
DensityMilli := 1000*weight / int64(max(Statements,1)) (integer truncation)
if Statements>=MinStatements and density rule enabled && DensityMilli>Max && not suppressed:
  diagnostic effects=all effects including zero-weight events;
  total nonzero weights grouped by kind; order descending grouped weight then kind lexical;
  include Weight,Statements,KindWeights and arithmetic message
summary: count=max(numberFunctions,1); accumulate density/count quotients and density%count remainders;
  Mean=quotient+remainder/count; Max=max with initial0; count incomplete flags;
  emit counts for all 9 kinds in fixed kinds order, including zeros
```

**Parameters:** default weights and cutoff in config record; denominator floor1 affects stored density even below MinStatements. **Limitations / invariants:** Complete independent of weights (unknown with weight0 still incomplete); unknown mutation is not an unclassified call. Pure prefix means no event, whereas panic weight0 means event present but zero weight. No event dedup except extraction-specific global reads. Arithmetic has no general saturation guard; validated ordinary input bounds constrain single-function sums. Mean avoids summing full densities first. **Cost:** O(E log E + M + resolver), O(E) copied events.

**Tests:** [TestMutationBudgetsAndProvenance L23–48](../../gstyle/domain/quality/evaluate_test.go#L23-L48), [TestRealEffectsStillFail/TestDensityFindingExplainsItself L113–177](../../gstyle/domain/quality/evaluate_test.go#L113-L177), [TestStrictLimitsAndMinimumStatements L215–237](../../gstyle/domain/quality/evaluate_test.go#L215-L237), [TestMeanUsesExactIntegerMath L320–332](../../gstyle/domain/quality/evaluate_test.go#L320-L332). **Examples:** IO+2unknown+external mutation over10 statements→weight6,density600; density500 exactly does not fire; 2 statements can have stored high density without finding. **Distinguishing design:** same unknown effect with weight1 vs0 changes density, not completeness; intrinsic unknown vs unknown call changes UnclassifiedCalls. Not executed.

### quality.go-guardrails — all core rule measurements and diagnostic ordering

**Locations:** [Evaluate/evaluateFunction/parameterBudget/appendRule/mutationTargets L15–44, L90–177, L251–265](../../gstyle/domain/quality/evaluate.go#L90-L177). **Callers / activation:** public Evaluate via check/wrapper; all eight policy rules default enabled; invalid suppression always checked. **Inputs:** canonical facts/config; **outputs:** FunctionResult per canonical fact and diagnostics, sorted stable by position then RuleID. **Dependencies:** density, suppression, DDD, plans/groups.

```text
for each canonical function:
  compute functionEffects regardless of Enabled rules
  group all mutations (including local) by Root+"@"+RootID;
    granularity=field → append "."+FieldPath
  groups in sorted key order; event order preserved within each group
  result.Mutations=len(all events); MutatedTargets=len(groups)
  suppression parse; parse error → invalid_suppression Actual1/Limit0
  append rule measurements: fn_length=CodeLines; fn_params=parameterBudget;
    mutated_targets=len(groups); mutation_per_target once per group=len(group), include its events
  ordinary rule append only if Enabled && Actual>Max && rule not allowed
  apply density cutoff; append three DDD measurements
  attach fn_params plans
sort diagnostics stable by Path,Line,Column then RuleID (not Name/Actual/target)
report schema1; summary all functions; groups over all diagnostics
```

**Parameters / limitations:** all mutation provenances count for budgets although local mutations do not enter density. Roots are syntactic binding identity, not alias equivalence. String-concatenated target key is not collision-proof for arbitrary saved facts. Only `invalid_suppression` is unconditional. Registry has 12 recognized suppression/grouping IDs: eight policy IDs, invalid_suppression, nilerr, forcetypeassert, typednil. The last three have **no evaluator measurement/diagnostic production in this scope**; they are accepted names, not activated detectors here. Complexity scores do not feed these quality rules. **Cost:** O(M log targets + diagnostic sorting + dependencies).

**Tests:** mutation budgets root/field, strict limits/receiver, immutability/shadowing tests; DDD family separately recorded. **Examples / design:** 4 local writes same root→mutation_per_target actual4, density0; 4 external fields root mode→one target,field mode→4; Alias1 and Alias2 to same storage count separately. **Unknown:** external error-detector pipeline using the three suppression-only IDs is outside scope, not asserted absent globally.

### quality.go-ddd-aggregate — distinct syntactically mutated named struct types

**Locations:** [dddViolations L54–65](../../gstyle/adapters/goquality/function.go#L54-L65), dependency [FindAggregateMods/assignTargets/baseIdent/namedStructName/derefNamed L21–118](../../gstyle/adapters/gopatterns/ddd.go#L21-L118), [appendDDDDiagnostics/distinctDDDTypes L122–148](../../gstyle/domain/quality/evaluate.go#L122-L148). **Activation:** extraction unconditionally runs detector; rule enabled by default max1. **Inputs:** function typed body, DDD evidence; **outputs:** one evidence hit per short type name; diagnostic count of distinct Detail strings.

```text
walk entire body including closures
assignment targets: only LHS directly SelectorExpr; IncDec only X directly SelectorExpr
for target: strip Selector/Index/Star/Paren wrappers until Ident
  TypeOf(base id); strip pointer chain; require *types.Named with Struct underlying
  name=Named.Obj.Name (not package-qualified); skip if seen name, else emit hit
extract evidence RuleID=aggregate,Line=Fset.Position(fn.Pos).Line,Detail=TypeName
evaluate unique Detail for RuleID aggregate; append if count>config.Aggregate.Max,
  enabled and unsuppressed (default 2 types triggers)
```

**Limitations:** top-level parenthesized selector/index-write targets fail direct Selector guard; aliases of named structs not Unalias'ed here; short names merge packages; value-copy/local changes count too. No actual aggregate definition/boundary graph. Evidence uses logical Position for fn line (unlike most typed facts' physical positions), but emitted diagnostic is function's physical Location and does not include DDD hit details. **Cost:** O(A+place depth), type set O(types).

**Tests:** [TestDDDAggregateRule/SingleTypeOK L5–39](../../gstyle/domain/quality/ddd_test.go#L5-L39), [TestFindAggregateMods/SkipsNonStruct L44–85](../../gstyle/adapters/gopatterns/ddd_test.go#L44-L85). **Distinguishing design:** `(o.Total)=...` vs `o.Total=...`; quality mutation sees both but this detector's direct-selector guard differs. Two imported `Order` types collapse by name. **Unknown:** no executed package-name-collision/paren test; this is a heuristic, not verified DDD semantics.

### quality.go-ddd-repository — path/receiver database heuristic

**Locations:** [dddViolations L66–73](../../gstyle/adapters/goquality/function.go#L66-L73), [db tables/isRepositoryFile/FindDbCalls/isDbCall L121–253](../../gstyle/adapters/gopatterns/ddd.go#L121-L253), [appendDDDDiagnostics/countDDD L126–159](../../gstyle/domain/quality/evaluate.go#L126-L159). **Activation:** extraction always; repository enabled max0. **Outputs:** count of direct syntactic database-like calls outside exempt paths, not transitive repository breach.

```text
lowercase filepath.ToSlash(path); each slash segment strip trailing .go
if segment==adapters OR in {repository,repositories,repo,repos,dao,daos,store,stores,storage}
  OR HasPrefix/HasSuffix segment with one of {repo_,_repo,repository_,_repository}: exempt whole function
else walk body: only CallExpr with Fun directly SelectorExpr
  hit if X bare Ident and any:
    info.Uses[id] is PkgName with local import Name in {sql,gorm,pgx,sqlx,ent,bun,pop}
    TypeOf(id) stripped pointer chain is Named with Pkg.Path==database/sql
    receiver spelling in {db,DB,tx,Tx,conn,Conn,sqlDB,database}
      AND method in {Query,QueryRow,QueryContext,Exec,ExecContext,Prepare,PrepareContext,
                    Begin,BeginTx,Commit,Rollback}
  OR TypeOf(X) is pointer-chain Named from database/sql (any method)
  emit logical Fset.Position(call.Pos).Line; detail X.Name+"."+Sel.Name if X Ident,
    otherwise Sel.Name
DDD Detail="direct db call CALL in business logic"; evaluate count of repository entries
```

**Limitations:** database/sql type test does not constrain method or actual handle class; package heuristic uses alias/local name, not import path. Name heuristics still apply with valid type information, including non-db custom types. Parenthesized call.Fun is excluded; generated/unselected helper DDD not propagated; path exemption covers all adapters files. **Cost:** O(A+path segments+pointer depth).

**Tests:** [TestDDDRepositoryRule L41–57](../../gstyle/domain/quality/ddd_test.go#L41-L57), [TestIsRepositoryFile/FindDbCallsHeuristic/SkipsRepositoryFiles L87–146](../../gstyle/adapters/gopatterns/ddd_test.go#L87-L146). **Distinguishing design:** same fake `db.Query` in service vs adapters→hit/exempt; alias sql import to different name may bypass name heuristic for package functions; `sql.NullString.Value` can satisfy package-origin type test irrespective of query semantics. No execution. **Unknown:** precise false-positive/negative rates not measured.

### quality.go-ddd-mutable-identity — name-based ID assignments outside constructor names

**Locations:** [dddViolations L74–82](../../gstyle/adapters/goquality/function.go#L74-L82), [idFieldNames/isIDField L13–21](../../gstyle/adapters/gopatterns/entity.go#L13-L21), [FindMutableIdentities/isConstructorName/idAssignments L551–589](../../gstyle/adapters/gopatterns/entity.go#L551-L589), [DDD evaluator L129–159](../../gstyle/domain/quality/evaluate.go#L129-L159). **Activation:** extraction always, enabled max0. **Inputs:** syntactic fn.Name and AssignStmt targets; no type requirement. **Outputs:** one hit per LHS ID-like selector, then number of mutable_identity facts.

```text
if fn.Name starts "New" OR "Create": return no hits (case-sensitive)
walk body including closures; only AssignStmt:
  for each LHS directly SelectorExpr:
    lowercase Sel.Name in {id,uuid,guid} → hit
    Line=PositionFor(assign.Pos,false).Line; Field=Sel.Name; FuncName=fn.Name
DDD Detail="assigns .FIELD outside a constructor"; count all matching DDD RuleID entries
```

**Limitations:** IncDec omitted; paren selector omitted; any object named ID recognized regardless entity semantics. Method named New... exempt; synthetic initializer name is package-qualified `<literal...>` and is not a constructor by its assigned variable name. Hit details/lines do not survive into emitted DDD diagnostics as supporting evidence. **Cost:** O(A+LHS).

**Tests:** [TestDDDMutableIdentityRule L59–75](../../gstyle/domain/quality/ddd_test.go#L59-L75), [TestFindMutableIdentitiesSkipsConstructors/IgnoresNonID L56–113](../../gstyle/adapters/gopatterns/entity_test.go#L56-L113); DDD suppression test covers all three. **Distinguishing design:** `u.ID=...` triggers, `u.ID++` does not; `Newspaper` name exempts even if not factory. **Unknown:** intended constructor/type semantics not validated; no rewriting.

### quality.go-suppression — declaration-comment selection versus saved-string parser

**Locations:** [precedingSuppression L305–316](../../gstyle/adapters/goquality/function.go#L305-L316), [suppression/parseLintIgnore/splitRulesReason/validateSuppressedRules L8–88](../../gstyle/domain/quality/suppression.go#L8-L88), [evaluateFunction/appendRule L94–110, L168–177](../../gstyle/domain/quality/evaluate.go#L94-L110). **Inputs:** parsed declaration Doc or saved PrecedingLine string; **outputs:** allowed rule list or invalid_suppression diagnostic. **Activation:** always evaluated; can only suppress known ordinary checks, never invalid_suppression.

```text
extract from fn.Doc: walk comment list backwards, return first text containing "cyclo-allow";
  no match→""; initializer synthetic Doc=nil
evaluate TrimSpace(comment)
if HasPrefix("//lint:ignore"): parse alternate format
else absent "cyclo-allow"→no suppression/error
require HasPrefix("// cyclo-allow("); Cut remainder at "):", require nonblank reason
split comma rules; TrimSpace each; require in ruleIDs and not invalid_suppression
  on any failure allowed=nil + error; else allow list (duplicates retained)
lint parser: Fields after prefix; consume leading tokens whose TrimSuffix(",") consists solely
  of lowercase ASCII,digit,_; first other token begins reason
  require nonempty rule tokens and reason tokens; join rules by comma then same validation
```

**Limitations / divergence:** extractor never selects ordinary `//lint:ignore` comments without “cyclo-allow”, so advertised alternate form is primarily usable through saved facts, not normal typed source. Lowercase plain-word reasons are consumed as rule-like tokens; uppercase/punctuation can be needed to separate reason. Valid suppression only removes diagnostic emission, not measurement/effects/planning input or helper summaries. Block comment containing directive becomes invalid. Doc comment attachment, not literally preceding physical line, controls extraction. **Cost:** O(comment bytes+rules×12).

**Tests:** [TestSuppressionsRequireReasonAndKnownRules L239–253](../../gstyle/domain/quality/evaluate_test.go#L239-L253), [TestSuppressionReadsParsedDeclarationComments L34–72](../../gstyle/adapters/goquality/suppression_comment_test.go#L34-L72), reduced-string test, [TestDDDRulesSuppressible L77–94](../../gstyle/domain/quality/ddd_test.go#L77-L94). **Distinguishing design:** `//lint:ignore fn_params Reason` in raw Go Doc vs same saved PrecedingLine→extractor omission vs parser acceptance; lowercase `reason text`→no separator/reason. `cyclo-allow` in string literal never becomes Doc metadata. Not executed.

## Call graphs, overlapping edits and advisory parameter plans

### refactor.go-call-graph — normalized name lookup, graph/site variants

**Locations:** [nameIndex/resolvedCallees/callGraph L80–120](../../gstyle/domain/quality/groups.go#L80-L120), [stackSites/resolveSite/paramCount/forwards L39–92](../../gstyle/domain/quality/stacking.go#L39-L92). **Callers:** fix groups and parameter plans in Evaluate. **Inputs:** canonical emitted facts, no helper-only nodes. **Outputs:** unique adjacency graph and duplicate-preserving site list with Args. **Parameters:** staticLocal only; normalized name→last function index.

```text
index function names NormalizeCallee→index (last write wins)
callGraph: each Local && !Dynamic Call resolving by name adds callee edge
  reverse caller edge only if target!=self
  sort+dedup each adjacency list; self-callee edges retained
stackSites: same resolution guard but exclude self entirely
  retain one site per Call, in function/call order; store Args only (no Line/receiver)
paramCount: len(ParamList) if >0 else Params
forwards: for each arg at callee position to:
  ignore to>=calleeParamCount
  if Kind==param && Param<callerParamCount → append(from=Param,to)
  no Param>=0 guard
```

**Limits / divergence:** graph uses same-name overwrite instead of physical identity/conflict rejection. Helper evidence used for density but not graph if helper not emitted (file selection shrinks plans while preserving effects). Dynamic/interface/cross-package edges absent; no trait target inference. Site count differs from unique adjacency count and omits self calls. **Cost:** O(N+C+adjacency sorting); forwarding O(argument count).

**Tests:** [TestStackSitesSkipDynamicAndUnresolved L109–123](../../gstyle/domain/quality/stacking_test.go#L109-L123), [TestForwardsPairCallerAndCalleePositions/IgnoreOutOfRange L82–107](../../gstyle/domain/quality/stacking_test.go#L82-L107), groups dynamic/external table case. **Distinguishing design:** repeated caller calls callee twice→1 graph edge,2 sites; self-recursive call→graph self edge,0 sites; negative saved index passes upper-only forward guard. **Unknown:** no proof name index uniquely identifies logical functions.

### refactor.go-fix-groups — overlap components from bounded caller footprints

**Locations:** [BuildFixGroups/buildFixGroups/violatorRules/footprint/callersWithin/groupComponents/fixDSU L19–75, L129–187, L235–265](../../gstyle/domain/quality/groups.go#L129-L187). **Callers / activation:** Evaluate always, changed-filter rebuild, public API. **Inputs:** facts, diagnostics, Grouping; **outputs:** groups numbered1..G, violating members only with sorted unique rule IDs. **Default:** CallerRules=[fn_params], CallerHops=1.

```text
public BuildFixGroups canonicalizes/validates facts; does NOT Validate config/diagnostics
map positions(Path,Line,Column)→function index, Name ignored (last at same position wins)
map matched diagnostics to per-index rule set; ignore diagnostics with no position match
if none→nil groups
build call graph; for each violator in sorted function index order:
  if no violated rule in CallerRules: footprint={self}
  else seen={self}; frontier={self}; repeat exactly CallerHops times:
    frontier:=all unseen callers of frontier; add seen (no early empty-frontier stop)
  DSU union violator with every footprint index, including nonviolating callers
DSU find path compression; union smaller root index wins
collect only violator indices by DSU root; sort members by source index
sort components by first member index
each group: stackOrder(members,callees); ID=position+1; Stacked=(len(members)>1)
```

**Limitations:** nonviolating shared caller links signature fixes but is omitted from group member listing; group is edit-overlap heuristic not full validation footprint. No shared-type links or downstream callee hopping. Larger hop count includes graph reachability through nonviolators but ordering only considers direct member edges. Invalid public grouping (negative/huge hops) is not separately rejected. **Cost:** per violator bounded BFS O(hops+reachable graph) plus DSU (path compression, not union-by-rank); O(N+edges) graph memory, plus footprints.

**Tests:** [TestBuildFixGroups L70–195](../../gstyle/domain/quality/groups_test.go#L70-L195): unrelated/non-signature independent; caller-config change; shared hub; hop1 vs2; cycles; no violations; dynamic/external exclusion. **Distinguishing design:** x/y both fn_params called by clean hub→one group listing x/y, not hub; density rule leaves them independent by default. **Unknown:** group “independent” is not proven safe parallel editing.

### refactor.go-stack-order — deterministic greedy callee-first order with cycle fallback

**Locations:** [stackOrder/nextStackable/stackReady L191–233](../../gstyle/domain/quality/groups.go#L191-L233). **Callers:** fix groups; multi-member `buildPlan` assumes already supplied callee-first members but does not call this orderer. **Inputs:** ordered member indices and adjacency; **outputs:** permutation of members. **Parameters:** no SCC decomposition.

```text
waiting=set(members); ordered=[]
while waiting nonempty:
  scan members in given source order; choose first waiting member
    whose callee list contains no still-waiting member
  if none ready: choose first waiting member in source order
  if none at all: break; else remove chosen, append it
```

**Limitations / invariant:** cycles/self edges defeat readiness; fallback breaks them, not topological proof. Paths through nonmember functions do not constrain order. **Cost:** worst O(V² + repeated adjacency scans), V=members; O(V) space.

**Tests:** cycle and caller/callee rows in `TestBuildFixGroups`; two-hop case expects source-order top,leaf where intermediate is not member. **Distinguishing design:** a↔b emits a,b regardless cyclic dependency; acyclic a→b emits b,a. **Evidence:** source-backed deterministic fallback, no runtime plan safety claim.

### refactor.go-parameter-plan — per-diagnostic signature and direct-caller edits

**Locations:** [buildPlan/newPlanCtx/changedMembers/feedingSites/touchedFunctions/siteCounts/steps/planFindings L328–432](../../gstyle/domain/quality/stacking.go#L328-L432). **Callers / activation:** evaluate loop calls planFindings for each function; only unsuppressed/enabled `fn_params` findings receive plans. Internal multi-member helper is tested but production uses singleton members. **Inputs:** all emitted functions/sites, members, violators; **outputs:** nil if none changed else ordered StackPlan with Steps and Bundles.

```text
changed := members filtered by violators, retaining given order; changedSet
if changed empty→nil
feeding := sites where callee in changedSet
incoming[callee]++ for ALL sites; outgoing[caller]++ for feeding sites
Touched := sorted indices of feeding callers not changed + unchanged members
steps := changed then Touched; Signature=true only for changed
  each uses original Location, incoming/outgoing counts, passThrough(index,feeding)
bundles := closed-parameter-bundles(feeding)
planFindings(idx): each fn_params diagnostic → buildPlan(functions,sites,[idx],{idx:true})
```

**Limitations:** does not propagate signatures through callers automatically; doesn't combine same-group fn_params diagnostics into one multi-function plan. Config CallerHops affects FixGroups, not this direct-caller plan. Site counts exclude recursive/dynamic/unresolved calls; source not rewritten, compiled or tested for extraction safety. **Cost:** O(S+members+steps×S + bundle algorithm), space O(S+N).

**Tests:** [TestNoPlanWithoutFnParamsViolation/PlanListsCalleeSignatureThenCallSiteEdits L130–157](../../gstyle/domain/quality/stacking_test.go#L130-L157), multi-violator helper assertion L159–181, planFindings L291–319. **Distinguishing design:** leaf←mid←top with leaf finding→steps leaf(signature),mid(call sites); top not touched; adding CallerHops=2 does not extend singleton plan. **Evidence:** multi-member API behavior tested is not today's group-plan activation.

### refactor.go-pass-through — syntactic-use versus forwarding counts

**Locations:** [passThrough/forwardCounts L294–316](../../gstyle/domain/quality/stacking.go#L294-L316), forwarding metadata above. **Callers:** planCtx.step, only feeding sites into re-signed functions. **Inputs:** ParamList Uses, sites, positional forwards; **outputs:** names in original parameter order. **Parameters:** strict Uses>0; forwarded>=Uses (not equality).

```text
forwarded := map index→count
for site with caller==f: for each forwards(site): forwarded[from]++
for i,param in f.ParamList:
  if param.Uses>0 && forwarded[i]>=param.Uses: append param.Name
```

**Limitations:** no dataflow/escape equivalence; `&param` may be called pass-through despite address semantics; `*param` currently other due peelArg gap. No ParamList means no pass-through regardless Params. Counts are not validated for saved facts. Arguments to non-re-signed functions count Uses but do not increase forwarded. **Cost:** O(S×argument count + P) per step; O(P) map.

**Tests:** [TestOnlyForwardedParamIsPassThrough/TestUnusedParamIsNotPassThrough L236–265](../../gstyle/domain/quality/stacking_test.go#L236-L265). **Examples / design:** Uses1,forwarded1→included; Uses2,forwarded1→excluded; Uses0→excluded even if stale Args forwards. Malformed Uses1,forwarded2 is included (source behavior). **Unknown:** advisory removal is not established safe.

### refactor.closed-parameter-bundles — one-round intersection mining and closure filter

**Locations / symbols:** [bundleKey/calleeKey/compareBundleKey/setKey/intersectSets/subsetOf/closedSets/candidateSets/dedupSets/setSupport/keepClosed/isClosed/bundles/siteKeys/makeBundle/sortBundles L94–290](../../gstyle/domain/quality/stacking.go#L94-L290). **Callers / activation:** buildPlan over feeding sites; library-internal tested helper; no separate threshold flag. **Inputs:** explicit bare-parameter forwards at sites and callee ParamList. **Outputs:** Bundle candidate params sorted `(Name,Type)`, support Sites, sorted unique carrier names. **Parameters:** minimum itemset size2; support can be1; only one pairwise-intersection round, not exhaustive closure mining.

```text
perSite[i]: set of callee ParamList[forward.to].(Name,Type) for each accepted forward
  no valid callee ParamList index→no key; caller parameter names/types ignored
  duplicate identical keys collapse within site (including repeated same caller param)
candidates := input sets + intersection(input[i],input[j]) for i<j, only original inputs
  dedup by map equality, retain first occurrence order (linear containsSet scan)
for candidate with size>=2: support=count(input sets containing it)
retain iff no candidate strict superset with same support contains it
for retained set:
  sorted params by name,type
  carrier names=caller and callee of each supporting site; unique+lexical sort
sort bundles: size descending, Sites descending, lexicographic Functions
  no Params tie-break; SortFunc is not a stable sort
setKey helper encodes sorted name NUL type NUL but is unused by this mining path
```

**Invariants / limitations:** “closed” only against generated candidate universe; intersections of 3+ input sets can be absent. Empty/unnamed/duplicate callee names/types accepted; type strings package-name qualified, not path identity. No requirement distinct caller parameters, multi-site support, matching names across callers, type compatibility of a new struct, or safe API rewrite. Support counts sites, not functions. **Cost:** S sites, max P items: O(S²P) intersections, K≤S+S(S−1)/2; O(K²P) linear dedup/closure, O(KSP) support; candidate storage O(S²P), no cap.

**Tests:** [closed-set tests L49–80](../../gstyle/domain/quality/stacking_test.go#L49-L80), [bundle tests L183–234](../../gstyle/domain/quality/stacking_test.go#L183-L234), deterministic caller-index test L267–289. **Examples:** one site forwarding a,b,c yields one bundle support1; second site a,b yields 3-item/support1 and 2-item/support2; constants/fields excluded. **Distinguishing design:** inputs `{a,b,c,d}`,`{a,b,c,e}`,`{a,b,d,e}` generate abc,abd,abe but not triple intersection ab (support3). An exhaustive closed-itemset miner would expose ab; current source does not. Unexecuted. **Unknown:** tied bundle output order across changing candidate traversal is not guaranteed by compareBundles.

## Changed findings and supporting quality ratchet

### quality.go-changed-filter — whole evaluation, diagnostic-only diff projection

**Locations:** [onlyChanged/checkFacts L78–111](../../gstyle/application/qualitycheck/cli.go#L78-L111), [touchedFunctions/filterChanged L12–40](../../gstyle/application/qualitycheck/gitchanged.go#L12-L40); boundary dependency [ResolveBase/ChangedRanges/RootSpecs/NewDiff/Touched/untrackedRanges/parseFileRanges L50–270](../../gstyle/adapters/gitchanged/gitchanged.go#L50-L270). **Activation:** `--changed` on report formats; ignored on facts export. **Inputs:** all facts/report plus cwd/pathspecs/base; **outputs:** subset Diagnostics and rebuilt FixGroups, unchanged Functions/Summary and existing diagnostic Plans.

```text
Evaluate all facts first (operational errors cannot be hidden by --changed)
NewDiff(cwd,paths,base): GitRoot; explicit base verify commit or error;
  else first merge-base(HEAD,main/master); else HEAD; no commits→empty base
  convert paths (default '.') via lexical Rel to root (not literal pathspecs)
  if base!="": git diff no color/ext-diff/textconv, force a/ b/ prefixes, unified0
    parse new path from diff --git header (%q quoted pair, else Cut at " b/")
    hunk new start,count(default1) → range[start,start+count-1]; count0→[start,start]
  untracked ls-files --others --exclude-standard -z -- paths:
    only .go, count newline+1 (empty→0), unreadable skip; whole range[1,count]
  maps.Copy untracked ranges over tracked diff ranges
for fact: range=[Line,Line+count(Source,"\n")]; inclusive overlap→touch key=Path+NUL+Name
filter diagnostics by that key; rebuild BuildFixGroups(all facts,remaining diagnostics,config)
leave function list/summary and per-diagnostic plans unchanged
```

**Divergence / limitations:** deletion anchor is new start, not syntax diff's start+1; base is merge-base main/master, not first branch tip incl origins; untracked files included only here. No `--literal-pathspecs`, so special path characters may change Git selection. Identity ignores Line/Column, so same-path same-name functions share touched status (e.g. multiple init). Saved facts source/path may not describe current disk; no consistency check. Changed report still summarizes all functions, and plan can mention untouched callers. **Cost:** O(Git diff bytes + untracked bytes + N×ranges + diagnostics + groups).

**Tests:** [TestTouchedFunctions L16–31](../../gstyle/application/qualitycheck/gitchanged_test.go#L16-L31), [TestChangedEndToEnd L35–143](../../gstyle/application/qualitycheck/gitchanged_test.go#L35-L143), dependency [gitchanged_test.go L10–132](../../gstyle/adapters/gitchanged/gitchanged_test.go#L10-L132) (custom prefixes, deletion anchor, quoted paths, inclusive overlap). **Distinguishing design:** two init bodies in one file, edit one→both diagnostics can survive name-key filtering; pure deletion at closing boundary differs from syntax diff. **Evidence:** source and tests inspected, Git scenarios not run.

### quality.go-excess-ratchet — supporting rate gate, not source analysis

**Locations:** [aggregate/excessRate/worstOffenders/checkBaseline/checkRule/baselineDrift L76–192](../../gstyle/application/qualitygate/main.go#L76-L192), [writeBaseline/readReport/loadBaseline/main L202–332](../../gstyle/application/qualitygate/main.go#L202-L332). **Callers / activation:** separate qualitygate command; `--baseline` check or `--write` creation (never invoked by this audit). **Inputs:** evaluated check JSON report, baseline JSON; **outputs:** sorted drift violations or policy error; exit0/1/2. **Parameters:** baseline version constant1 (written, not validated on read), default write tolerance0.05, perUnit1000.0, epsilon1e-9, worst5.

```text
report decode once with normal JSON Decoder (unknown fields/trailing docs not rejected)
aggregate diagnostics by RuleID:
  reject if previously seen same rule has different Limit
  Excess += max(Actual-Limit,0) using int64; retain Limit
rate(excess,functions): functions<=0→0; else float64(excess)/float64(functions)*1000
checkBaseline loops ONLY rules present in current aggregate:
  missing baseline rule→Limit=currentLimit,Rate=0
  existing different Limit→hard error
  if rate>storedRate*(1+tolerance)+1e-9 → regression
  else if rate<storedRate*(1-tolerance)-1e-9 → improvement requiring refresh
  else no drift
regression worst:=matching diagnostics sorted excess descending then Name ascending, take5
sort violations by RuleID; improvements have no worst list
baseline write: aggregate observed rules only; time.Now UTC RFC3339, short git HEAD,
  Functions,tolerance,Version1, computed rates
main requires exactly one baseline/write; rejects tolerance<0;
  checking uses baseline.Tolerance, not CLI tolerance
loadBaseline JSON Unmarshal without validation of version/rates/counts/tolerance
```

**Limitations / consequential gap:** if a baseline rule's last current finding disappears, it is not in the current map and is **never checked** for improvement or limit change. Thus “every improvement beyond5% requires refresh” is not universal. Unknown fields/version and negative counts/rates may pass decoding; zero/nonpositive function count yields0 regardless excess. No checked arithmetic overflow/finite-float enforcement. Worst ties at equal excess+Name lack complete stable ordering. This is a supporting CI ratchet, not a detector. **Cost:** O(diagnostics + rules log rules), worst sorts per regressing rule; no denominator consistency validation.

**Tests:** [main_test.go L28–181](../../gstyle/application/qualitygate/main_test.go#L28-L181): aggregate limits/excess, identical/new/worse/improved findings, inclusive noise at5%, proportional growth, unbaselined rule, changed limit, worst order. No disappearing-rule/invalid-baseline/version assertion in scoped tests. **Distinguishing design:** baseline fn_params excess2/rate20, current diagnostics empty with100 functions→no improvement violation; retain a fn_params diagnostic Actual=Limit to force current rule presence→rate0 improvement violation. Not executed. **Unknown:** checked-in baseline contents/build integration not reviewed or regenerated.

## Consequential gaps and comparison handoff

These are source-backed boundaries or explicitly labeled inferences, not implemented fixes:

1. **facts.go-quality-schema / refactor.go-call-graph:** validation omits planning metadata; upper-only index guard admits negative saved parameter positions. Design a malformed-facts fixture before treating plans as safe.
2. **quality.go-suppression:** source extraction omits `lint:ignore`; saved-string parser has rule-like lowercase reason ambiguity. Compare source vs saved facts explicitly.
3. **mutation.go-binding-provenance / effects.transitive-summary:** append-result provenance and argument-insensitive helper mutation differ from inline storage ownership; no whole-program escape guarantee.
4. **effects.transitive-summary:** context-free name cache under context-sensitive active/depth truncation; test deep/shallow shared helper order and mutual recursion before claiming permutation invariance.
5. **facts.go-function-identity / refactor.go-call-graph / facts.go-report-join / quality.go-changed-filter:** physical tuple, normalized name, position-only and path+name are four different identities; duplicate init/name collisions need distinguishing fixtures.
6. **refactor.closed-parameter-bundles:** single pairwise intersection round misses some closed3+-input intersections; no support≥2 guard; tie comparator excludes Params.
7. **facts.go-parameter-arguments:** `ast.StarExpr` not peeled; package-name type qualification and qualified constants require boundary tests.
8. **quality.go-ddd-* / quality.go-config:** syntactic/name/path heuristics; three DDD maxima unvalidated; aggregate/repository logical hit lines and mutable identity physical hit lines differ. DDD details are counted but not attached as diagnostic evidence.
9. **quality.go-excess-ratchet:** vanished rules absent from current loop; no baseline schema/rate validation; improvement test covers reduced excess while still present, not eradication.
10. **effects.go-prefix-classification:** policy is a curated approximation, not API-effect proof; package coverage test is weak; exported classifier uses defaults while Evaluate accepts overrides.
11. **quality.go-cognitive:** custom for visitor omits Post; logical parentheses create flattening barriers; ignore directive presents zero score instead of absence. External package-loader/compiler internals remain unresolved.
12. **extraction.go-physical-mapping / quality.go-changed-filter:** Git bases, literal pathspec handling, untracked files and pure-deletion anchors differ. Report/facts paths do not establish parity.

**Completed source-backed IDs: 35.** Review counts, precise unfinished fixture list and resumption order are in the [coverage ledger](../go-quality-coverage.md). No implementation, baseline, golden, dependency, branch or commit was changed.
