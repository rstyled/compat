# Rust frontend and supporting evaluation — phase-one audit

**Status: substantive partial checkpoint, not a completed workspace audit.** Owned slice: `rstyle/crates/rstyle-driver`, `rstyle/crates/cargo-rstyle` including tests, `rstyle/scripts`, `rstyle/eval`, and `rstyle/rust_refactoring_examples`. Only this file and [rust-frontend-coverage.md](../rust-frontend-coverage.md) are written by this auditor.

Snapshot: Rust clean HEAD **`2c4752ca9c7b992e66d21380600a69f597133687`**. All source line ranges below refer to that snapshot. Parent `compat` HEAD does **not** identify the Rust child. Toolchain, hashes, full file/depth ledger, exact test index, unresolved boundaries and resumption instructions are in the coverage file.

## Record conventions and boundaries

Each numbered heading is one stable algorithm record (42 total). The family is its ID prefix. Each record gives purpose/output meaning, implementation symbols/ranges, callers, status/activation, inputs/outputs and missing cases, dependencies/parameters, Rust or Python/shell pseudocode, limitations/cost, exact test families, examples/divergence and a minimal distinguishing fixture. Closely coupled helpers are enumerated inside the record.

**Fields inherited by every record:**

- **Go pseudocode:** unresolved in this disjoint Rust slice, **not absent in Go**. No general Go/Rust equivalence is asserted.
- **Reference pseudocode:** CCGraph/PDF fidelity unresolved; the paper and historical reflection are not reviewed in this slice. Source comments saying “CCGraph” do not establish paper behavior. Supporting evaluation/statistical methods are separate from production analysis, not CCGraph stages.
- **Evidence status:** implementation/call-site descriptions are source-verified; named tests are **test assertions, not executed results**. Proposed examples/fixtures are unexecuted unless identified as existing assertions. Costs exclude rustc/library internals and downstream algorithms not reviewed here. No test, analyzer, benchmark, installation, source rewrite or suppression command was executed.
- **Default activation:** records 1–26 are production or production-opt-in as specified; 27 is supporting saved-facts access plus explicit absent modes; 28–42 are opt-in supporting tooling only. `usize` is host-sized; arithmetic is ordinary Rust arithmetic unless wrapping/saturating is explicitly stated. Source-derived absence means absence in this snapshot/scope, not a language-wide impossibility.

## Mode map and fact lifecycle

```text
cargo-rstyle [optional argv[1] == "rstyle" removed]
  --skill -> embedded usage text; no metadata/compiler/analysis
  no subcommand -> gather(facts, PDG=false) -> load style config -> evaluate -> report -> 0/1
  patterns -> gather(facts-sem, PDG=true) -> optional ledger load -> mine/prep
           -> existing-abstraction suppression -> ledger -> score -> top -> report -> CI gate
  ignore -> gather(facts-sem, PDG=true) -> load ledger -> same mining flags, unfiltered candidates
         -> status / prune[dry-run] / dismiss -> optionally write ledger -> 0
  errors -> 2 (clap parse errors are delegated to clap)

metadata -> selected target names -> pinned cargo check with workspace rustc wrapper
 -> after_analysis -> FnFacts JSON per <crate-name>-<lib|bin|test>.json
 -> filename selection -> deserialize unchanged FnFacts -> concatenate sorted filenames
 -> production merge by (path,line,column,display name), NOT by compiler id

style: merge -> path exclusions -> graph/effects -> rules -> comment suppressions
     -> diagnostic sort -> summary -> fix GROUP/PLAN suggestions (no rewrite)
patterns: merge -> abstraction/generated filtering -> PDG devirtualize -> hide implements
        -> signature mining -> PDG candidate mining -> locators/IDs -> ledger -> score/top
supporting saved-facts examples: direct FnFacts JSON -> first-by-ID -> raw PDGs/WL,
        with optional canonicalization; bypass production prep/ledger/style config
```

Neither a TUI nor RPC endpoint, changed-function filter, user-facing saved-facts input flag, automatic fixer, physical function coalescer, or separate extraction conversion schema exists in the inspected frontend. JSON serialization is not merely rendering: missing/default fields and merge identity affect analysis. Text layout, JSON pretty-printing, stdout/stderr mechanics and binary packaging alone are explicit non-analysis exclusions; semantic mode selection and exit gates are included.

## 1. `pipeline.cli-modes.rust-frontend`

**Purpose/output:** dispatch analysis and determine observable exit status. **Source:** [cargo main.rs](../../rstyle/crates/cargo-rstyle/src/main.rs#L19), `Cli`/`Command`/`PatternsArgs`/`IgnoreArgs`/`MineArgs` 19–125, `main` 333–362, `patterns` 216–239, `exit_with` 319–329. **Callers/status:** executable entrypoint; implemented/default style; opt-in patterns/ignore/skill. **Inputs/outputs:** argv, selected report and exit code; error strings lead to 2. Dependencies: clap 4.6.7 (parser internals unresolved), records 2, 21, 22, 26.

```text
remove ONLY the second argv element when exactly "rstyle"; clap parse
if skill: print embedded SKILL and exit 0 before gathering/config
match command:
  patterns: run record 22; exit its code
  ignore: run record 26; successful management command exits 0
  absent: run record 21; render; exit bool(nonempty diagnostics)
ordinary tool/config/compile/IO failure: stderr, exit 2
patterns code = bool(fail_on_candidates AND filtered report.candidates nonempty)
show_ignored: affects text listing only; JSON includes ignored without this flag
```

**Parameters:** global packages=[], all_targets=false, format=text, config/manifest/ignore_file=None; patterns min_score=0.0, top=None, no_ignore/show_ignored/fail_on_candidates=false. Ignore flags have clap requires/conflicts shown at 79–92; status may combine with ID prefix. Threshold/coverage inputs are `u32` with **no frontend clamp to 1000**; 1001 is used intentionally by evaluation. Cluster defaults 600/600, pair coverage=None, normalization none, single_call_guard=false, max_holes=3. Overrides preserve explicit zero; guard is ORed with default.

**Invariants/cost:** dispatch O(argv bytes), analysis external. Config is syntactically accepted globally but unused by patterns/ignore. **Tests:** CLI `clean_crate_exits_zero`, `violations_exit_one_and_match_golden_output`, `compile_errors_exit_two`, `bad_config_exits_two`, `ignore_rejects_unknown_ids_and_missing_modes`, `fail_on_candidates_exits_one_until_every_candidate_is_dismissed`. **Examples/divergence/fixture:** clean ->0, compile failure ->2; boundary `patterns --top 0 --fail-on-candidates` can exit 0 with mined candidates because gate follows truncation. Compare same pool with top=None versus 0; missing dedicated assertion. Existing tests do not establish the documentation's broader “any candidate” phrasing before display filters.

## 2. `extraction.compiler-targets.rust`

**Purpose/output:** choose packages, compiler targets and accepted fact filenames. **Source:** [workspace.rs](../../rstyle/crates/cargo-rstyle/src/workspace.rs#L25), `load` 25–37, `crate_names`/`unknown_packages` 39–57; [run.rs](../../rstyle/crates/cargo-rstyle/src/run.rs#L76), `cargo_args`/`command` 76–126; [driver main.rs](../../rstyle/crates/rstyle-driver/src/main.rs#L36), `flag_value`/`target_of`/`with_sysroot` 36–75, `main` 94–111; [collect.rs](../../rstyle/crates/cargo-rstyle/src/collect.rs#L14), `parse_name`/`Wanted::accepts` 14–27. **Callers/status/activation:** `gather` 154–184 in every analysis mode; implemented/default workspace, optional package/all-target selection. Dependencies: cargo metadata/check, rustc driver, cache record 3.

```text
cargo metadata --format-version 1 --no-deps [--manifest-path path]
fail on metadata failure or JSON error
selected names not exactly among metadata.packages names -> error(first unknown)
wanted crates = every target.name of selected packages (all if []), '-' replaced by '_'
cargo args = check --quiet + (--workspace if packages=[] else repeated -p name)
             + optional --all-targets + optional manifest path
wrapper: drop driver argv[0]; add --sysroot via wrapped rustc --print sysroot if missing
flag_value: first match --flag=value or --flag followed by next argument
reject extraction when no --crate-name, any arg starts_with('--print'), or crate=build_script_build
kind = 'test' if exact '--test'; else 'bin' if FIRST --crate-type == 'bin'; else 'lib'
if RSTYLE_OUT_DIR present and target accepted: callback writes <crate>-<kind>.json
else run compiler with NoOp callbacks
reader: require lowercase '.json', split at LAST '-'; crate must be wanted
accept kind lib/bin by default; with all_targets accept ANY kind suffix
```

**Limitations:** metadata model retains target name, not target kind, package ID or configuration. No cleanup of obsolete names. Non-bin crate types, examples compiled as bins, and comma-separated `--crate-type` are coarsely classified. Filename includes neither package nor target triple/profile/cfg; same-name/same-kind collisions can overwrite, including concurrent compilation (inference from filename key). Sysroot subprocess success status is not checked; successful spawn can append empty/non-success stdout. **Cost:** O(target names + argv scans + filename count), compiler cost unknown. **Tests:** `workspace::tests::{crate_names_replace_dashes,package_selection_filters}`, `run::tests::{default_selection_is_whole_workspace,package_selection_and_all_targets,toolchain_is_pinned_nightly}`, `collect::tests::{parses_crate_and_kind,filters_by_crate_and_kind}`, CLI `unknown_package_exits_two`, `compile_errors_exit_two`. **Examples/fixture:** wanted app accepts app-lib/bin, rejects other-lib and app-test unless all_targets; app-unknown.json accepted with all_targets. Two workspace packages with target name `shared` exercise first differing filename step; no collision/probe tests found in driver.

## 3. `cache.compiler-facts.rust`

**Purpose/output:** reuse Cargo compilation/facts while isolating style and semantic modes. **Source:** [run.rs](../../rstyle/crates/cargo-rstyle/src/run.rs#L20), `pinned_toolchain` 20–25, `driver_path` 27–42, `driver_fingerprint` 44–59, `command` 95–126; [cargo main.rs](../../rstyle/crates/cargo-rstyle/src/main.rs#L127), constants 127–130, `gather` 154–184. **Status/callers:** implemented/default all gather paths. Inputs: binary metadata, ambient env, Cargo fingerprints; outputs: command env, persisted fact directories. External dependency: Cargo cache algorithm unresolved, not a content-addressed facts cache implemented here.

```text
driver = RSTYLE_DRIVER if present (no existence check), else sibling rstyle-driver (must exist)
fingerprint = 'rstyle' + decimal(modified_unix_seconds or 0) + 'x' + decimal(length or 0)
              + ('p' if PDG else '')
root,target from cargo metadata
out = target/rstyle/{facts | facts-sem}; mkdir; builddir=target/rstyle/build
RUSTFLAGS = trim(existing RUSTFLAGS or '' + ' -Cmetadata=' + fingerprint)
set RUSTUP_TOOLCHAIN to embedded nightly-2026-09-30
set RUSTC_WORKSPACE_WRAPPER=driver, RUSTC_WRAPPER='', CARGO_TARGET_DIR=builddir
set RSTYLE_OUT_DIR=out, RSTYLE_ROOT=workspace root
remove RUSTC and RSTYLE_PDG; set RSTYLE_PDG=1 only for semantic mode
cargo check success -> read accepted JSON files; failure -> error, do NOT report cached facts
```

**Limitations:** mtime has whole-second resolution and length is not a content hash. Equal-length rebuild with unchanged/same-second mtime can collide. No facts schema/version, root, compiler revision or extraction config is in this custom fingerprint (Cargo adds its own inputs). Missing/deleted facts do not themselves dirty Cargo compilation; a fresh compile cache with a removed fact JSON can yield missing functions. Accepted stale files are not purged. Style/patterns use the same build directory but different flags and output folders. **Cost:** O(1) stat + Cargo-dependent check + JSON read. **Tests:** CLI `two_runs_are_byte_identical`, `config_change_reevaluates_without_recompiling` (fact mtime unchanged after threshold edit), `patterns_output_is_byte_identical_across_runs_and_copies`, `pdg_is_only_recorded_for_patterns_and_modes_do_not_clobber`; none proves invalidation under binary metadata collision or removed facts. **Fixture:** warm cache; delete one fact file, rerun without source changes; compare to fresh build. Positive cached repeat, negative mode cross-contamination, boundary equal metadata are separate cases, all unexecuted here.

## 4. `extraction.functions.rust`

**Purpose/output:** discover source-owned function bodies and produce complete per-function facts. **Source:** [extract.rs](../../rstyle/crates/rstyle-driver/src/extract.rs#L24), `crate_facts` 24–33, `function_facts` 35–85, `display_path` 133–141; [driver main.rs](../../rstyle/crates/rstyle-driver/src/main.rs#L84), callback 84–91. **Callers/status:** compiler after_analysis callback, implemented/default; PDG optional. Inputs: TyCtxt HIR body owners, workspace root; outputs: location-sorted FnFacts. Dependencies: records 5–17, source-map/rustc internals unresolved.

```text
for def_id in tcx.hir_body_owners():
  require DefKind Fn or AssocFn (not closure/const body owners)
  require fn_sig and body_id; reject sig.span.from_expansion()
  get snippet(sig.span through body.value.span); if error drop entire function
  start = lookup(sig.span.lo); require display_path(start.file,root)
  has_self = implicit_self; params = signature.inputs.len - bool(has_self)
  extract statement/call/effect/uses, mutation/type facts, signature, optional PDG
  implements = associated trait_item_def_id mapped to compiler definition ID, else None
  set source/name/id/location/preceding_line/param_list/top_statements
sort by (path,line,column,name); callback pretty-serializes and directly writes one JSON vector
```

**Limitations:** macro-generated function signatures are omitted entirely; macro expansions within handwritten functions are retained differently by each extractor. Outside-root absolute, non-real or unavailable local-path source files are dropped; relative real paths can pass without actual prefix membership. No canonicalization/symlink resolution. Snippet/path failure is silent omission, not an incomplete-function fact. Nested handwritten function items are separate body owners; ordinary closures are not standalone functions. **Cost:** O(body owners plus per-body traversals + F log F sorting + source bytes); rustc costs unknown. **Tests:** CLI `derived_code_is_not_analyzed` asserts 11 handwritten functions in violations, `clean_crate_exits_zero` asserts four, `facts_record_sig`, `facts_record_call_graph_ids_and_mutated_types`. **Fixture/examples:** ordinary impl method emitted; derive-generated method dropped; handwritten fn expanded by macro signature dropped. A root-external include or unreadable snippet distinguishes omission from unknown evidence; not tested in reviewed frontend.

## 5. `facts.function-identity.rust-frontend`

**Purpose/output:** compiler definition IDs and workspace membership, distinct from physical merge keys and reviewed-candidate locators. **Source:** [ids.rs](../../rstyle/crates/rstyle-driver/src/ids.rs#L11), `def_id_str` 11–17, `in_workspace` 21–25; `extract::display_path` 133–141 above. **Callers:** FnFacts.id/implements, workspace call edges, type IDs, PDG callees, mutation delegation; implemented/default. **Inputs/outputs:** DefId/root -> string or membership bool; parameters none.

```text
id = tcx.crate_name(def_id.krate) + tcx.def_path(def_id).to_string_no_crate_verbose()
workspace = display_path(source file containing tcx.def_span(def_id).lo,root) is Some
path helper: FileName::Real -> local_path -> strip_prefix(root), otherwise original path
return lossy string with '\\' replaced by '/' iff resulting path is NOT absolute
```

**Limitations:** `{impl#N}` order-dependent disambiguators remain; “stable” means caller/callee agreement, not stability after arbitrary edits. Display name uses a different rustc API. No source-content hash; no normalization of compiler IDs here. Membership trusts source spans/relative paths. Record 18 merges by display location, record 23 replaces impl ordinals for ledger names. **Cost:** compiler ID/path string length; external compiler queries unknown. **Tests:** CLI `facts_record_call_graph_ids_and_mutated_types`, `facts_record_sig`; core locator tests cover later correction, not the driver API itself. **Examples/fixture:** graph::direct and graph::Shape::area asserted; insert an unrelated impl block above a method, compare raw ID (can renumber) with locator (same owner/name). No Go/paper parity claim.

## 6. `extraction.counts.rust`

**Purpose/output:** recursive statements, top-level phases, parameter counts/uses, code-line/spacing input and preceding suppression line. **Source:** [effects.rs](../../rstyle/crates/rstyle-driver/src/effects.rs#L28), `param_index` 28–40, `collect` 42–65, `counts` 97–99, `on_path` 190–203, visitor 231–296; [extract.rs](../../rstyle/crates/rstyle-driver/src/extract.rs#L87), `top_statements` 87–93, `param_list` 95–122, `lines_above` 124–131; [lines.rs](../../rstyle/crates/rstyle-core/src/lines.rs#L5), `code_lines`/`line_has_code`/`has_blank_line`/`preceding_comment_line` 5–52. **Status/callers:** default extraction, source line helpers called by style rules. Inputs: HIR spans/patterns, source strings; outputs: `usize` counts and comment/string facts.

```text
generated_depth=unsafe_depth=statements=0; uses=[0]*body.params.len
counts(span) = !from_expansion(span) OR generated_depth==0
visit_stmt: statements += counts(stmt.span); depth += generated(stmt)
            walk_stmt; depth -= generated(stmt)
visit_expr: depth += generated(expr); inspect calls/paths; walk children; depth -= generated(expr)
visit_block: if tail exists statements += counts(tail.span); walk_block
visit_arm: if body not Block, statements += counts(body.span); walk_arm
simple parameter binding HirId -> index after skipping self; local path mention increments uses[index]
params count = signature inputs minus self; top = block.stmts.len + has_tail, non-block=1
param_list = zip(inputs,body.params), skip self; simple binding name else '_'
  type snippet whitespace-collapsed, snippet failure=''; uses[index] or 0
lines_above = file lines max(0,line-41)..line-1 (zero-based); choose nearest trim line
  not starting '#[' or '///'; do NOT skip blank, ordinary code or '//!'
code_lines: scan bytes per line, keep nested /* depth across lines
  '/*' increments; '*/' only while depth>0 decrements; outside '//' stops line
  any non-ASCII-whitespace outside comments makes line count
blank_line = any source.lines() line trim()==''
```

**Limitations:** recursive HIR count is not source semicolon count; generated-depth guard can suppress internal macro/desugaring statements, but user-spanned statements always count. Closure-body descent depends on rustc `OnlyBodies` traversal; uses may include closure mentions, confirmed only where tests assert. Destructured parameters have `_` and no simple binding index. Top-level Item statements count as phases though PDG ignores them. Code-line scanner is **not string-aware**: comment markers inside strings/raw strings can change counts. This is not cyclomatic/cognitive complexity; neither is computed by this frontend. **Cost:** O(visited HIR + source bytes); lookback capped 40 lines. **Tests:** CLI `facts_record_params_and_argument_provenance`, `fn_spacing_is_configurable`, `json_output_reports_resolved_mutations_and_effects`; core `lines::tests::{counts_only_code_lines,blank_line_detection,code_next_to_comments_counts,nested_block_comments,suppression_line_skips_attributes_and_docs}` and `rules::tests::{length_boundary,spacing_boundary_and_blank_line,long_initializers_do_not_count,spacing_zero_disables,params_boundary_and_self}`. **Fixture:** positive five top statements no blank line; negative blank anywhere even signature; boundary `"/*"` string, multiline attribute, blank between allow and fn distinguish lexical/nearest-line heuristic from parser-aware behavior.

## 7. `extraction.argument-sources.rust`

**Purpose/output:** ordered argument provenance for call graph/refactor plans, excluding receiver. **Source:** [args.rs](../../rstyle/crates/rstyle-driver/src/args.rs#L12), `peel`, `local_id`, `is_constant`, `local_field_chain`, `classify` 12–69; effects `sources`/`on_call`/`on_method` 159–188. **Status:** implemented/default workspace edges; no driver unit tests. Inputs: typeck, simple param index, HIR arg; output `Param(index)|Const|Field|Other`. Dependencies: records 6, 8, core graph/stacking consumers.

```text
peel repeated AddrOf(& or &mut), Unary(Deref), DropTemps
if peeled path resolves Local in param map: Param(index)
else if Lit: Const
else if Path resolves Const/AssocConst/ConstParam/Static/Ctor: Const
else if Field and recursively peeled base field-chain roots at ANY local binding: Field
else Other
direct FnDef method syntax Type::method(recv,...): skip first arg iff associated method
method syntax recv.method(args): classify only args (receiver excluded)
```

**Limitations:** local alias of a parameter is Other, no alias fixpoint; field of parameter is Field, not Param; array indexing/computed expression is Other; references/derefs erase passing mode. Static mut also classifies Const as provenance, independent of global-effect extraction. **Cost:** O(arg expression wrapper/field depth); memory O(argument count). **Tests:** CLI `facts_record_params_and_argument_provenance`, `param_plan_orders_callee_then_callers_with_bundle_and_pass_through` (consumption assertion, not alias correctness). **Examples/fixture:** `&*p` -> Param(0), `opts.tag` ->Field, `7` ->Const, `let q=p; f(q)` ->Other. Compare direct receiver syntax with method syntax; assert equal non-self provenance. Destructuring and alias boundary remain untested.

## 8. `extraction.calls-intrinsics.rust`

**Purpose/output:** HIR resolved call events, workspace edges, unsafe/global intrinsic events and parameter mentions. **Source:** [effects.rs](../../rstyle/crates/rstyle-driver/src/effects.rs#L87), Walker helpers 87–229, visitor 231–296; [paths.rs](../../rstyle/crates/rstyle-core/src/paths.rs#L4), `strip_generics` 4–23. **Status/callers:** implemented/default function extraction. Inputs: resolved expression types, receiver adjusted type, spans/root/params; outputs in compiler walk order; no call/event deduplication here. Dependencies: records 5, 7; core config classification/effect graph.

```text
Call(callee,args):
  FnDef(id): record_target(id,dynamic=false, sources after optional self skip)
  Closure/CoroutineClosure: record NO call event (children still visited)
  FnPtr: CallEvent('<fn pointer>',line,dynamic=true)
  other: CallEvent('<indirect callable>',line,dynamic=true)
MethodCall: if dependent_def_id missing, no event
  dynamic = adjusted receiver type.peel_refs is Dynamic; record_target
record_target: require Fn/AssocFn (constructors discarded)
  if in_workspace: append Edge(id,line,dynamic,args)
  if id.is_local: STOP (no CallEvent and no unsafe-function check)
  callee = strip_generics(tcx.def_path_str(id))
  if unsafe_depth==0 AND span not expansion AND callee unsafe: append Unsafe effect
  append CallEvent(callee,line,dynamic)
Path: count local param use; every path to Static mut appends Global effect (read OR write)
user-provided unsafe block: append Unsafe('unsafe block'), increase unsafe_depth during child walk
all event lines = lookup span.source_callsite().lo line
strip_generics removes ONLY '::<...>' with nesting; ordinary '<T as Trait>' stays
```

**Limitations:** cross-crate workspace call produces both edge and nonlocal CallEvent; local call only edge. Local unsafe calls outside explicit blocks bypass unsafe-function check. Intrinsic closure call itself is omitted, while nested walk may accumulate its contents using fixed enclosing typeck; precise rustc traversal/typeck boundary unresolved. Dynamic flag is not complete generic-dispatch uncertainty: only Dynamic receiver test; plain direct FnDef=false. Static mut access is classified regardless of whether a write. Macro-expanded calls remain CallEvents; unsafe call effect excludes expansion, user unsafe block still recorded. **Cost:** O(HIR plus args and callee path strings), workspace queries external. **Tests:** CLI `effects_are_classified_from_resolved_paths`, `facts_record_call_graph_ids_and_mutated_types` (dyn Shape in map closure), `effects_propagate_through_calls_and_stop_at_boundaries`; core paths tests named in coverage. **Fixture:** unsafe local versus external call without enclosing unsafe block, fn pointer versus closure callable, generic trait versus dyn; inspect separate edges/calls/effects, not only final density. Unclassified nondynamic external call is later ignored by style classification (not Unknown).

## 9. `extraction.mutations.rust`

**Purpose/output:** writes/mutable borrows, local/field identity, escaping/delegated flags and mutated workspace type IDs. **Source:** [mutations.rs](../../rstyle/crates/rstyle-driver/src/mutations.rs#L18), `collect` 18–47, Collector `record`/`is_workspace_reborrow`/`note_type`/`root_name`/`describe` 56–132, `field_name` 134–144, Delegate 146–171. **Status/callers:** implemented/default; rustc ExprUseVisitor internals unresolved (compiler source unavailable). Inputs: LateContext/body/typeck/places; outputs: callback-ordered MutationEvents, sorted unique types. No method-name mutation heuristic.

```text
create LateContext for def/body; ExprUseVisitor::for_clippy.consume_body; ignore returned result
Delegate.consume/use_cloned/fake_read/bind: no-op (initializer bind is NOT mutation)
Delegate.borrow: if kind==Mutable -> record(place,at,is_helper_call=true)
Delegate.mutate: record(...,false)
record:
  root name = local hir_name OR upvar.var_path.hir_name; rvalue/static -> drop
  note workspace ADT behind base_ty.peel_refs then one boxed_ty peel; insert definition ID in BTreeSet
  projection steps pair each projection with previous type
  field_path = dot join Field ADT field names by variant/index, otherwise numeric index
  escapes = ANY Deref with preceding type Ref OR RawPtr (Box itself stays owned)
  delegated = escapes AND is_helper_call AND LAST projection is Deref
              AND final place.ty ADT belongs to workspace
  escapes &= !delegated
  append root,field_path,line(source callsite),escapes,delegated
```

**Limitations:** helper classification flag covers **every mutable borrow**, not just a verified call expression/callee. Delegation is whole-object type/projection based; downstream pairs it to calls by line (not argument/root). Root identity is name string, so shadowed locals of same spelling collapse in mutation budgets. Index projections do not appear in field_path; no local alias canonicalization, heap model, return/escape proof or interior-mutability analysis here. Compiler consume error is ignored, no completeness field. **Cost:** compiler traversal unknown; collector O(callbacks × projection depth + T log T). **Tests:** CLI `json_output_reports_resolved_mutations_and_effects`, `facts_record_call_graph_ids_and_mutated_types`; core `rules::tests::{four_mutations_of_one_root_are_flagged,field_granularity_splits_targets,four_distinct_roots_are_flagged,local_mutations_count_for_budget_but_not_density,repeated_writes_to_one_target_count_once_for_density}` consume handmade facts, not compiler place guarantees. **Fixture:** initialize versus assign; mutate owned Box versus &mut T; borrow `&mut *p` into a local without calling; same-spelled shadowed `x`; two delegated calls on one source line. Verify raw flags/types before final scores. Whole-workspace helper mutation can be removed from direct density but retained in mutation budget.

## 10. `extraction.signature-shapes.rust`

**Purpose/output:** structural raw type/signature facts for methods and called functions. **Source:** [sig.rs](../../rstyle/crates/rstyle-driver/src/sig.rs#L11), `args_of`/`dyn_id`/`shape` 11–49, `impl_self_ty`/`split`/`receiver` 51–82, `sig_facts` 84–116, `shape_receiver`/`callee_sig` 118–160. **Status:** implemented/default signatures; callee labels only with PDG. Inputs: compiler Ty/DefId/HIR FnSig; outputs: TyShape and optional SigFacts. Dependencies: record 5; downstream shape normalization intentionally not done here.

```text
shape(type):
  Adt -> full definition ID + recursive TYPE args only (skip const/lifetime args)
  Ref -> mutable bool + inner (drop lifetime)
  Tuple/Slice/Array -> recursive elements (Array length discarded)
  Bool/Char/Int/Uint/Float/Str/Never -> compiler type.to_string
  Param -> generic index as usize; FnPtr -> FnPtr (no signature)
  Dynamic -> principal trait ID or ''; Alias of Opaque kind -> Opaque; else Other
own signature: require impl_of_assoc (free/default trait declaration body -> None)
  impl self only if ADT; otherwise self_ty=None,self_args=[]
  receiver: RefMut/Ref/Value only if direct inner/first ADT matches self_ty ID; else Other
  no self -> None receiver; skip self from params; shape return
  flags from HIR header; generics=own_counts.types
callee signature: require Fn or AssocFn, get instantiate_identity signature
  impl ADT receiver as above; trait/foreign without ADT: ref mut/ref/value from first type
  async/unsafe/const via tcx; generic type count only
```

**Limitations:** erased array lengths, lifetimes, const arguments, fn-pointer signatures, raw-pointer structure and nonopaque aliases; these can collapse to identical shapes. No substitution of actual call generic arguments: callee signature uses identity instantiation. `Box<Self>`/Pin receiver is Other. **Cost:** recursive type structure size, compiler queries unknown. **Tests:** CLI `facts_record_sig` (free sig null, Dog owner/receiver/return, trait impl link), `patterns_group_impls_that_differ_only_in_concrete_type_arguments` (downstream grouping). **Fixture:** methods taking `[u8;2]` and `[u8;3]` have same Array(u8) shape; positive &Self ->Ref, negative Box<Self> ->Other. Assert producer facts before normalized key comparisons.

## 11. `extraction.pdg-builder.rust`

**Purpose/output:** ordered HIR expression/value graph, **not a CFG/SSA/memory PDG**. **Source:** [pdg.rs](../../rstyle/crates/rstyle-driver/src/pdg.rs#L157), Builder/build/blank/lower_body/finish/add/link/typed/bind/params/operands/under 157–318, `expr` 323–337, `pdg_of` 673–680; schema [facts.rs](../../rstyle/crates/rstyle-core/src/facts.rs#L231) 231–309. **Status:** implemented/partial PDG semantic model; production opt-in RSTYLE_PDG presence (patterns/ignore). Inputs: HIR/typeck/root; outputs: indexed nodes, directed Data/Ctrl edges with usize arg_pos. Dependencies: records 10,12–17.

```text
nodes=[],edges=[],binds=HashMap<HirId,node>,ctrl=[]
emit Param for EACH body parameter including self, shape pat type, bind every pattern binding to node
lower body.value
if typeck body.value is not unit: append blank Return (ty=None,line body start), Data(value,ret,0)
add(node): index=nodes.len; append; if ctrl.last=(owner,pos), append Ctrl(owner,index,pos)
link(Some(from),to,pos): append Data(from,to,pos); None -> no edge
operands(parent,kids,start): lower kids in HIR order; link result -> parent at start+offset
under(owner,pos): push ctrl, lower once, pop; no bind snapshot
expression recovery order: recognizable for-desugar -> Iterate; recognizable try-desugar ->Try;
  outer macro expansion ->Macro; otherwise expression-kind lowering
finish: sort edges (from,to,kind,arg_pos); dedup exact edges; node order retained
```

**Limitations:** only innermost control edge emitted, no execution-order edges, memory/alias/store dependencies, phi nodes or loop-carried fixpoint. IDs allocated parent-before-operands except transparent cases; apparent graph topology need not reflect execution. No caps/recursion guard. `NodeKind::Ctor`/Case are normalization-only and never emitted by driver. **Cost:** O(HIR + E log E) graph storage O(V+E+bindings+control depth), except recovery scans/macros; compiler types external. **Tests:** CLI `pdg_is_only_recorded_for_patterns_and_modes_do_not_clobber` only asserts Iterate/Call and >=4 nodes; `patterns_for_loops_and_for_each_form_one_trait_candidate` asserts integrated coverage. Core handbuilt PDG tests do NOT validate extraction. **Fixture:** two independent calls swapped -> no ordering edge; empty unit fn -> params only; nonunit body -> synthetic Return. Compare exact emitted node/edge lists, not just candidate counts.

## 12. `extraction.pdg-bindings.rust`

**Purpose/output:** local value references, let transparency, generic assignment/operator nodes. **Source:** [pdg.rs](../../rstyle/crates/rstyle-driver/src/pdg.rs#L370), `path`/`literal` 370–401, `block`/`local`/`let_expr` 533–581, `generic` 649–669; `children` 28–45; `bind` 288–292. **Activation/status:** semantic production, partial reaching-definition modeling. Inputs: binding map, HIR expressions; outputs node reference or None, Op/Let/Lit nodes. Parameters: snippets clip 32 chars, string literals 24 (limit−3 + `...` when exceeded; Unicode scalar boundaries).

```text
local path -> binds[id] or None (NO new use node)
fn item path -> Lit(lit_kind='fn',callee ID/signature,type)
other path -> Lit('path', detail=snippet except expansion='')
literal kind -> str/int/float/bool/char/other
literal detail: expansion=''; Str debug-quoted clip24, Int decimal, Bool text, Char debug; others=''
block: iterate stmts; Let->local, Expr/Semi->expr discarded result, Item ignored; return only tail result
local let: lower init; simple Binding with no subpattern and Some(init) -> bind directly to init
  otherwise emit typed Let, Data(init,let,0), bind ALL pattern names to same Let
  let-else: lower else block afterwards, without added condition/snapshot
let expression: emit typed Let first; lower init, link pos0; bind pattern to Let
operator generic: Binary->op token; Unary->token; AssignOp->token+'='; Assign->'='
  Index->'index'; Struct->'struct'; Tup->'tuple'; Array/Repeat->'array'; Cast->Cast(''); else Op('expr')
  emit parent; lower direct expression children in rustc walk order (nested bodies excluded), link numbered operands
  assignment NEVER updates binds[target]; no distinction of LHS write from ordinary operand
```

**Limitations:** `let mut x=0; x=1; use(x)` still links use to original 0 node, not '='; destructured names share one node, no projection extraction. Scope exit does not restore map, although compiler HirIds distinguish usual bindings. Unary deref/address-of/DropTemps are transparent, casts remain. Record 9 sees writes independently; a mutation fact is not a PDG reaching-write edge. **Cost:** O(HIR/literal/snippet bytes); bindings O(number of unique HirIds). **Tests:** CLI literal/macro tests cover values only; no inspected driver assertion for assignment reaching definitions, let-else or destructuring edges. Core clip tests `{short_text_is_unchanged,long_text_keeps_limit_minus_three_and_dots,cuts_on_char_boundaries}`. **Fixture:** compare `let x=1; consume(x)` with `let mut x=0; x=1; consume(x)`; expected original-node versus '=' reaching-use difference at extraction, not proven-equivalent graphs.

## 13. `extraction.pdg-control.rust`

**Purpose/output:** branch/match control ownership and explicit/implicit return nodes. **Source:** [pdg.rs](../../rstyle/crates/rstyle-driver/src/pdg.rs#L584), `branch`/`matcher` 584–622, `returned` 638–647, `expr_kind` 340–368, `lower_body` 203–215. **Status:** production semantic, partial control/value model. Inputs: HIR conditions, arm patterns/guards, bind/control map; outputs Branch/Match/Return nodes, no merge. Parameters: if arm 0/1; match ordinal; data condition/scrutinee pos0.

```text
if: add Branch; lower cond under current OUTER ctrl; Data(cond,branch,0)
  lower then under (branch,0); else if present under (branch,1); discard branch results; return Branch node
match: add Match; lower scrutinee, Data(scrutinee,match,0)
  each arm in order: bind ALL arm pattern names to Match; under(match,ordinal): lower guard then body
  discard arm results; return Match node
Ret: add typed Return; lower optional value; Data(value,return,0); return None
Break: lower optional value and return its node, NO jump node; Continue: None
nonunit function still gets synthetic Return after whole body regardless of early-return paths
```

**Limitations:** no result-value Data edges from branch/arm to Branch/Match; matching destructuring binds to entire Match, not scrutinee component. No independent-arm binding snapshots, reachability or early-return control termination; statements after return still lowered. Nested condition nodes get outer rather than branch control. **Cost:** single traversal O(HIR+edges). **Tests:** CLI `patterns_enum_dispatch_is_a_candidate` exercises match-arm calls, not merge correctness. **Fixture:** `let x=if c {f()} else {g()}; h(x)` links Branch->h, not f/g->Branch. Negative no else has only arm0; boundary guarded match and statements after return. Propose exact edge comparison with a reaching-value PDG, whose implementation is outside this slice.

## 14. `extraction.pdg-loops.rust`

**Purpose/output:** recover for and Iterator::for_each into Iterate; retain while/loop as Loop. **Source:** [pdg.rs](../../rstyle/crates/rstyle-driver/src/pdg.rs#L74), `peeled`/`last_expr`/`for_parts` 74–119, `is_for_each`/`for_each`/`iterate` 470–519, `looping` 624–636. **Status:** production semantic; language-specific normalization at extraction, always on. Inputs: HIR desugaring/layout, closure body; outputs Iterate/Loop graph. Parameters: transparent external iter/iter_mut/into_iter handled in record 15.

```text
for_parts peels DropTemps/empty single-tail blocks
require Match(_,single outer arm,ForLoopDesugar)
require scrutinee Call(_,single head), peeled outer.body Loop(block)
require peeled(last tail OR final Expr/Semi statement) Match(_,arms,_)
choose arms[1]; require TupleStruct(single pat) OR Struct(single field pat)
on success: emit Iterate with pat type; head data->Iterate pos0; bind pat to Iterate
  lower body under(Iterate,0); return Iterate, discard body result
for_each: resolved def_path_str ends_with 'Iterator::for_each', exactly one arg direct Closure
  body=hir_body(closure); first param optional; Iterate.ty = item pat shape or None
  lower receiver head; link pos0; bind item if any; lower closure body under Iterate0
Loop: detail=lowercase Debug(LoopSource); emit Loop, lower block once under Loop0; return Loop
```

**Limitations:** compiler-desugar layout brittle; failed for recovery falls through generic HIR control model. No loop-carried data, fixed-point or explicit condition-to-Loop data; while lowered via compiler body/if structure. for_each uses enclosing builder/typeck and closure bindings, not a fresh closure graph. for_each identification is a suffix test, not trait DefId equality. **Cost:** O(HIR) plus constant-shape recovery checks; no iterative dataflow. **Tests:** CLI `patterns_for_loops_and_for_each_form_one_trait_candidate` asserts three sites, coverage1000; `pdg_is_only_recorded_for_patterns_and_modes_do_not_clobber` Iterate presence. **Fixture:** animals emit_cats versus emit_cats_each is existing positive; external zero-arg iterator call erased; similarly named workspace iteration method is not erased. Manual while counter versus for range in spelling S1 highlights first extraction control-shape difference; evaluation labels are not executed evidence.

## 15. `extraction.pdg-calls.rust`

**Purpose/output:** call/value/receiver dependencies, constructors and external collection-view erasure. **Source:** [pdg.rs](../../rstyle/crates/rstyle-driver/src/pdg.rs#L403), `call_node`/`call`/`method` 403–468, TRANSPARENT 26, `path` 370–392. **Status:** production semantic, implemented. Inputs: resolved FnDef/dependent DefId plus operand expressions; outputs Call or Op('ctor') nodes. Dependencies: signature record 10, identity5, loop14.

```text
direct call target = callee expression type FnDef(id), else None
if target DefKind::Ctor: Op('ctor',type) with NO callee id/signature
else Call(type, optional target ID and optional raw callee_sig)
emit parent before operands
if target None: lower callee expression, Data(callee,parent,0)
for actual args indexed from 0: lower and Data(arg,parent,index)
method: id=type_dependent_def_id or None, name=item_name or ''
if id outside workspace AND args empty AND name in ['iter','iter_mut','into_iter']:
  return lower(receiver) (call erased)
else for_each guard -> record14; else emit Call; receiver pos0, args positions1..
```

**Limitations:** indirect callee and first argument both use data pos0 (collision/ambiguity); direct Type::method includes receiver among args, unlike call-graph provenance. External named `iter` on arbitrary type is erased without proving collection-view semantics. PDG has no dynamic flag; typechecking and signature cannot prove target uniqueness. Constructor CallEvent was discarded separately by effect extractor; PDG retains Op ctor. **Cost:** O(number operands + recursive lowering). **Tests:** CLI loop/for_each, enum dispatch and signature families; no exact indirect-port or external-name-erasure assertion found. **Fixture:** fn pointer with one arg -> callee and arg share pos0; zero args has callee only; workspace `iter` versus external `iter` should differ. Boundary callee signature unavailable -> later call-class ID or '?' fallback.

## 16. `extraction.pdg-macros.rust`

**Purpose/output:** macro opacity, written argument recovery and try-expression recovery. **Source:** [pdg.rs](../../rstyle/crates/rstyle-driver/src/pdg.rs#L47), `UserArgs`/`macro_name` 47–72, `try_operand` 121–130, `expr` 323–337, `macro_call` 521–531, `literal_detail` 144–155. **Status:** production semantic; implemented/partial expansion model. Inputs: expansion context/spans; outputs Macro(name,type) with written-operand Data edges; Try node. Parameters: recovery precedes macro interception (for first, try second).

```text
try_operand: exact ExprKind::Match(TryDesugar), scrutinee Call(_,single operand)
if recovered: emit Try; lower operand; Data(pos0); DO NOT lower expansion's success/error branches
macro_name: expr.span.from_expansion AND outer_expn.kind Macro -> expansion name
macro_call: emit Macro(name); intravisit walk children using UserArgs
UserArgs.visit_expr: if expansion span, recurse walk_expr; else append expression and STOP descending it
lower collected maximal user-spanned expressions in visitor order; Data positions0..
expanded literal/path detail=''; written literals retain record12 details
```

**Limitations:** generated implementation calls/branches omitted from PDG while effects walker still traverses expansion; graph and effect views intentionally diverge. Source-span recovery may omit or duplicate semantic inputs depending on expansion; macro bodies/side effects are not summarized. '?' is opaque propagation, no explicit error/return relation. **Cost:** macro subtree scan plus lowering recovered inputs; potentially repeated scans with nested macros, no cap. **Tests:** CLI `patterns_macro_literals_never_show_partial_tokens` asserts no garbled format!/L0 hole; `patterns_literal_holes_show_whole_values` asserts alpha|beta. **Fixture:** `format!("alpha {}", f())` versus beta under macro may not expose format-string literal hole; plain string literals do. spelling S7 `?` versus explicit match/early return first differs at Try recovery; equality remains unresolved.

## 17. `extraction.pdg-closures.rust`

**Purpose/output:** isolate opaque closure values except known for_each lowering. **Source:** [pdg.rs](../../rstyle/crates/rstyle-driver/src/pdg.rs#L340), `expr_kind` 340–368, `Kids` 28–45, `for_each` 478–499; effects `on_call` 165–177 and OnlyBodies visitor 231–296. **Status:** partial/production semantic. Inputs: closure HIR, nested-body visitation policy; outputs one typed Closure node, no nested closure PDG/capture edges. Dependencies:14,8.

```text
ordinary closure expression -> add Closure(ty,line); do NOT descend body
direct call to closure-typed expression -> PDG ordinary unresolved Call, lower callee (Closure node)
HIR effects walk does not emit a CallEvent for Closure/CoroutineClosure call itself
for_each direct closure argument exception -> lower actual body as Iterate under record14
```

**Limitations:** closures in map/filter/fold can hide algorithm bodies from mining while effects/uses can still see nested HIR bodies. No capture/use/return dependency model or closure target resolution. Compiler nested-body traversal internals unresolved. **Cost:** PDG O(1) per opaque closure plus callee use; exception proportional to body. **Tests:** CLI graph total's dyn edge in map is asserted by `facts_record_call_graph_ids_and_mutated_types`; clean describe/filter fixture; for_each integration test. No extraction assertion of captures/ordinary closure PDG. **Fixture:** `xs.map(|x| dangerous(x))` versus for_each direct closure: compare effects/workspace edges with PDG node set. Positive for_each visible, negative map opaque, boundary indirect closure variable called as fn pointer changes call facts.

## 18. `facts.json-merge.rust-frontend`

**Purpose/output:** deserialize cached facts and remove exact physical/display duplicates, without field enrichment. **Source:** [collect.rs](../../rstyle/crates/cargo-rstyle/src/collect.rs#L29), `read_facts` 29–48; [facts.rs](../../rstyle/crates/rstyle-core/src/facts.rs#L311), FnFacts 311–355, key/merge357–369; schema field defaults 35–182/270–309; producer callback driver84–91. **Status:** implemented/default; inputs JSON vectors; outputs concatenated vector then stable-sorted first record per physical key. Dependencies: serde1.0.229/serde_json1.0.151, extraction4, selection2.

```text
read_dir errors -> fail; individual bad directory entries/non-UTF8 filenames -> silently skip
filter accepted names; sort names lexicographically
read/deserialize each accepted file into Vec<FnFacts>; any read/JSON failure -> error; concatenate
serde required FnFacts: path,line,column,name,params,has_self,statements,source,
  preceding_line,mutations,calls,effects
defaults: id='', implements=None,param_list=[],top_statements=0,edges=[],mutated_types=[],sig=None,pdg=None
nested defaults: mutation.delegated=false; call/edge.dynamic=false; edge.args=[]; param.uses=0;
  optional/sparse PDG node evidence None/' '/0 as actual schema (detail='',line=0); edge.arg_pos=0
merge: STABLE sort by (path,line,column,name); dedup equal key; first input record wins
```

**Limitations:** no schema version, denied-unknown-fields or graph-index validation on facts. Unknown extra fields are not frontend validation errors. Equal raw ID at distinct physical/name keys survives; equal physical keys with conflicting richer PDG/effects do not combine. Default IDs can collapse saved-facts maps but not physical merge. Missing pdg excludes candidates, missing sig excludes method signature evidence, missing top count skips spacing. **Cost:** O(JSON bytes + F log F), memory O(all facts). **Tests:** collect two unit tests; core `facts::tests::{merge_sorts_and_dedupes,old_facts_without_sig_still_parse,pdg_is_optional_and_round_trips}`; patterns `duplicate_target_facts_do_not_duplicate_sites`. **Fixture:** two records same key with None vs Some(PDG): reverse input order changes retained evidence; two same-ID keys survive production but first-ID examples drop one. No assertion proves all-target cfg conflict resolution correct.

## 19. `filtering.mining-preparation.rust-frontend`

**Purpose/output:** remove abstained/generated functions and resolve trait call labels before evaluation oracle hides links. **Source:** [prep.rs](../../rstyle/crates/rstyle-core/src/prep.rs#L7), `hide_implements` 7–21, `impls`/`peel`/`receiver_adt`/`devirtualized` 23–75, `generated`/`prepare` 77–102; patterns_report `mine_all`69–77. **Status:** implemented/default patterns/ignore, hide oracle opt-in. Inputs: merged facts; outputs cloned facts preserving order, rewritten PDGs. Parameters: hide pattern substring, '*' wildcard; comment abstraction gate.

```text
active = facts excluding valid allow(abstraction) and IDs with segment '_' OR starts '_#'
table[(implements trait method,self_ty ADT id)] = fn for active methods with both fields;
  BTreeMap collect -> last duplicate wins (concrete self_args NOT part of key)
for each Call node:
  first Data edge to call with arg_pos0 -> operand node.ty
  peel Ref recursively; require Adt(id); lookup table[(callee_id,id)]
  if found replace callee_id and callee_sig; retain all other node/edge fields
then hide_implements: if Some link matches '*' or contains any supplied pattern, set None
(no rewriting of FnFacts.edges, and PDG devirtualization already happened)
```

**Limitations:** suppressing an impl removes it from devirtualization table. Generic ADT instantiations can collide because self_args erased from key. Indirect pos0 ambiguity from record15 can select wrong receiver evidence. dyn/type-param/no typed receiver retains trait target. Anonymous-const generated filter is mining-only, including handwritten functions under anonymous const. **Cost:** table O(F log F); each Call scans edges O(C×E); cloning O(fact/graph bytes). **Tests:** exact `prep::tests::{trait_calls_resolve_to_the_receiver_impl,functions_inside_anonymous_const_are_dropped,disambiguated_anonymous_consts_are_dropped_too,anonymous_const_filter_only_matches_whole_segments,allow_comment_removes_function,hide_drops_matching_trait_links_only}`; CLI `patterns_hide_implements_recovers_the_trait_as_a_candidate`. **Fixture:** two impls for `Wrapper<u8>`/`Wrapper<u16>` same trait method -> table last owner, despite distinct locators; hide-before versus after prepare gives distinct call labels. Source enforces after, not a configurable order.

## 20. `filtering.style-comments.rust-frontend`

**Purpose/output:** named style suppression/invalid diagnostics and abstraction/effect-boundary predicates. **Source:** [suppress.rs](../../rstyle/crates/rstyle-core/src/suppress.rs#L3), RULE_IDS/parse/allows3–44; lib `function_diagnostics`70–78; source selection record6. **Status:** implemented/default style, selective mining gates. Inputs: one preceding line, rule IDs; outputs None/Allow/Invalid. Parameters allowed IDs: fn_length, fn_params, fn_spacing, mutation_per_target, mutated_targets, side_effect_density, abstraction.

```text
trim line; require EXACT prefix '// rstyle-allow(' else None
split first ')', else Invalid malformed
reason = trim(tail.strip_prefix(':') or ''); empty ->Invalid
names = comma split, trim (empty and unknown names invalid; duplicates allowed)
if any name not in whitelist ->Invalid, else Allow(names)
style: compute all diagnostics first; Allow drops only named rule IDs; Invalid adds invalid_suppression
mining: valid abstraction drops whole function before evidence production
graph boundary: valid side_effect_density prevents exporting effects to callers
```

**Limitations:** whitespace between ')' and ':' makes missing reason; nearest blank prevents detection; no body-scoped suppression. Invalid abstraction comment is not reported by patterns (style reports Invalid). Suppression changes transitive effects as well as visibility. **Cost:** O(comment bytes+names). **Tests:** CLI `suppressions_apply_only_with_a_reason`, `effects_propagate_through_calls_and_stop_at_boundaries`; exact suppress tests in coverage. **Fixture:** same fn with valid reason, no reason, or `) : reason`; boundary callee with density allow can reduce caller report, so suppression is not pure rendering. Cross-mode invalid abstraction behavior differs at validation/reporting step.

## 21. `pipeline.style.rust-frontend`

**Purpose/output:** semantic style config, diagnostic and suggestion pipeline. **Source:** [cargo main.rs](../../rstyle/crates/cargo-rstyle/src/main.rs#L141), `load_config`141–151/`analyze`186–190; [lib.rs](../../rstyle/crates/rstyle-core/src/lib.rs#L37), exclusions37–44, rule/function diagnostics46–78, summarize88–120, evaluate122–145; [rules.rs](../../rstyle/crates/rstyle-core/src/rules.rs#L29)29–219; [config.rs](../../rstyle/crates/rstyle-core/src/config.rs#L20) defaults20–165 and classify221–237. **Status:** implemented/default; graph propagation/fix-group algorithms delegated to core, only boundary traced here. Inputs: PDG-free facts, TOML config; outputs diagnostics, summary, fix_groups/plans, no edits.

```text
facts=gather(style,false); config explicit file else root/rstyle.toml if exists else defaults
TOML defaults omitted keys/tables; unknown config keys rejected
merge -> glob path exclusions -> core graph.build -> direct effects -> core propagate(depth)
for every fn run length,params,spacing,mutation_budget,side_effect_density, then record20
sort diagnostics; summary all retained functions/effects (even suppressed diagnostics)
mean density = sum density / max(F,1); max or0; effect counts by kind
core groups.build(facts,graph,diagnostics,config); return Report
producer-consumer details:
  mutation budget groups ALL events (incl delegated), root or root.field; >3 writes or >3 targets defaults
  effects: only escapes mutations, unique(root,field), first line; classified calls; intrinsic events
  classification longest configured path prefix; equal-length ties follow last max iterator item
  no matching nondynamic call -> no effect; matching dynamic call -> known class, else Unknown
  density = 1000*sum(weights)/max(statements,1), integer floor
  small if statements<3 OR code_lines<10; default density flag actual>500
  fn_length actual>50; params >4 (self not counted unless enabled)
  spacing: top>=5 and no blank ANYWHERE, zero threshold disables
```

**Parameters:** weights mutation1/io3/network3/global2/unsafe4/time1/random1/panic0/unknown1; depth3; excludes target/**; grouping caller_rules=[fn_params], caller_hops1. Prefix tables source defaults183–218: IO filesystem/io/env setters/path queries/process launch, network std net/reqwest/tokio/hyper, time now, random rand, panic core/std panicking. **Limitations:** graph drops unresolved edges/self-recursion and ignores dynamic in target lookup (graph52–82); delegated propagation keyed by source line (graph159–168). Core transitive and plan internals remain outside full review. No completeness/unknown-call budget: unclassified nondynamic external calls look effect-free. Arithmetic not saturated. **Cost:** merge/path/rule scans + delegated core costs unknown. **Tests:** CLI style/effects/config/fix families (coverage T01–T19); core rules tests source inspected, none executed. **Fixture:** known IO report versus unclassified custom external mutator; config edit without compiler changes; invalid excludes ->error. Diagnostics suppression does not remove summary effect count. Fix suggestions are not proof of safe extraction.

## 22. `pipeline.patterns.rust-frontend`

**Purpose/output:** activate mining and apply result filters in exact order. **Source:** [cargo main.rs](../../rstyle/crates/cargo-rstyle/src/main.rs#L192), `cluster_params`192–202, `mine_options`204–210, `patterns`216–239; [patterns_report.rs](../../rstyle/crates/rstyle-core/src/patterns_report.rs#L52), build52–66, mine_all69–82, run98–121; candidate sort/identify/mine758–835. **Status:** implemented/opt-in production; normalize/pair-coverage/single-call-guard/max-hole experimental overrides. Inputs: semantic facts/options/ledger; outputs independent ranked signature_groups/candidates, unfiltered suppressed and ignored lists.

```text
facts = gather(semantic,true)  // NO load_config call, no style exclude paths
ledger = None if --no-ignore else load(explicit or root/rstyle-ignore.toml)
min_score_milli = round(max(min_score,0.0)*1000.0) as u32 (Rust saturating float cast)
merged facts -> record19 -> signature mine -> candidates.mine(params)
candidates.mine: only pdg-bearing fns sorted(path,line,id); cluster plus per-PDG dispatch outcomes
  collect outcomes; score-desc/site-asc sort, suppressed sort(site,reason); identify record23/24/25
apply ledger to ALL mined candidates before display filters
kept candidates retain score>=min_score_milli, take top or usize::MAX
signature groups independently retain >=same threshold, take same top
suppressed unchanged; ignored=all ledger-hidden candidates (not filtered), ignored_count=len
exit gate after filters as record1; min_score/top are NOT mining thresholds
```

**Limitations:** style excludes/config thresholds unused; show_ignored text-only. `--no-ignore` bypasses ledger load entirely, including malformed-file errors, but not abstraction comments/existing-abstraction suppression. All candidates API ignores ledger/min-score/top but still honors extraction/prep/mining flags and candidate guards. No changed-function filter or frontend dedup of equal candidate IDs; fact merge is the duplicate-target defense. **Cost:** downstream mining unresolved, result filtering O(groups+candidates), ledger matching record25. **Tests:** `patterns_report::tests::{min_score_and_top_filter,duplicate_target_facts_do_not_duplicate_sites,candidates_carry_a_stable_id_and_site_shapes,ledger_hides_a_dismissed_candidate_and_says_why,ledger_hides_before_min_score_and_top,all_candidates_ignores_the_ledger_and_display_filters}`, CLI patterns/ignore families. **Fixture:** with bad style config, style errors while patterns need not; top0 empties groups/candidates but preserves suppressed/ignored. With no_ignore, comment/existing trait suppression remains. Tests for ledger-before-top encode only a one-candidate pool, not replacement by next kept candidate.

## 23. `facts.locator.rust-frontend`

**Purpose/output:** stable reviewed-function names independent of ordinary impl block ordinals. **Source:** [locator.rs](../../rstyle/crates/rstyle-core/src/locator.rs#L14), `trait_of`/`signature_text`/`base`14–45, `assign`/`numbered`47–68; facts `TyShape::render`184–209/`SigFacts::owner`212–229; candidate identified758–792. **Status:** default mining/ledger, implemented with order-dependent fallback. Inputs: prepared facts id/sig/implements/path/line; output BTreeMap<id,locator>. Parameters: impl prefix '{impl#', duplicate suffix '#2' onward.

```text
owner = self_ty plus rendered self_args except direct Param variants
render: full ADT IDs/generic type args; &mut/&; tuple '(joined)' (no singleton comma), slice/array '[T; _]';
  Param='Tindex'; Dyn='dyn id'; FnPtr='fn'; Opaque AND Other='_'
base: find FIRST id segment starts '{impl#'; require owner and sig else original id
suffix=all segments after that impl segment joined '::'
inherent -> owner+'::'+suffix
trait impl -> '<owner as trait-method-id without last ::segment>::'+suffix+'(params) -> ret'
assign: sort facts(path,line,id), keep first unique raw id
count occurrences of base; first base unchanged; later base#2,#3,...; collect by raw id
```

**Limitations:** signature disambiguation loses erased shape evidence; same owner/method may still collide (trait argument absent from signature). Non-ADT/old facts fall back to ordinal ID. Inherent locator omits parameter/return signature. hide_implements oracle changes trait locator to inherent form, changing candidate ID; production and oracle ledgers differ. **Cost:** O(F log F + rendered type bytes), memory O(F). **Tests:** all seven locator tests, exact symbols in coverage; CLI output stability assertions are limited fixture evidence. **Fixture:** insert unrelated impl (locator unchanged), swap indistinguishable trait impl source order (fallback #2 assignment changes), alter inherent return type (locator same). Raw compiler ID and locator are separate identities, never interchangeable with physical merge key.

## 24. `facts.shape-fingerprint.rust-frontend`

**Purpose/output:** deterministic PDG site fingerprint and candidate ID inputs, not semantic body equivalence. **Source:** [wl.rs](../../rstyle/crates/rstyle-core/src/wl.rs#L12), constants/hash/mix/label/adjacency/refine/histogram12–138, Wl::new184–202, shape_hash223–230; candidates::site160–172. **Status:** implemented/default candidate sites and ledger status. Inputs: **prepared, devirtualized PDG**, no canonicalization in `site`; outputs 16-hex `u64` shape. Dependencies: normalization of callee signature/type classes is core boundary; hashing/refinement reviewed here solely for identity.

```text
FNV offset=0xcbf29ce484222325; prime=0x100000001b3
fnv(bytes): h=(h XOR byte).wrapping_mul(prime)
combine(a,b): FNV over a.to_le_bytes then b.to_le_bytes from OFFSET
label strings:
 Call='call:'+normalize(sig).key else id else '?'
 Macro='macro:'+macro_name or ''; Lit='lit:'+lit_kind or ''
 Op='op:'+detail.split(':').first; Param='param:'+core class_of(ty) or ''
 other kinds=Debug(kind)
initial colors=FNV UTF8 labels; build in/out adjacency, skip endpoints>=nodes.len
edge tag=combine(bool(kind==Ctrl) as u64,arg_pos as u64)
3 refinements ALWAYS (4 levels incl initial; identity does NOT use diameter-capped levels)
refine each node: sorted multiset combine(edge_tag,prev_neighbor_color)
  fold incoming from combine(own,0x1f); fold outgoing from combine(incoming_result,0x2e)
sorted BTreeMap color->usize count at deepest level
hash=fold OFFSET over (color,count): combine(combine(acc,color),count as u64)
shape text=format 016x
```

**Limitations:** field names, literal values and call IDs with available signatures do not enter labels; type/callee differences can be deliberate holes yet keep shape. Op detail **does** affect labels before ':', despite general comments about names/detail. Hash collision has no secondary equality check; duplicate edges from saved facts affect multiset even though driver dedups. `Wl::new` also computes diameter (<=400 exact BFS, larger returns4), unnecessary for shape selection but incurred. normalize/class_of internals not fully audited here; this is not a paper WL contract. **Cost:** 3 adjacency sorts/histograms plus diameter O(V(V+E) log V) conservative bound at V<=400, large graphs no exact diameter; O(V+E) storage per constant levels. **Tests:** `wl::tests::{shape_hash_ignores_names_and_node_order,shape_hash_changes_with_structure,shape_hash_is_pinned}` (pinned f440c2186883aa43). **Fixture:** edit same-kind literal or field spelling without structure -> fingerprint can remain same; add edge/call -> can change. Strict reviewed ledger therefore does NOT resurface on every source/body edit.

## 25. `filtering.ledger.rust-frontend`

**Purpose/output:** stable candidate ID, exact/growth suppression and versioned ledger schema. **Source:** [ledger/mod.rs](../../rstyle/crates/rstyle-core/src/ledger/mod.rs#L15), version/schema/check15–72, parse118–138, render175–187, site_key194–196/joined198–202/candidate_id206–212; [matching.rs](../../rstyle/crates/rstyle-core/src/ledger/matching.rs#L48), member sets48–54, matches58–76/hiding_entry79–85/apply88–108, entry_for110–135/add138–147/prune151–163. **Status:** default patterns unless no_ignore; implemented opt-in persisted review. Inputs: CandidateKind/sites/definitions; outputs 12 lowercase hex ID, kept/hidden partition retaining input order. Dependencies:23,24, TOML parser.

```text
site_key=locator+'@'+(shape if Some else '-')
ID text=kind.name+'|'+sort(site_keys).join('\n')+'|'+sort(definition locators).join('\n')
ID=FIRST12 of 016x FNV1a(UTF8 text)  // high 48 bits; no dedup before ID hash
parse ledger: required version==1, unknown fields denied, duplicate tables parser error
require each ID len12 lowercase0-9a-f; growth entry requires nonempty sites
strict add: fns=sorted unique locators of sites+definitions, sites/definitions=[] (hints only)
growth add: fns=[], sites=sorted unique site_keys, definitions=sorted unique locators
replace same-ID entry preserving attached notes, overwrite options/reason
matches: require same kind; exact ID ->Exact WITHOUT inspecting hints/member sets
else require allow_growth and stored site set subset current site set AND stored defs subset current defs
added=saturating_sub(current site+def set sizes,stored sizes); zero->Exact else Growth(added)
choose matching entry with smallest added; BTreeMap ID order breaks ties first
apply: partition candidates hidden/kept without reranking/dedup
prune: keep entry iff ANY current unfiltered candidate matches
```

**Limitations:** no collision resolution/content equality; candidate text delimiter encoding unescaped. Definition bodies never enter candidate ID (locator only). Shape changes limited by record24; source-semantic edits can remain hidden. Empty shapes use '-' distinct from absent fn mapping. Growth checks membership/shape, not score or inference text. File format enforces nonempty stored sites, not correctness of manually written site keys. **Cost:** ID sorting O(S log S+D log D), application roughly O(candidates×ledger×set construction), prune same product. **Tests:** ledger ID/schema/matching exact symbols in coverage (23 tests across mod/matching); CLI `ignore_hides_a_candidate_and_patterns_says_so`, growth management and output stability. **Fixture:** strict exact body-literal edit can stay hidden; growth add member stays hidden; lose/reshape member resurfaces when shape actually changes. Changing definition body alone keeps ID. No-ignore bypass does not undo earlier trait suppression.

## 26. `pipeline.ignore.rust-frontend`

**Purpose/output:** resolve/dismiss, report current locations/state and prune reviews against full candidate pool. **Source:** [cargo main.rs](../../rstyle/crates/cargo-rstyle/src/main.rs#L259), session259–271, status/prune/dismiss273–294, ignore_cmd296–309; [ignore.rs](../../rstyle/crates/cargo-rstyle/src/ignore.rs#L12), ledger_path/load/save12–30, resolve33–55, dismiss58–78, prune81–105; [status.rs](../../rstyle/crates/rstyle-core/src/ledger/status.rs#L46), current46–61/recorded64–76/member78–94/new_members105–115/entry_status117–141/status144–152. **Status:** production opt-in; writes ledger only, not source. Inputs semantic gathering/root/ledger/mining flags/ID prefix; outputs text and optional disk update; no analysis/display filtering before management.

```text
gather semantic true; load ledger (missing file ->empty; bad file ->error)
all_candidates(facts,mine_options): ignores ledger/score/top, not prep/mining guards
status first in match dispatch: optional prefix filter starts_with (no min4 rule here)
  assign locators over RAW gathered facts; current locator->last fn location/shape
  stored sites split at last '@' if shape!='-'; else treat whole site string as unshaped locator
  include strict fns and defs as no-shape hints
  absent locator ->Gone; present and recorded shape differs from Some(current) ->ShapeChanged
  recorded shape but current shape None ->Unchanged; no recorded shape ->Found
  active=any matches(record25)
  stale new_members = locators of candidate with largest overlap known, minus known;
    ties max_by_key choose LAST candidate, kind not constrained
prune: compare full candidates; dry_run returns original ledger plus report; otherwise save kept
resolve dismissal: prefix byte len>=4; starts_with comparison case-sensitive, no hex validation
  zero/many ->error; one -> add record25, save
save=direct std::fs::write(render), no atomic temp file/parent mkdir
```

**Limitations:** status hashes **raw** gathered PDGs, whereas candidate sites hash **prepared** PDGs, so devirtualized trait-call shapes can show mismatch even unchanged source. `locator@-` parsing retains '@-' in locator and can show Gone (normally PDG-bearing candidates have shapes, but manually/sparse facts expose it). Strict fns are hints, not checks. Status stale heuristic not proof the body changed. Ledger rendering preserves contiguous comments above/inside entries, relocates to above header; unrelated comments lost. **Cost:** mining external + status per-function hashes plus candidate overlap scans; resolve O(pool×prefix). **Tests:** all five ignore unit tests, four status tests; CLI last six ignore/CI families. **Fixture:** devirtualizable caller dismissed with growth then status on unchanged facts; compare raw versus prepared shape. Prefix len3 error, unique len4 success, ambiguous len4 error; status prefix can be shorter. No filesystem writes executed in this audit.

## 27. `pipeline.saved-facts.rust-frontend`

**Purpose/output:** distinguish production from supporting direct saved-PDG consumers and absent fix/TUI/RPC paths. **Source:** core examples [norm_pairs.rs](../../rstyle/crates/rstyle-core/examples/norm_pairs.rs#L12)12–65, [norm_sim.rs](../../rstyle/crates/rstyle-core/examples/norm_sim.rs#L20)20–83, [norm_comparable.rs](../../rstyle/crates/rstyle-core/examples/norm_comparable.rs#L11)11–50, [align_ablation.rs](../../rstyle/crates/rstyle-core/examples/align_ablation.rs#L19)19–68, [wl_trace.rs](../../rstyle/crates/rstyle-core/examples/wl_trace.rs#L11)11–43. **Status:** implemented supporting executables, NOT production cargo-rstyle modes; absent automatic fix/TUI/RPC in frontend. Inputs: caller-ordered JSON files, stdin pairs, rule string; outputs numeric traces/measurements. Dependencies: core WL/align/canonicalize internals boundaries.

```text
load saved FnFacts directly, keep only PDG-bearing records; map by raw ID, first occurrence wins
NO physical merge, no comment/generated filter/devirtualization/hide oracle/config/ledger
norm_pairs/wl_trace: BTreeMap id ordering; suffix match must be exactly one (comments say substring,
  actual ends_with); ambiguous/missing ->error2
norm_pairs raw/canon measurement: ALWAYS align, even incomparable; output comparator bit separately
norm_sim: full-ID tab pairs; missing ->'NA'; incomparable ->coverage0, still WL score/nmax
norm_comparable: full-ID pairs; missing ->0; canonicalize rules, Wl, core comparable
align_ablation: every i<j after ID sort; core comparable gate; run SIX variants regardless WL threshold
wl_trace: Side::from_facts then trace threshold600 (Side/trace internals not inspected in this slice)
```

**Limitations:** direct saved-facts results can differ from production on identical files due to prep and dedup keys; score experiments do not themselves validate final candidate reachability. Transport/rendering alone excluded, but comparability gates and coverage0 versus unconditional alignment are semantic. Core group/stacking output is planning, no edits, rustfmt, borrow-check or extraction validation. **Cost:** file bytes/maps plus core algorithms; all-pairs O(F²) calls in ablation. **Tests:** no example-unit tests found in inspected files; Python scorers use these as dependencies, not executed. **Fixture:** same raw trait call facts through production versus norm_sim -> labels may differ; missing fn ID ->NA versus0; incomparable pair norm_pairs may show positive coverage while norm_sim reports0. Resumption: `norm_stats.rs` and `wl_trace::Side` internals explicitly unreviewed.

## 28. `support.loo.rstyle`

**Purpose/output:** leave-one-project-out threshold tuning, mixed labeled-pair recall/candidate-noise scoring. **Source:** [loo_eval.py](../../rstyle/scripts/loo_eval.py#L15), constants15–26, run_miner29–47, site/labels/score50–101, prf104–107, main110–177. **Status:** supporting opt-in Python; writes eval CSVs; not run. Inputs: labels.csv and current miner JSON, four examples + synthetic + three external clones. Parameters grid thresholds200..900 step100 × coverage[0,400,600,800], four threads, normalization optional.

```text
labels: skip no site_b and label IDs starting X; key unordered(site path,tail without ' (arm...')
  duplicate pair keep strongest no<maybe<yes; retain all label IDs
miner cache /tmp/rx_loo/project_thr_cov[_norm][_EXTRA]_int(binary mtime).json
  no source/driver/ledger/label digest; refresh bypass
run CLI patterns --all-targets with threshold/coverage, ambient ledger enabled
score flags = candidate.sites + signature_groups.get('sites',[]) (schema actually members ->usually [])
for EACH flagged item:
  hit labels iff BOTH path suffix AND raw ID suffix match
  if ANY positive/maybe hit: union positive pair TPs, do NOT count decoys in same item
  elif any hit: fp_decoy+=1 PER item, else fp_unlabeled+=1 PER item
fn = positive pair count - distinct TP pairs; maybe counts positive; yes tracked separately
P=tp/(tp+fp) or0; R=tp/(tp+fn) or0; F1=2PR/(P+R) or0
for held among4: maximize train F1 on other3; ties higher threshold then coverage
evaluate held once at chosen grid, compute separate held oracle maximizing same tie rule
synthetic excluded from LOO; real clone noise is candidate count, not labeled FPR
```

**Limitations:** units mix pair TPs/FNs with candidate FPs; ignored candidate ledger silently changes evaluation; signature group schema mismatch gives empty sites/no TP plus possible unlabeled count. Label CSV split column ignored: projects documented tune/holdout are all rotated in LOO. Cache binary whole-second mtime alone misses changed sources/driver/labels/ledger. **Cost:** 256 grid/project jobs; scoring O(items×labels×sites), miner unknown. **Tests:** no direct LOO tests found; dataset28 labels; `normalize_ablation` reuses helpers. **Fixture:** a candidate spanning both positive and decoy credits positive only; group with members but no sites is empty flag. Change ledger with same binary mtime and warm cache: cached scores unchanged. Historical CSV values are artifacts, not current observed results.

## 29. `support.alignment-ablation.rstyle`

**Purpose/output:** evaluate pair selectors/variant coverage, distinct from final candidate recall. **Source:** [align_ablation.py](../../rstyle/scripts/align_ablation.py#L17)17–78; [align_ablation.sh](../../rstyle/scripts/align_ablation.sh#L4)4–12; example record27. **Inputs:** comparable pair JSONL with six [coverage,holes] arrays, labels; outputs labeled/variants/selectors CSVs. **Status:** supporting; required pairs.jsonl/external caches not validated. Parameters variants baseline,labels_only,no_final_prune,complete_checked,coarse_to_fine,combined.

```text
strip project prefix from label sites, remove ' (arm...' tail; skip X/single-site labels
resolve by project and id ends_with('::tail'), orientation free; last matching pair for label ID wins
variant rows: pairs=len(all), count covariance !=baseline, round(mean coverage), >=600/>=800 counts
positives = resolved yes/maybe IDs ONLY; negatives resolved no IDs
selectors = WL>=800/600/500; for baseline/coarse_to_fine/combined ×600/700/800/900:
  coverage>=x; WL>=600 OR coverage>=x
count selected resolved positives/decoys, and selected all pairs per example/real project
shell: release build align_ablation; truncate JSONL; seven caches; append all comparable pairs;
  summarize Python (no threshold-based candidate extraction)
```

**Limitations:** unresolved positive labels excluded from denominator (optimistic relative to full labeled corpus); no path check, unlike LOO; duplicate label pairs independent IDs; zero pairs -> division by zero. Pair coverage variants aren't production flags automatically. **Cost:** source example O(F²×6 alignments), summary O(pairs×labels +selectors×pairs). **Tests:** none direct, files artifacts only. **Fixture:** one unmatched yes label disappears from pos_labeled; same suffix in two modules resolves last. Compare this denominator to LOO's all-positive pair denominator.

## 30. `support.canonicalizer-ablation.rstyle`

**Purpose/output:** candidate-level canonicalizer and alignment-selection experiments. **Source:** [normalize_ablation.py](../../rstyle/scripts/normalize_ablation.py#L17)17–83; [pair_cov_eval.py](../../rstyle/scripts/pair_cov_eval.py#L14)14–63. **Status:** supporting opt-in; outputs eval/normalize and eval/align CSVs. Inputs: LOO helpers/labels/config names; outputs TP/FN/FP totals, synthetic/real noise and hit label IDs. Parameters: 26 defined normalize configurations at base600/600; pair selector12 configs.

```text
normalize configs = none,all,all-minus-each7,each-only7, pc650/pc600, guards,
  h4/pc800/pc700 variants as literal CONFIGS17–32
chosen configs sequentially set L.NORM/L.EXTRA globals; each runs all4+synthetic+noise via L.run_miner
reuse L.score; sum TP/FN and candidate FP; flagged IDs from candidates ONLY using L.cand_hits
named partial run writes ablation_<FIRST name replace '+' with '_'>.csv
pair_cov configs=(threshold800,600,1001) ×(pcNone,700,650,600), min_coverage600
cache /tmp/rx_pc/project_thr_pc.json; refresh optional, NO binary stamp/config/source digest
run same all-target CLI; only nonempty stdout checked (return code NOT checked)
4 threads; sum score; noise candidate counts; write pair_cov.csv
```

**Limitations:** threshold1001 valid frontend and forces WL-only threshold failure, not an invalid CLI input. Pair-coverage adds selection but retains comparator/min-coverage/inference guards. Inherit ledger/schema/scoring caveats28. ThreadPool import in normalize script unused; configs must be sequential due globals. Partial CSV may contain several configs despite name. **Cost:** 26×8 miners or12×7 miners; downstream unknown. **Tests:** Python `EvalConfig.test_ablation_config_drops_one_rule_and_none_is_empty` pertains CodeNet parser, not these runs. **Fixture:** warm rx_pc cache after rebuilding miner -> old result can persist; normalization plus pc1001 still depends on comparable guard. No measurements rerun.

## 31. `support.codenet-sampling.rstyle`

**Purpose/output:** filter/deduplicate Rust submission corpus before sampling. **Source:** [codenet_sample.py](../../rstyle/scripts/codenet_sample.py#L41), keys/constants41–46/load49–78, strip/fingerprint/foreign/reject81–110/prepare113–130. **Status:** supporting, not production extraction. Inputs: rust_submissions.csv + training JSONL or code-dir; output kept rows/funnel. Parameters status='Accepted', min_lines15,max_lines250; defaults record32.

```text
metadata dict by submission_id (later duplicate row wins)
wanted status rows for code loading; JSONL code lookup tries row then nested metadata,
  ordered id keys submission_id/id and code/source/src/content/text; last code record wins
code-dir reads problem/Rust/sid.rs with UTF8 errors replace; missing absent
iterate sorted metadata IDs; first rejecting branch: wrong status, no code, reject_reason, duplicate hash
reject_reason: physical newline count+1 <15/>250, literal '#![feature', foreign crate, no fn regex
strip_comments regex non-nested '/\*.*?\*/' DOTALL then '//[^\n]*'; no string awareness
fingerprint SHA1 whitespace-collapsed stripped source; dedup ACROSS all problems/users
foreign crate roots from anchored use/extern crate, allow std/core/alloc/crate/self/super and
  regex local mod/enum/struct declarations; this is not Rust name resolution
```

**Limitations:** tokens inside string/comments can affect regex filtering, imports in groups/aliases/multiline forms not fully parsed; SHA1 collision no secondary compare. Whole-source dedup erases identical solutions before clone scoring. “Accepted” is dataset status, not compilation or refactoring suitability proof. **Cost:** O(code bytes +N log N metadata), stores wanted code text. **Tests:** `Sampler.test_funnel_counts_each_filter` asserts ten rows with wrong-status/foreign/tiny/duplicate/compile-fail counts; no nested-comment/raw-string regression. **Fixture:** same source whitespace variants across different problems -> one kept; string containing '//' changes fingerprint. Different external fully qualified path without use can pass regex then fail compile.

## 32. `support.codenet-sharding.rstyle`

**Purpose/output:** deterministic split/sampling and bounded-corpus sharding. **Source:** [codenet_sample.py](../../rstyle/scripts/codenet_sample.py#L133), clusters133–151/rank154–156/split159–164/pick167–175/count178–179/units182–191/targets194–201/plan204–230/parser340–361. **Status:** supporting. Inputs: filtered submissions, identical-problem cluster pairs, seed/params; outputs split/submission shard plan, target and eligible counts. Dependencies31,40.

```text
load optional cluster file: lines with EXACTLY2 p\d+ matches; union-find path halving,
  union larger root into lexical smaller root; missing problems self cluster
rank(seed,key)=SHA1(UTF8 decimal seed+':'+key), sort hexdigest
split = integer digest(split_seed,root)%1000;
  <holdout_frac*1000 ->holdout; <(holdout+test)*1000 ->test; else dev
units: group submissions by problem, keep only >=min_per_problem2, group by cluster root
target per split=min(sample_n,pool) if truthy sample_n else finite-population sample_size(pool)
roots in sampling-seed hash order; holdout skipped unless emit_holdout
pick per problem <=12: hash-order users/subs; first nonempty user with >=2 ordered by hash
  takes first2 before remaining hash-order subs; concat problem groups by problem_id
room=target-taken; if room<2 skip unit; truncate group to room
cost=fn regex count after comment strip; first existing same-split shard that fits max_fns380
  else create if <shards60 for split, EVEN IF single group cost >max_fns; else skip
return plan; source/run later sorts subs by ID within each shard
```

**Limitations:** max_fns not enforced on newly created oversize group; regex function count differs from extracted candidate count (impls/generated/main/closures). Truncation can leave a problem with one submission despite eligibility min2. Fractions/seeds/budgets have no semantic-range validation. Split reserve is procedural flag, not access/security boundary. **Cost:** O(N log N +units×shards), union-find bounded by parsed pairs; storage O(N). **Tests:** `Clusters::{test_cluster_problems_share_a_split_under_every_seed,test_pair_across_cluster_is_identical_problem_not_cross_problem,test_same_seed_same_digest,test_holdout_is_not_written_unless_asked}`; Sampler split test. **Fixture:** one selected cluster >380 functions creates oversize shard; lower sample room1 skips unit; same split_seed different sampling seed preserves cluster split, not members.

## 33. `support.codenet-compile-pairs.rstyle`

**Purpose/output:** source adaptation, compile-based reduction and submission-tier labels/manifests. **Source:** [codenet_sample.py](../../rstyle/scripts/codenet_sample.py#L233), module/write233–251/failing254–260/check_loop263–278/tier281–294/shape297–302/run305–337. **Status:** supporting source generation/reduction, not analyzer rewriting; read only in this audit. Inputs shard plan/code, Cargo compiler; outputs buildable-or-marked-failed shard, module pairs and digest. Parameters eight compile rounds, offline all-target check, edition2021.

```text
module_name='s'+sid.lstrip('s'); crate cn_<split>_<global shard index>
rename EVERY regex '\bfn main\s*(' occurrence to 'pub fn entry_main(' (not parser aware)
write standalone workspace crate lib with pub modules; allow(warnings)
check offline all-targets short diagnostics under /tmp/cn_t_name
if success stop; else filenames src/(s\d+).rs from stdout+stderr -> drop hit modules,
  delete files/update lib; if no attributable hit fail; after8 rounds return false without final recheck
all unordered survivor module pairs inside shard:
  different problem and same nonempty cluster ->identical_problem, else cross_problem
  same problem +same nonempty user ->resubmit, else same_problem
record rows even when build=false; no-check labels builds=true without compilation
manifest funnel compile_fail, shards, args, tier counts, targets/pool, regex fn counts/main-only share
sample digest=SHA1('\n'.join(sorted survivor submission_ids)) (not contents)
```

**Limitations:** default runs compiler on dataset-selected untrusted code, no sandbox/timeout inside script. stale module files remain on reusing output dirs but lib lists only selected modules. main rename can hit comments/string literals and change semantics; compilation is not behavior-preservation proof. Function-count/main-only comment “no fn pair” is historical explanation, not enforced by output: entry_main is retained. **Cost:** up to8 checks/shard (compiler unknown), pairs O(M²). **Tests:** Sampler `test_pairs_have_all_three_tiers_and_no_dropped_submission`, `test_resubmit_is_same_problem_same_user`, `test_main_is_renamed_and_crate_builds`; Clusters deterministic digest. **Fixture:** error in lib with no src/sN attribution ->false with surviving pairs; success only after last deletion is never checked. No sampling executed.

## 34. `support.codenet-function-scoring.rstyle`

**Purpose/output:** weak function-pair labels, IO-helper fixpoint, candidate flag sets and all/comparable denominators. **Source:** [codenet_score.py](../../rstyle/scripts/codenet_score.py#L15), literal prefix tables15–27, module/base30–41, user/plumbing44–60/impl/name/hides63–79/tag82–98/table101–108/pairs111–125/split128–144/tally147–156. **Status:** supporting pure Python. Inputs extracted dictionaries/report/module tiers; outputs helper IDs, fn pair labels, flagged sets/tallies. Parameters max IO statements15; positive tiers resubmit/same_problem/identical_problem.

```text
module = FIRST regex '::(s\d+)(?:::|$)' match
base name removes s\d{3,} even inside qualified trait; repeatedly strip '<...>' not containing ' as '
IO fixpoint, ID map last fact wins; each round iterate insertion order:
  skip alreadyIO OR statements(default99)>15
  users=PDG Call callee IDs present in corpus; output macro by prefix print/println/eprint/eprintln/write/writeln
  reject helper if prints, CallEvent OUTPUT prefix, or users not subset knownIO
  other calls must ALL match literal PLUMBING tuple; '<indirect callable>' disqualifies;
    fn pointer also fails prefix; known input prefix OR any user helper means reads
  plumbing-only + reads OR hides_read ->tag IO
  hides_read: Scanner name OR source regex calls any same-module helper short name
              OR shares impl id with ANY helper (impl set not restricted by module)
fn_table: tag_io with last-by-ID facts, then FIRST fact per ID for module/name/arity
for each module pair/tier, Cartesian nonIO fns:
 positive if same(base name,params); cross_problem negative only DIFFERENT base names;
 all other function combinations unlabeled
candidate: module flag all pairs of site modules (includes helpers)
 real sites=known nonIO; if >=2 distinct modules: all cross-module real fn pairs flagged
 else if >=2 total modules: shared_helper count/pairs
for labeled fn pairs zipped with comparable flags: count 'all'; also 'comparable' iff true
```

**Limitations:** no proof equal name/arity means equal algorithm; negative different names can still be true reuse. IO pruning heuristics and source regex change denominators. Empty-call Scanner method can count helper. `tally` zip silently truncates if comparability vector length wrong. Prefix tables include broad alloc/core/std plumbing; output whitelist is narrower. Function facts default/saved schema assumptions required, not validated. **Cost:** fixpoint up to F growth rounds times call/source scans; function Cartesian O(Fa×Fb); candidate pair generation O(S²). **Tests:** exact Scoring four tests in coverage (handmade facts, no compiler); Sampler tiers. **Fixture:** reader hidden inside closure tagged by regex; printer not IO; same-name cross-problem pair excluded from negative denominator; unknown comparability flags shorter than pairs silently omit tail.

## 35. `support.codenet-run-score.rstyle`

**Purpose/output:** per-config shard evaluation, raw/comparable rates and holdout gate. **Source:** [codenet_eval.py](../../rstyle/scripts/codenet_eval.py#L29), configs29–62/miner65–91/pairs94–109/shard117–128/evaluate131–150/main153–170. **Status:** supporting; not run. Inputs sampled pairs.csv/shards, source compiler, config names, saved semantic facts; outputs results_<split>.csv. Defaults none,all,all+pc650; dev split; holdout requires confirmation, test requires only explicit split.

```text
rules_of: none=''; all-X-Y ->ordered seven rules excluding names (validate removed names); else raw base
miner modifiers: guard flag; pc suffix passed verbatim; h requires numeric suffix; others error
main builds workspace --examples; configs split on ',' (so CLI comma-separated rule base is ambiguous)
run patterns --all-targets with ambient ledger; return code0/1 AND nonempty stdout required
scratch /tmp/cn_m_<seed directory basename>_<shard basename>, independent of config; no report JSON cache
load ALL sorted facts-sem JSON files, no Wanted filename filter
module_tier last row per unordered pair; record34 table/flags/pairs
call norm_comparable(rule base,files) with full-ID tab pairs; stdout whitespace tokens=='1', no length check
sum cells per config/shards selected by shard name starts split+'_'
rate=round(flagged/pairs,4), n0 ->0; shared helper candidate/module counts row with blank rate
```

**Limitations:** modifier guards/thresholds do not enter comparability denominator except normalization; it is core comparable, not final candidate eligibility. Ambient ledger and stale accepted facts can change rates. Test one-shot discipline is documentation, not enforced; holdout only yes/no confirmation. Default out path differs from README seed examples. **Cost:** configs×shards miner + O(labeled pairs) helper subprocess input; miner costs unknown. **Tests:** EvalConfig two tests (parser and holdout before build); Scoring helper tests. **Fixture:** `--configs case,counter` becomes two configs, not joint rules; stale facts file contributes fn pairs; compare all/comparable scope to actual selected pairs. No CodeNet dataset present/revalidated in this audit.

## 36. `support.seed-aggregate.rstyle`

**Purpose/output:** seed means/spread and heuristic beyond-spread comparison. **Source:** [codenet_aggregate.py](../../rstyle/scripts/codenet_aggregate.py#L17), load17–25/summarize28–31/rows34–44/main47–68. **Status:** supporting; inputs results CSVs per seed; outputs table/optional CSV. Defaults seeds1,2,3 splitdev; no external statistics package.

```text
key=(config,level,tier,scope); append every row per seed (no complete-seed enforcement)
rates=h/n if n else0; mean unweighted across available rows
sd=sample stdev(n-1 denominator) if >1 else0; lo=min,hi=max
pooled pairs/flagged=sum separate counts (not used as mean denominator)
if baseline same other dimensions exists and not shared_helper:
 delta=mean-base_mean; beyond=abs(delta)>max(hi-lo,base_hi-base_lo) STRICT
main omit shared_helper rows, optional level filter; CSV floats round5
```

**Limitations:** seed spread rule is not significance test/CI; missing/duplicate seed rows silently change number/weights. **Cost:** O(CSV rows +cell sorting), memory rows. **Tests:** no direct tests found. **Fixture:** rates1/1 and0/99 mean0.5 while pooled1/100; identical delta=spread is not beyond. Unknown historical artifacts do not support a current recall claim.

## 37. `support.sign-flips.rstyle`

**Purpose/output:** paired binary detection changes and exact two-sided sign test. **Source:** [codenet_flips.py](../../rstyle/scripts/codenet_flips.py#L19), sign_test19–22/flips25–42/main45–56. **Status:** supporting; input same module tiers, two miner configs, current facts; output per-tier [both,A-only,B-only,neither] and p. Defaults seed1,2,3 splitdev; no holdout option.

```text
for each seed and matching split shard sorted: run configA then configB with same scratch tag
use each to get flag sets; build function pairs using table from LAST(B) facts
cell index = 3 -2*bool(in A)-bool(in B)
sign n=onlyA+onlyB,k=min; p=min(1,2*sum(comb(n,i),i=0..k)/2**n), n0 ->1
```

**Limitations:** pairs share functions/shards, independence not established; test measures count direction, not semantic correctness. Python big integer combinatorics then float division; no large-n numeric cap. **Cost:** miner twice/shard; sign O(k) combination sums (big-int cost unknown). **Tests:** `Flips.test_sign_test_is_exact_and_symmetric`. **Fixture:** no discordance p1;0 versus6 ->2/64; swap counts same p. Pair identity changes between configs would be scored on B's table only.

## 38. `support.auc-bootstrap.rstyle`

**Purpose/output:** paired raw/canonical ranking separation, bootstrap uncertainty and excess above negative threshold. **Source:** [codenet_sep.py](../../rstyle/scripts/codenet_sep.py#L26), constants26–29/auc32–38/paired_ci41–53/percentile62–64/excess67–71/sample74–77/collect88–105/views108–113/report116–136/main139–151. **Status:** supporting; inputs cached raw facts + norm_sim numeric output; output printed statistics. Parameters negative cap4000/shard, boot200, bootstrap seed7; raw resubmit positives, cross-problem negatives; same/identical unlabeled.

```text
sample negatives by SHA1(seed:shard + ':' + fnA+'|'+fnB), retain first cap; keep all other tiers
collect zipped pair/norm_sim rows; skip NA; parse eight integers
views: WL and coverage only cmp_raw && cmp_canon; coverage-all uses norm_sim0 when incomparable
AUC = sum(count neg<p +0.5*count neg==p)/(Npos*Nneg); missing side ->NaN
bootstrap Random(seed): independently resample positives/negatives with replacement preserving
  raw/canon within each row; diff=AUCcanon-AUCraw; sorted B diffs
CI=[diff[int(.025B)],diff[min(B-1,int(.975B))]]
threshold=sorted raw negative coverage index min(n-1,int(.99n)) (not interpolated)
excess=(fraction tier score>threshold - fraction neg>threshold)/(1-fneg), fneg1 ->0
compare canonical excess against SAME raw-derived threshold
```

**Limitations:** per-pair bootstrap ignores correlated functions/shards/seeds; printed warning is not correction. Missing tier keys/empty comparable pools/boot0 can error; no input guards for these. Negative sampling biases possible labels. **Cost:** B×(P+N log N) conservative via AUC sorting, O(P+N+B) storage; core measurement unknown. **Tests:** Separation three named tests in coverage. **Fixture:** identical raw/canon ->zero diff interval; all ties AUC0.5; empty comparable view not robust. These are proxy labels, not refactoring correctness or paper fidelity.

## 39. `support.unmatched-triage.rstyle`

**Purpose/output:** estimate unmatched graph mass and rank normalization changes for manual review. **Source:** [codenet_sep.py](../../rstyle/scripts/codenet_sep.py#L56), unmatched56–59/report122–136; [codenet_drops.py](../../rstyle/scripts/codenet_drops.py#L18), shard_pairs21–30/measure33–36/gap39–41/collect44–59/main62–85. **Status:** supporting only, not structural proof or detector. Inputs numeric raw/canonical WL score and max node count, source facts; outputs per-pair gaps/sources and counts. Defaults dev,fn_resubmit,top10,sign added; rules all +each7.

```text
unmatched = nmax*(1000-wl_milli)/1000 (FLOAT proxy)
gap=canon_unmatched-raw_unmatched
load first fact per ID across sorted files; record34 pairs of chosen tier
measure all and singles with norm_sim; include only all-rule cmp_raw AND cmp_canon
collect gap and available per-rule gaps, both source snippets
counts: removed gap<-0.5, added gap>0.5, remainder same
rank descending gap for 'added', ascending for 'removed'; show first top (not strict-sign filtered)
```

**Limitations:** WL histogram kernel score is not exact unmatched-node count/alignment cardinality. Comment “every increase is a rule defect” is a historical hypothesis, not verified finding. Contraction math can reduce ratio without changing difference; proxy depends on quantized WL. No score-length check before positional indexing in drops; source saved cache stale. **Cost:** pairs×8 measurements +O(pairs log pairs) ranking, core unknown. **Tests:** `Flips.test_unmatched_ignores_shared_contraction` checks numeric approximation within0.2, not graph-level correctness. **Fixture:**100 nodes score900 ->10;95 nodes score894 ->10.07; returned top may have wrong sign if no positive/negative gaps. No benchmark or historical measurement reverified.

## 40. `support.sample-size.rstyle`

**Purpose/output:** nominal independent-proportion sample count with finite-population correction. **Source:** [sample_size.py](../../rstyle/scripts/sample_size.py#L18), z_score18–20/sample_size23–28/table31–36/main39–45. **Status:** supporting stdlib NormalDist; inputs population/confidence/margin/p; outputs integer count. Parameters confidence95 or99 in table/sampler, p0.5, standalone population53822, margins.05/.03/.02/.01.

```text
z=NormalDist.inv_cdf(0.5+confidence/200)
n0=z*z*p*(1-p)/(margin*margin)
if population None: ceil(n0)
else min(population,ceil(n0/(1+(n0-1)/population)))
```

**Limitations:** no population/margin/p domain validation; population0/margin0 divides by zero. Independence/design-effect not modeled; sharding later can fall short target and compile filtering reduces achieved counts. **Cost:** O(1) library inverse-CDF boundary, table proportional margins. **Tests:** `Clusters.test_sample_size_is_finite_population_corrected`: None95/.05=385, None99=664, population53822=656, population10=10. **Fixture:** p0.5 positive, finite n10 capped, n0 invalid population boundary. Nominal precision is not evidence actual correlated corpus estimates meet CI coverage.

## 41. `support.package-recreation.rstyle`

**Purpose/output:** external corpus Rust-only extraction/training package build. **Source:** [recreate_rust_package.py](../../rstyle/scripts/recreate_rust_package.py#L43), fetch43–62/selection67–85/extract94–125/text130–150/rows153–227/copies229–276/sample278–289/code292–311/record314–341/jsonl344–355/build388–396/main401–426. **Status:** supporting; not run, no network/download. Inputs CodeNet1.0.0 tar/extracted files; outputs consolidated Rust metadata/code/descriptions/derived/statistics. External curl/tarfile/HTMLParser algorithms boundaries. Parameters description text8000, HTML20000, sample input/output4000 chars; UTF8 replacement.

```text
fetch-only: curl resumable -C - with retries3 delay5, destination explicit/default
extract: use existing --tar else curl streaming -L --retry3 --fail; iterate gzip tar once
keep top README, ALL metadata/problem_descriptions/derived prefixes,
  data/<problem>/Rust subtree by parts[3]=='Rust'
tar.extract(filter='data'); on TypeError fallback unfiltered extraction
finally wait curl/print status; nonzero stream curl not explicitly raised by code
build uses FIXED relative Project_CodeNet and rust_package, ignores --dest and --url output provenance
read sorted per-problem metadata; language EXACT Rust; trim ONE trailing '\r' from values;
  errors warn and return[]; write per-problem and consolidated metadata
copy descriptions; replace derived input_output; copy identical problem clusters/readmes,
  omit bulk duplicate data FROM package (extract had kept entire derived subtree)
for each Rust metadata row: read filename_ext then fallback.rs; no/empty/read-fail code ->skip
HTMLParser joins stripped handle_data including script/style contents; errors ignored; truncate
record metadata/code/raw/text descriptions/samples; preserve input row order; write JSONL
statistics count files/rows; no asserted expected counts or package digest
```

**Limitations:** --dest extraction can conflict with fixed build paths; --keep-tar flag parsed but unused; absent nonexisting --tar gets downloaded regardless keep flag. Streaming still retains derived bulk subtree, contrary to package-copy savings implication. No input checksum/pinning beyond URL; unfiltered old-Python fallback potentially unsafe tar behavior. Tool description expected127210/2139 is not verified here. **Cost:** full archive scan/decompression + code bytes and per-row repeated description/sample reads; memory all Rust rows. **Tests:** no direct recreation tests found. **Fixture:** --dest otherdir with build ->reads default Project_CodeNet; empty code omitted; metadata unknown language excluded. No download/install performed.

## 42. `support.harnesses.rstyle`

**Purpose/output:** quality gates and curated measurement/tracing invocation. **Source:** [style.sh](../../rstyle/scripts/style.sh#L4)4–7, [test.sh](../../rstyle/scripts/test.sh#L5)5–8, [eval_examples.sh](../../rstyle/scripts/eval_examples.sh#L4)4–26, [norm_pairs.sh](../../rstyle/scripts/norm_pairs.sh#L4)4–32, [wl_site.sh](../../rstyle/scripts/wl_site.sh#L4)4–44, [install-hooks.sh](../../rstyle/scripts/install-hooks.sh#L3)3–7. **Status:** supporting; not run. Inputs CLI flags/caches/curated pairs; outputs exit gate, lists/traces or hook setting. Dependencies production pipelines, record27 and29; shell/process internals unresolved.

```text
style: build workspace; exec CLI rstyle with forwarded args, honor CARGO_TARGET_DIR or target
  source contains NO assertion that violations==0 beyond CLI exit behavior
test: shared target dir CARGO_TARGET_DIR else XDG_CACHE_HOME/HOME cache; test workspace --locked +args
eval_examples: build; four projects × supplied thresholds or800,600,500,400,300;
  all-target patterns; parse JSON, print candidate/suppressed site sets (stderr suppressed)
norm_pairs: build core example; hardcoded fifteen labeled pairs; default rulesall; raw cache glob;
  print raw/canonical row measurements record27, not production candidates
wl_site: build example/workspace; only run miner if cache DIRECTORY absent, ignores failure;
  five hardcoded pairs B1,Q2,self-clone,T3,T4 with expected high/low labels;
  trace600; write site JSON/index; optional --serve static server (transport excluded)
install-hooks: chmod tracked hooks; git config core.hooksPath=.githooks; hooks internals out of slice
```

**Limitations:** directory existence is not freshness/completeness, curated high/low not automated assertions. Parent shell pipelines lack pipefail in sh: CLI failure may surface only JSON parse error. Hook installation is infrastructure excluded; CI candidate flags change semantics through record1. **Cost:** builds/checks external + fixed/grid pair counts. **Tests:** this_workspace_passes_its_own_rules encodes style gate; golden traces not proof of paper parity; scripts/test.sh would run costly full tests and was not run. **Fixture:** present empty/stale cache directory skips wl_site gathering; `style patterns --top0 --fail-on-candidates` inherits display-filter gate. Next phase should separate curated explanation from reproducible evaluation.

## Consequential fact drops and unresolved contract edges

| First stage / record | Actual drop or collapse | Consequence / minimal distinguishing input |
|---|---|---|
| function discovery4 | expansion signature/outside real workspace/snippet failure omitted | no unknown/incomplete row; compare macro-generated versus handwritten function |
| identity/merge5,18 | compiler ID ≠ display location key ≠ locator | duplicate-target/cfg conflicts choose first key record, not richest facts; reverse colliding inputs |
| provenance7 | aliases/destructuring not Param; refs/derefs erased | pass-through plan can undercount/blur borrow mode |
| calls8,21 | nondynamic unclassified calls absent from direct effects; closure calls not emitted | “pure” evidence can mean unrecognized, not effect-free |
| mutation9 | root spelling/field-only path, delegation every mutable borrow + workspace whole object | shadowing/index/alias collapse; line matching can misattribute delegated writes |
| signature10 | const/lifetime/array length/fnptr/raw pointer details erased | different callable contracts share type shape |
| PDG12–17 | no assignment rebind, branch value merge, loop-carried fixpoint, execution/memory edges; closures/macros opaque | graph similarity does not imply refactoring safety or preserved dependence |
| prep19 | generic self args not table key; order hide after devirtualize | wrong owner for colliding instantiations; oracle changes locators but keeps rewritten callees |
| patterns22 | style config/excludes not applied; ledger then score/top then CI gate | patterns findings/gate can differ despite same config or existing mined pool |
| identity24–25 | structure label hash ignores some semantic edits; high48 candidate hash unchecked | reviewed candidate can stay suppressed after literal/field/definition edits |
| status26 | raw versus prepared PDG shape; locator@- parse fallback | false “shape changed”/“gone” status possible; needs distinguishing fixture |
| saved examples27 | first ID, raw facts, prep bypass, comparability guard differences | saved trace/coverage not automatically production result |
| eval28–41 | cache keys lack content provenance, proxy labels/denominators, ambient ledger | historical recall/noise claims not current observation or correctness proof |

**Handoff priorities:** (1) record raw/merged/prepared PDGs for assignment, branch-result, while/for, closures/macros and indirect-call ports; (2) validate cache deletion/stale-file/collision and target-name cases; (3) distinguish raw/prepared status fingerprints, generic impl collision and semantic-edit ledger persistence; (4) reconcile supporting scoring denominators/cache/label provenance with artifact-producing revisions; (5) complete Go/paper comparison and compiler-library semantics under their respective owners. Phase one does not choose unified behavior or implement these fixtures.
