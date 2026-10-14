# Rust core algorithm inventory — phase one

**Snapshot:** independent Rust repository HEAD `2c4752ca9c7b992e66d21380600a69f597133687`, clean when inspected, 2026-10-10. **Status: partial audit checkpoint**, not a parity/conformance or safety verdict. All local core source/example/test bodies were read; reference comparison, external producer contracts and dependency internals remain unresolved. See [coverage and exact test assertion ledger](../rust-core-coverage.md).

## Record conventions and evidence boundaries

Each `### ID` below is an algorithm record, not a proposal. Shared fields apply to every record unless overridden:

- **Implementation/status:** implemented Rust at the snapshot above; paths below link to that checkout. `src/foo.rs:Lx–Ly` means `rstyle/crates/rstyle-core/src/foo.rs`, not a parent-repository revision. Symbols and ranges are supplied per record.
- **Go pseudocode / reference pseudocode:** unresolved in this owned slice, not absent globally. The plan and reflection were read as discovery inputs; the PDF was hashed but not inspected. No paper-exact assertion or Go/Rust equivalence is made. Reference-stage contracts must be reconciled by the paper/parity audit.
- **Evidence:** implementation and local wiring source-verified; tests are inspected **assertions, not executed results**. The coverage document maps every named test to its exact claimed result. Examples/fixtures here are hand-built or unexecuted unless expressly identified otherwise.
- **Inputs/missing facts:** these are plain facts, not compiler types. Schema defaults do not establish completeness, purity, ownership or absence of effects. No validation of PDG acyclicity, index validity or graph semantics precedes every consumer. `usize` arithmetic is ordinary Rust arithmetic unless explicitly stated; no saturating/checked overflow policy should be inferred from integer-only scoring.
- **Activation/callers:** `S` means production style `evaluate`; `P` means production `patterns_report::run` or unfiltered `all_candidates`; `O` means opt-in mining parameter; `L` means public/library API; `T` means supporting example/trace. Production boundary inspected in `cargo-rstyle/src/main.rs:97–124,186–238,259–277`: style gathers non-PDG facts and loads Config; patterns gathers semantic facts and passes mining Options, not style Config. CLI descriptions `0..=1000` do not themselves enforce this range on `u32` flags.
- **Tests/examples:** consult the matching module heading in the assertion ledger. A positive fixture plus boundary/negative guard is stated where useful; untested distinctions are labeled **fixture design**.
- **Cost:** source-derived upper bounds, not measurements. `F` functions, `E` graph edges, `V` nodes, `M` mutation events, `C` calls, `D` propagation depth; string/comparison costs additional. Where recursion or helper rescanning prevents a useful bound, marked unknown. No new tests, source rewrites, benchmarks or unified behavior are implemented.

## Entrypoints, facts and quality

### facts.schema.rust — serialization contract

**Source:** [facts.rs](../../rstyle/crates/rstyle-core/src/facts.rs):7–355, `FnFacts`, `MutationEvent`, `Edge`, `SigFacts`, `Pdg`; consumed by S/P/T. Implemented data boundary; frontend producers out of scope.

```text
Deserialize required FnFacts fields: path,line,column,name,params,has_self,statements,
  source,preceding_line,mutations,calls,effects.
Default id="", implements=None, param_list=[], top_statements=0, edges=[],
  mutated_types=[], sig=None, pdg=None.
MutationEvent requires root,field_path,line,escapes; delegated defaults false.
CallEvent requires callee,line; dynamic defaults false.
Edge requires callee,line; dynamic=false,args=[] by default.
ParamFacts requires name,type (serialized spelling of ty); uses=0 by default.
SigFacts requires receiver,ret; defaults self_ty=None,self_args=[],params=[],
  is_async/is_unsafe/is_const=false,generics=0.
Pdg defaults nodes=[],edges=[]; PdgNode requires kind only:
  ty/callee_id/callee_sig/macro_name/lit_kind=None,detail="",line=0.
PdgEdge requires from,to,kind; arg_pos=0 by default.
```

PDG edge kinds are **Data and Ctrl only**, no execution-edge variant. Direction is `from` producer/controller to `to` consumer/controlled node; `arg_pos` carries operand/arm index. No effect bits on `PdgNode`; effect evidence lives on function facts. `Ctor` and `Case` are normalization kinds. Serde fact structs do not deny unknown fields; config/ledger do. Missing PDG prevents layer-2 site participation but not signature grouping; missing top-statement evidence silently skips default spacing; missing param uses prevents pass-through inference. Schema tests assert old absent sig parses, sparse Lit line defaults 0, optional PDG round-trips; no frontend extraction is established. Cost serialization linear in fact size; serde internals unresolved.

### facts.merge — physical deduplication

**Source:** [facts.rs](../../rstyle/crates/rstyle-core/src/facts.rs):357–369 `key`, `merge`; S (`lib.rs:125`) and P (`patterns_report.rs:71`). Outputs location/name-ordered facts.

```text
stable_sort(facts, key=(path,line,column,name));
remove adjacent equal keys; retain first occurrence in original input order;
return remaining facts.
```

**Not** an id-keyed union or strongest-fact merge. Conflicting duplicate source/PDG/effect evidence is discarded according to input order. O(F log F), O(F) sorting space implementation-dependent. Tests `merge_sorts_and_dedupes`, `merge_is_order_independent` exercise identical/nonconflicting entries only. **Fixture design:** same physical key, one pdg=None and one pdg=Some(g); reverse input and inspect survivor. This distinguishes the implementation from its broad order-independence comment.

### facts.config-defaults.rust — semantic configuration loading

**Source:** [config.rs](../../rstyle/crates/rstyle-core/src/config.rs):4–284 `Config::parse`, defaults, `RuleList::try_from`; S/L. TOML/serde external implementation unresolved.

```text
parse TOML with defaults for omitted tables/fields; reject unknown Config/nested keys;
RuleList rejects first name not in suppress::RULE_IDS; duplicates remain legal.
Defaults:
 exclude=["target/**"];
 fn_length.max_lines=50;
 fn_params.max_params=4,count_self=false;
 fn_spacing.min_statements=5;
 mutation.max_mutations_per_target=3,max_mutated_targets=3,granularity=Root;
 side_effects.max_density_milli=500,min_statements=3,min_lines=10,
   transitive_depth=3;
 weights=(mutation1,io3,network3,global2,unsafe4,time1,random1,panic0,unknown1);
 grouping.caller_rules=["fn_params"],caller_hops=1.
```

No numeric range validation beyond deserializing unsigned values. `abstraction` is valid in RuleList but not a style-emitted detector. Config tests assert defaults, nested override preserves unrelated defaults, typo errors and grouping rule validation. O(input bytes + rule-list validation); excluded-glob matching boundary handled by quality evaluation, not P.

### quality.code-lines.rust — byte scanner and blank lines

**Source:** [lines.rs](../../rstyle/crates/rstyle-core/src/lines.rs):5–40 `code_lines`, `line_has_code`, `has_blank_line`; S/rules and driver helper.

```text
depth=0; count=0;
for source.lines() in order:
 i=0; has_code=false;
 while i < byte_length(line):
   if suffix starts "/*": depth+=1; i+=2;
   else if depth>0 and suffix starts "*/": depth-=1; i+=2;
   else if depth==0 and suffix starts "//": break;
   else: has_code |= depth==0 && !byte[i].is_ascii_whitespace(); i+=1;
 count += has_code;
has_blank_line = any line.trim().is_empty().
```

Nested comments span lines. Scanner has no string/character/raw-string lexical state, so comment delimiters inside a string can change counts. Blank line anywhere in signature/body (even comment block) counts as spacing. O(bytes), O(1) scanner state. Tests establish three code lines in a comment-heavy fixture, code next to comments counts, nested comments work, whitespace line is blank but `// c` is not. **Fixture design:** `let x = "/*";` followed by code lines; compare lexical count to this scanner.

### facts.preceding-comment.rust — suppression source-line selection

**Source:** [lines.rs](../../rstyle/crates/rstyle-core/src/lines.rs):44–52 `preceding_comment_line`; driver/helper L, downstream `suppress::parse`.

```text
take lines before min(fn_line_index,lines.len()); walk backwards;
trim each; return first not starting "#[" or "///"; otherwise "".
```

It returns a blank or ordinary code line too; does not skip `//!`, multi-line attribute continuations or blanks. O(number of skipped lines). Test skips one doc line and inline attribute, returns allow comment; index 0 returns empty. **Fixture design:** blank between valid comment and attribute/function blocks suppression.

### quality.fn-length — strict line threshold

**Source:** [rules.rs](../../rstyle/crates/rstyle-core/src/rules.rs):29–37 `fn_length`; S/L; requires source.

```text
actual=quality.code-lines.rust(source);
if actual>max_lines (default50): emit one fn_length diagnostic at f.path,line,column;
else [];
```

Includes signature/closing brace code lines; no minimum-statement gate; equality passes. O(source bytes). `length_boundary`: body_of(48) =50 passes; body_of(49) yields actual51. Missing source cannot deserialize; empty supplied source measures0.

### quality.fn-params — count plus optional receiver

**Source:** [rules.rs](../../rstyle/crates/rstyle-core/src/rules.rs):39–49; S/L.

```text
actual=f.params + int(config.count_self && f.has_self);
if actual>max_params(default4): one fn_params diagnostic; else [].
```

Does not recompute from param_list; inconsistent supplied counts remain inconsistent. O(1). `params_boundary_and_self` asserts4+self passes default, self enabled actual5, params5 actual5 with self disabled.

### quality.fn-spacing.rust — top-level statement gate

**Source:** [rules.rs](../../rstyle/crates/rstyle-core/src/rules.rs):54–65; S/L.

```text
min=cfg.fn_spacing.min_statements(default5);
actual=f.top_statements; limit=min.saturating_sub(1);
if min>0 && actual>=min && !has_blank_line(source): emit fn_spacing(actual,limit);
else [].
```

Old facts top_statements=0 skip. No check that blank separates meaningful phases. Tests assert4 passes,5 flags(5,4), adding blank passes, long initializer top=3/old0 passes, min0 disables and min10 admits top20. O(source bytes).

### mutation.target-groups — root/field identity

**Source:** [rules.rs](../../rstyle/crates/rstyle-core/src/rules.rs):67–90 `mutation_groups`, `to_details`; S/L through budgets. Inputs already extracted mutation events, no alias analysis in core.

```text
BTreeMap<String,Vec<usize>> groups={};
for mutation in supplied order:
 key=root; if granularity=Field && field_path!="": key=root+"."+field_path;
 append line to groups[key];
details=ascending key rows(label,count=lines.len(),lines unchanged).
```

All events count, irrespective of `escapes`/`delegated`; repeated same line counts repeatedly. No initialization exclusion here. Root default collapses all self fields. O(M log M), O(M). Root/field tests distinguish four fields → one target with count4 vs four one-write targets.

### mutation.per-target — budget maximum

**Source:** [rules.rs](../../rstyle/crates/rstyle-core/src/rules.rs):92–112 `mutation_budget`; S/L.

```text
over=groups whose event count>max_mutations_per_target(default3);
if nonempty: emit ONE mutation_per_target with actual=max count in over,
  limit=config max and only over-target details;
```

No warning at3; four self fields in Root emit one diagnostic actual4 detail self. Local four writes still flag despite zero density. O(M log M), details space O(M).

### mutation.distinct-targets — target breadth budget

**Source:** [rules.rs](../../rstyle/crates/rstyle-core/src/rules.rs):113–125; S/L, after per-target emission.

```text
if groups.len()>max_mutated_targets(default3): emit mutated_targets,
 actual=groups.len(),limit=max,details=ALL groups;
return per-target then breadth diagnostics.
```

Both can emit; no cap beyond configured limit; empty events produce none. Test four roots gives mutated_targets actual4; Field split fixture with max_targets4 gives none. O(number of groups) after grouping.

### effects.path-classification.rust — longest textual prefix

**Source:** [config.rs](../../rstyle/crates/rstyle-core/src/config.rs):183–237 `DEFAULT_IO`, `EffectPaths::classify`; S direct effects/L; no driver recomputation required when Config changes.

```text
tables in order = IO,Network,Time,Random,Panic;
flatten prefixes in table/list order; keep callee.starts_with(prefix);
choose max prefix byte length; equal length chooses LAST matching entry;
return its single kind, or None.
```

IO defaults: `std::fs::`, `std::io::`, `std::env::set_var`, `std::path::Path::{exists,try_exists,is_file,is_dir,metadata,canonicalize,read_dir}`, `std::process::Command::{output,spawn,status}`, `std::process::{exit,abort}`. Network: `std::net::{TcpStream,TcpListener,UdpSocket}::`, `reqwest::`, `tokio::net::`, `hyper::`. Time: `std::time::{SystemTime,Instant}::now`; random:`rand::`; panic:`core::panicking::`,`std::panicking::`. Brace notation here expands to literal separate prefixes. Text prefix, not symbol-component equality: `set_var_extra` also matches. No default Global/Unsafe/Mutation prefix table. Overrides replace supplied lists while other defaults survive. O(total prefix bytes tested). Tests distinguish process builder env and SocketAddr getter (None) vs output/UDP send (classified); longest random override beats IO. **Fixture design:** identical prefix in IO and Panic returns Panic.

### effects.direct-summary.rust — direct weighted event construction

**Source:** [rules.rs](../../rstyle/crates/rstyle-core/src/rules.rs):127–174 `Effect`, `effects_of`; S via `all_effects`, L. Inputs mutations,calls,intrinsics; output ordered event list, not completeness lattice.

```text
written=BTreeSet<(root,field_path)>;
for escaping mutations in input order:
 if pair newly inserted: emit Mutation(label=root[.field],line=first escaping line,via=None);
for calls in input order:
 kind=path classification OR (if dynamic then Unknown else None);
 if kind exists: emit(kind,label=callee,line,via=None);
for every f.effects intrinsic: emit(kind,label=detail,line,via=None);
concatenate in that order; no cross-stream or call/intrinsic deduplication.
```

Unclassified **static** external call produces no event, not Unknown. Classified dynamic call keeps known kind. Non-escaping locals budgeted but do not add effects. Field identity always used for effect dedup even with Root mutation budget. O(M log M + prefix classification + intrinsic count), O(events). Tests give unknown dynamic fn pointer then IO for known dynamic path; repeated writes → one effect; IO+unsafe+mutation arithmetic fixtures in ledger. **Fixture design:** same intrinsic and classified call retained twice.

### effects.transitive-export.rust — outward collapse and trait intersection

**Source:** [graph.rs](../../rstyle/crates/rstyle-core/src/graph.rs):84–182 `boundaries`, `outward`, `split_more`, `exported_by`, `exported`; S propagation/L.

```text
boundary[t] = valid allow(side_effect_density) comment;
delegated = any caller mutation with delegated=true AND line==call.line;
for each sorted target t:
 if boundary[t]: export [];
 else:
  group target current effects in EffectKind order, retaining only
    IO,Network,Global,Time,Random;
  for each kind:
   base=first effect.label stripped of final " +N more" if parseable;
   total=sum(1+parsed N) over group;
   export(kind,label=base if total==1 else base+" +{total-1} more",
          line=call.line,via=target.name);
  if delegated && any target current Mutation:
   append Mutation("&mut state",call.line,via=target.name);
take FIRST target's exported events whose (kind,label) occurs in EVERY other export;
keep first target's via/name and line; return.
```

Not a may-effect union and not even an intersection by kind alone: IO `read` vs IO `write`, or differing aggregate counts, prevents inheritance. Panic, Unsafe, Unknown and nondelegated Mutation stay local. Delegation is line-based, not per receiver/call-site identity. Boundary absorbs exports but does not erase callee's own current effects. Tests cover same-label intersection, one effectful target vs pure, boundary, collapsed `open +2 more`, accumulated counts, delegated b write vs pure c. **Fixture design:** both targets IO with different labels yields empty caller; two unrelated calls on one line share delegation evidence. O(target effect counts plus intersection scans), label count overflow unchecked.

### effects.transitive-summary.rust — bounded synchronous rounds

**Source:** [graph.rs](../../rstyle/crates/rstyle-core/src/graph.rs):184–223 `Inputs`, `round`, `propagate`; [lib.rs](../../rstyle/crates/rstyle-core/src/lib.rs):109–120 `all_effects`; S default depth3/L.

```text
current=direct.to_vec(); repeat up to depth:
 for each function i using OLD current:
  out=direct[i].clone(); seen={(kind,label) of direct[i]};
  visit resolved calls in sorted Callee order;
  for exported events: append only if (kind,label) newly seen;
 next=all out;
 if next==current (full event equality including via,line): break;
 current=next;
return current.
```

Direct duplicates remain in out even though seen is set; repeated inherited labels across callers/call sites collapse, retaining first call's line/via. No summary unknown on unresolved edges or depth exhaustion. Rounds restart from direct rather than append indefinitely; cycles bounded even if labels change and no fixpoint. Tests chain depths0/1/2, immediate via c/b and call line5; two-node same-IO cycle gives one event each; no general convergence theorem. Cost O(D × per-round export work), O(total current+next events); depth0 returns direct.

### quality.side-effect-density — weighted per-statement threshold

**Source:** [rules.rs](../../rstyle/crates/rstyle-core/src/rules.rs):176–219 `density_milli`, `effect_details`, `side_effect_density`; S/L, consumes full propagated effects.

```text
total=sum(cfg.weights[kind] for EVERY effect);
actual=1000*total / max(f.statements,1); // usize, floor division
small=(statements<min_statements(default3) || code_lines(source)<min_lines(default10));
if small || actual<=max_density_milli(default500): [];
else group only positive-weight effects by sorted label
 "{kind}: {label}" + optional " (via {via})"; retain line order;
 emit one side_effect_density(actual,limit,details).
```

Summary computes actual even for exempt/suppressed functions; no 1000 clamp (1500,2500 legal). Zero-weight panic counted in summary events but not diagnostic details. Multiplication/sum overflow not checked. O(effects log effects+source bytes). Tests assert6/4→1500; mutation1+unsafe4 over2→2500;9 lines skip,10 checked; weight3→750 then1→250 passes. Empty effect vector with statements0→0.

### quality.evaluate.rust — selection, rule order, suppression and summary

**Source:** [lib.rs](../../rstyle/crates/rstyle-core/src/lib.rs):37–145, [report.rs](../../rstyle/crates/rstyle-core/src/report.rs):119–123; S entry, CLI `analyze` above.

```text
build globset from cfg.exclude; any invalid Glob/build returns Err before analysis;
facts=merge(facts); drop excluded path matches;
graph=refactor.call-graph; full=direct-summary + transitive-summary;
for each fact:
 concatenate fn_length,fn_params,fn_spacing,mutation_budget,side_effect_density;
 parse preceding_line:
  None: unchanged;
  Allow(names): retain diagnostics whose rule_id not named;
  Invalid(msg): append invalid_suppression(actual1,limit0,details=[]);
stable-sort diagnostics(path,line,column,rule_id);
summary.functions=facts.len; violations=diagnostics.len;
 densities=per-function density including exempt/suppressed;
 mean=sum densities/max(F,1), max=maximum or0;
 counts=each full Effect event by kind name (including weight0);
fix_groups=groups::build using FINAL diagnostics; return Report.
```

Invalid suppression itself can create a fix group. Excluded callees cannot contribute graph/effect facts. Rule suppression also defines transitive boundary through separate parse. Tests assert only mutation remains after params suppression, invalid missing reason coexists with params, excluded target path drops functions/diagnostics, summary(2,750,375,io1). Globset `0.4.20` internals unresolved. Cost sum of stages plus O(diagnostics log diagnostics); no style cache in core.

### patterns.comment-suppression.rust — validated reason-bearing allow syntax

**Source:** [suppress.rs](../../rstyle/crates/rstyle-core/src/suppress.rs):3–44 `RULE_IDS`, `parse`, `allows`; S/P/L, via preceding_line supplied fact.

```text
trim entire line; if not starts exact "// rstyle-allow(": None;
split rest at FIRST ')'; if absent: Invalid(malformed);
reason=tail.strip_prefix(':').map(trim) or "";
if empty: Invalid(requires reason);
names=rules.split(',').map(trim); first not registered -> Invalid(unknown);
otherwise Allow(names). allows(rule) only true for valid Allow containing rule.
```

IDs: fn_length,fn_params,fn_spacing,mutation_per_target,mutated_targets,side_effect_density,abstraction. Space between `)` and `:` is invalid, duplicate names permitted, empty rule list invalid. O(comment length). Valid abstraction removes mining function, valid density stops exports. Tests exact named lists/reasons, plain comment/empty None, unknown/missing reason Invalid. No universal suppression for invalid_suppression.

### facts.path-normalization.rust — strip turbofish only

**Source:** [paths.rs](../../rstyle/crates/rstyle-core/src/paths.rs):4–23 `strip_generics`; L driver-facing helper, producer activation beyond caller search unresolved.

```text
scan Unicode chars with peek; depth0:
 when current ':' and next2 == ':<': consume those2; depth=1;
 otherwise emit character;
depth>0: '<' increments, '>' decrements, everything else dropped.
```

Does not strip bare `<Foo as Bar>` qualified paths. Unclosed turbofish truncates suffix without error. O(chars), O(output). Tests Vec/HashMap turbofish, nested Vec and lifetime removal, plain/qualified unchanged.

### facts.text-clipping.rust — char-count truncation

**Source:** [clip.rs](../../rstyle/crates/rstyle-core/src/clip.rs):4–10 `clip`; L driver-facing helper. Fact-string information loss boundary, producer limits unresolved.

```text
if text.chars().count()<=limit: return text;
else return first limit.saturating_sub(3) chars + "...".
```

Limit<3 can yield three characters, exceeding limit. No hash/checksum keeps lost suffix. O(chars), O(output). Tests short32 unchanged,40 ASCII limit32→29+dots,40 é limit24→21é+dots. **Fixture design:** distinct long literals same clipped prefix can merge hole values downstream if producer uses this helper.

## Call graph and refactor planning (not source rewriting)

### refactor.call-graph.rust — resolved multi-target graph

**Source:** [graph.rs](../../rstyle/crates/rstyle-core/src/graph.rs):23–82 `Callee`, `Graph`, `build`, `callers`; S→effects/groups/stacking; L.

```text
by_id maps each f.id -> vector of fact indices;
also map every f.implements trait-method id -> its index;
for each caller i and input Edge:
 lookup edge.callee; missing -> drop;
 targets=sorted unique found indices excluding i; empty -> drop;
 make Callee(line,targets,args=clone);
unique/sort Callees by derived order(line,targets,args);
callers[t]=sorted unique i for all resolved calls' targets.
```

`Edge.dynamic` is **ignored**; not devirtualized by receiver type here. Trait default body indexed by id plus all impls; same-id facts may yield several targets. Self recursion removed, mutual cycles retained. Distinct calls same line/targets/args deduplicate. No unknown edge node. O(F log F+edge resolution/sorting), O(F+resolved target incidence). Trait test asserts one call with2 targets; grouping/stacking tests use inverse graph. **Fixture design:** dynamic false/true otherwise identical yield same graph.

### refactor.edit-footprints.rust — caller-hop union

**Source:** [groups.rs](../../rstyle/crates/rstyle-core/src/groups.rs):45–90 `violators`, `with_callers`, `footprint`; S after suppression.

```text
by_location[(path,line,column)]=index (last fact at same location wins);
for diagnostic with matching location: rules[index].insert(rule_id);
footprint(i) starts {i}; if ANY rule in caller_rules then hops=caller_hops else0;
frontier={i}; repeat hops:
 next=callers of frontier not already seen; mark and replace frontier;
return seen.
```

Default caller rule fn_params,1 hop; excludes name/id from diagnostic mapping. Nonviolating callers may connect footprints. O(hops × traversed caller incidences); visited prevents repeated inclusion/cycles. Tests default/non-signature split, configurable density grouping, second hop joins top/leaf.

### refactor.fix-grouping.rust — DSU over footprint membership

**Source:** [groups.rs](../../rstyle/crates/rstyle-core/src/groups.rs):23–42,189–265 `Dsu`, `roots`, `components`, `build`; S.

```text
dsu parents=0..F;
for sorted violating index i:
 for every footprint item x: union(i,x), always smaller root, path compression;
bucket ONLY violating indices by root;
sort buckets by smallest member index; assign 1-based group ids;
then apply stack order, soft hints and stacking plans; emit only violator functions.
```

Hard group connectivity is transitive overlapping footprint union, not a proof all edits interact semantically. Nonviolating hub omitted as group member but can appear in plan. Tests two independent groups id1,2; signature caller/callee one group; shared clean hub joins x,y but members only x,y; no flags→[]. Cost DSU traversal plus footprint costs; worst-case recursive find depth initially O(F), no rank, no external rewrite/validation.

### refactor.fix-order.rust — callee-first with cycle fallback

**Source:** [groups.rs](../../rstyle/crates/rstyle-core/src/groups.rs):92–111 `stack_order`; S, consumes group members and call graph.

```text
remaining=sorted unique members;
while nonempty:
 choose smallest m whose every target is m or not in remaining;
 if none: choose smallest remaining m;
remove chosen; append.
```

Index order is source order only if input facts already merged; public groups API itself does not merge. Targets outside group impose no order. No SCC condensation. O(group_size² × inspected call incidence). Tests callee before caller, cycle a,b fixed ascending.

### refactor.soft-hints.rust — shared type/caller hints

**Source:** [groups.rs](../../rstyle/crates/rstyle-core/src/groups.rs):19–21,113–187 `soft_items`, `hints_for`; S.

```text
per group types=union mutated_types for members violating mutation_per_target/mutated_targets;
callers=union immediate callers OUTSIDE group of density violators;
for each type shared by other groups: Hint(shared_type,type,other-group count);
for each caller: collect groups listing same soft caller plus its violating-owner group;
 remove current group; if nonempty Hint(shared_caller,caller.name,number of groups);
sort(-other_groups,kind,item); truncate5.
```

Shared types/callers do not union groups; names may collide in displayed caller item. O(groups² × soft set scans), O(soft items). Tests shared Account produces2 independent groups+hint count1; fixed caller elsewhere produces shared_caller count1. Five-hint cap source verified, not directly tested.

### refactor.argument-forwards.rust — positional provenance

**Source:** [stacking.rs](../../rstyle/crates/rstyle-core/src/stacking.rs):21–65 `all_sites`, `forwards`, `key`; S through plans.

```text
expand every resolved Callee target into Site(caller,callee,args);
for each args[to] in order where to<callee.param_list.len:
 if ArgSource::Param(from) && from<caller.param_list.len: emit(from,to);
 else skip;
callee item identity=(param.name,param.ty) textual key.
```

Trait call expands per target, so these are target-expanded counts, not necessarily physical site counts. No Const/Field/Other bundle item. Missing args or param_list yields no evidence; absent uses=0 affects pass-through separately. O(target-expanded args). Tests [(2,0),(0,2)] and out-of-range input reduces to[(0,1)].

### refactor.closed-parameter-bundles.rust — one-round closed itemsets

**Source:** [stacking.rs](../../rstyle/crates/rstyle-core/src/stacking.rs):67–142 `closed_sets`, `bundles`; S/L via plans.

```text
per_site=set of (callee-param-name,type) for forwarded arguments;
candidate_sets=all input sets plus EVERY pairwise intersection (one round only);
keep size>=2; support(set)=number of original per_site sets containing it;
drop candidate if strict candidate superset has equal support;
for each kept set: params ascending; sites=support;
 functions=sorted unique caller and callee DISPLAY names of supporting sites;
sort bundles(-param count,-sites,functions), stable ties inherit candidate-set order.
```

Not exhaustive intersection closure: three-way intersection not produced by any input/pair may be absent. No min support>1; name+type collapse duplicate parameter positions. Repeated target-expanded sites increase support. Source `norm`/compiler type equivalence not used. Cost candidates O(S²), closure filtering O(K² × set size), support O(K S × set size), K≤S+S(S−1)/2; memory O(K × items). Tests identical abc→(abc,2), abc/abd/ab retain ab support3 plus size3 sets; abc +ab gives bundle sizes/sites[(3,1),(2,2)], singleton/empty→none. **Fixture design:** abcXY,abcXZ,abcYZ produce triple-only abc absent from one-round candidates.

### refactor.pass-through-parameters.rust — mentions versus forwards

**Source:** [stacking.rs](../../rstyle/crates/rstyle-core/src/stacking.rs):145–159 `pass_through`; S plan step, only sites into changed callees.

```text
forwarded[from] +=1 for every valid forward at sites with this caller;
iterate caller.param_list in declared order;
emit name iff uses>0 && forwarded[from]>=uses.
```

Not equality test, not ownership proof; trait target expansion can exceed real mention count. Old facts uses0 never emit, even if forwarding vector exists. O(site args + param count), O(params). Tests a uses1 forward1 emitted, b uses2 forward1/c unforwarded not; unused abc0 none.

### refactor.stack-plans.rust — signatures then touched sites

**Source:** [stacking.rs](../../rstyle/crates/rstyle-core/src/stacking.rs):162–240 `Ctx::step`, `plan`, `plans`; S called by groups.

```text
changed=group members with rule fn_params; empty -> None (even other caller_rules configured);
feeding=ALL target-expanded sites into changed callees;
touched=sorted union feeding caller indices and other members, excluding changed;
steps = changed signatures in supplied callee-first member order, then touched ascending;
per step: incoming_sites=count ALL targets at this callee;
 outgoing_sites=count this caller's sites into changed;
 pass_through=preceding record using feeding;
bundles=preceding closed itemset record using feeding; return StackPlan.
```

Calls beyond immediate callers of changed methods do not recursively enter plan unless also members/changed. Grouping caller_hops and custom caller_rules do not redefine changed-set rule. No source edits, compile validation or borrow-checking. Tests leaf/mid/top signatures all ordered; leaf-only plan callee signature then mid call-sites with counts(1,0),(2,1), top excluded; unrelated flags→None. Cost rescans sites per plan step plus bundles.

## Signature/type and preprocessing stages

### patterns.signature-normalization.rust — positional variables and Self

**Source:** [shape.rs](../../rstyle/crates/rstyle-core/src/shape.rs):10–175 `Namer`, `variable_ids`, `normalize`; P/L, also graph call labels. Input SigFacts; output key,vars.

```text
traverse param types THEN return in pre-order;
if Adt.id==self_ty: hide children; Self substitutes entire type including own args;
if other Adt crate first segment not core/alloc/std: record id once in first-use order;
variables index0..: A..Z,A1..Z1,...;
render:
 Self for own ADT; nominal std/core/alloc ADT short last-segment name;
 other ADT variable name; append <rendered args> except Self;
 Ref preserves &/&mut; Tuple "(a, b)"; Slice "[x]"; Array "[x; _]";
 Prim exact; Param "T{index}"; FnPtr "fn"; Dyn "dyn {short(id)}";
 Opaque "impl _"; Other "_";
receiver prefix None / Self / &Self / &mut Self / "self: _";
qualifiers ordered const,async,unsafe then "fn" and optional "<generics>";
key="{qualifiers}({receiver+params comma-space}) -> {ret}"; vars=distinct count.
```

Lifetimes, array lengths, fn pointer signatures and dynamic trait args unavailable. Nominal path shortened can collide across std modules. Nonstd external ADTs alpha-renamed too, not just workspace ones. O(type tree size × distinct vars) because Vec membership/lookups; recursion stack type depth. Tests pin strings and4 receiver classes; equal repeat vs distinct params A/A vs A/B; Vec<u8> vs String nominal distinction; Self return. No general semantic equivalence from equal key.

### graph.type-classes.rust — coarse initial parameter types

**Source:** [shape.rs](../../rstyle/crates/rstyle-core/src/shape.rs):177–196 `class_of`; P/WL/L.

```text
render nominal ADT by short name and recursively coarse args;
EVERY nonnominal ADT -> "_" WITHOUT its args;
Ref,Tuple,Slice,Array,Prim,Param,Dyn render as above;
FnPtr,Opaque,Other all "_".
```

Different abstraction policy from signature normalization (FnPtr here `_`, signature `fn`; opaque `_` vs `impl _`). No Self substitution. O(type tree traversed). Test &[Dog]/&[Cat]→`&[_]`, String retained. **Fixture design:** nonstd Wrap<u8> vs Wrap<bool> same coarse class but different normalized signature argument structures.

### facts.type-differences.rust — corresponding ADT ids only

**Source:** [shape.rs](../../rstyle/crates/rstyle-core/src/shape.rs):198–221 `zip_children`, `adt_diffs`; P alignment holes/L.

```text
if both ADTs and ids differ: emit ONE(idA,idB); STOP below that node;
otherwise recurse paired children:
 ADT args zip; tuple children zip; same Ref/Slice/Array inner;
all other pairs no differences.
```

Zip ignores extra trailing children; ref mutability, primitive changes and mismatched type shapes produce no Type hole. Even differing nominal std ADTs can be holes. O(smaller paired tree), recursion depth stack. Test &[Dog]/&[Cat] emits Dog/Cat; identical String none. **Fixture design:** &T vs &mut T no ADT hole; differing outer Wrap ids suppress inner differences.

### patterns.signature-groups — buckets, owners and rarity

**Source:** [facts.rs](../../rstyle/crates/rstyle-core/src/facts.rs):212–228 `SigFacts::owner`; [sigmine.rs](../../rstyle/crates/rstyle-core/src/sigmine.rs):36–126 `buckets`, `build`, `sorted`, `specificity_milli`, `mine`; P/L.

```text
owner(sig)=self_ty or None; concrete args=self_args except TOP-LEVEL Param variants;
 append rendered concrete args if any (position of filtered params lost).
for facts with sig AND owner: bucket normalize(sig).key with Member and traited flag;
total=sum RAW bucket lengths (including single-owner and traited methods);
per bucket:
 partition implements-present from inherent; sort Member derived fields
  (path,line,id,name,self_ty); adjacent dedup_by equal id within EACH list;
 owners=unique inherent owner strings; if <2 -> no group;
 specificity=round(1000*ln(total/max(inherent.len+traited.len,1))), floor at0;
 shared=max distinct inherent owners with same last method name;
 same_name=shared>=2;
 boost=if same_name then floor(floor(specificity/2)*shared/owner_count) else0;
 score=specificity+boost;
sort(-score,key).
```

Adjacent id dedup after location-first sorting is not global id dedup when repeated id entries are separated; total remains prededup. Trait methods counted in base rate but not proposed members; missing sig/owner omitted. Free functions with supplied owner-less signature excluded. Owner includes concrete arguments so same ADT different u8/u16 can count as2 types; generic Param-only args collapse. Cost O(F log F+type normalization); f64 log/round boundary not pinned against all platforms. Tests specify two inherent owners minimum,4-of4 specificity0, same-name half boost and2/3 scaling, rare over getter, reverse-order equality fixture.

### patterns.prepare.rust — abstraction/generation filtering

**Source:** [prep.rs](../../rstyle/crates/rstyle-core/src/prep.rs):77–102 `generated`, `prepare`; P before signature and body miners; L.

```text
active=facts in supplied order, dropping valid allow(abstraction) and any id path
 segment exactly "_" OR starts "_#";
build impl lookup from ACTIVE facts; devirtualize each present PDG;
return cloned facts preserving all other fields/order.
```

Filtering all anonymous-const-like IDs is textual, not provenance checked. Suppressed implementations are removed before lookup and rarity counts. No Config.exclude here. Tests drop `_`/`_#1`, retain `_x` and ordinary modules, valid abstraction comment removes function. O(fact+PDG cloning + lookup). **Fixture design:** same target/gen path excluded in S but retained by P unless another prep guard.

### patterns.devirtualization.rust — static receiver ADT lookup

**Source:** [prep.rs](../../rstyle/crates/rstyle-core/src/prep.rs):23–75 `impls`, `peel`, `receiver_adt`, `devirtualized`; P via prepare.

```text
table[(implements,self_ty)]=FnFacts for functions with both and sig;
 duplicate key LAST fact wins; no self_args key;
for Call node:
 find FIRST incoming Data edge with arg_pos0;
 get producer type; peel all Ref wrappers;
 if Adt.id known and (call.callee_id,adt.id) in table:
  replace callee_id by impl id, callee_sig by impl sig;
 otherwise unchanged; retain nodes' other fields and all edges.
```

No receiver generic specialization/dyn call completeness, no rewrite of FnFacts.edges (style graph remains multi-target). Multiple same-ADT impl args can overwrite each other. Test Cow trait call resolves Cow impl. O(V E+lookup+cloning), receiver edge scan linear. **Fixture design:** two concrete generic impls same trait and ADT overwrite by input order.

### patterns.trait-hiding.rust — evaluation oracle

**Source:** [prep.rs](../../rstyle/crates/rstyle-core/src/prep.rs):9–21 `hide_implements`; P opt-in options.hide_implements; CLI repeatable flag.

```text
after prepare/devirtualization: for each f.implements:
 if any pattern=="*" or implements.contains(pattern): clear implements;
keep PDGs already rewritten and all other facts unchanged.
```

This is not removal of all trait knowledge; devirtualized node signatures/ids remain. Empty pattern matches every trait id; no glob except literal `*`. O(F × patterns/string search). Test Speak hides only matching, then `*` hides remaining Other. Useful oracle but not evidence of real undiscovered traits.

## Graph canonicalization — independently changeable rewrites

### graph.normalize.pipeline.rust — flags and actual order

**Source:** [normalize.rs](../../rstyle/crates/rstyle-core/src/normalize.rs):16–106 `Rules::parse`, `canonicalize`; P-O `cluster::Params.normalize`, L/T. Default ALL FLAGS FALSE; CLI `--normalize`, no Config table.

```text
parse comma-separated trimmed nonempty names from false flags:
 all sets ALL; ctor,pred,case,exit,counter,cmp set named flags;
 try sets propagate; unknown -> Err; repeats allowed; "" identity.
clone PDG; enabled passes in EXACT order:
 propagate_errors -> fold_ctors -> collapse_preds -> unify_case ->
 drop_unreachable -> counter_loops -> compare_class.
```

Contrary to `R1,R2,...` order comment, propagation R8 runs first so ctor op/Match guards still exist. Single pass except helper recursive else-if flattening; no global fixpoint. Canonicalization precedes pair-size/call floors so shrinking can remove eligibility. Tests parse exact names, default identity, ALL finite-fixture idempotence; not proof for arbitrary cyclic PDGs. Cost sum of following stages, plus full clone.

### graph.normalize.remove-nodes.rust — stable compaction and edge dedup

**Source:** [normalize.rs](../../rstyle/crates/rstyle-core/src/normalize.rs):110–162,701–704 `data_producers`, `data_consumers`, `without`, `dedup`, `rewire`; all normalization consumers.

```text
producers(n)=incoming Data.from in ORIGINAL edge order, duplicates retained;
consumers(n)=set outgoing Data.to;
without(dead): assign live nodes new dense indices in old order;
 remove every edge touching dead; rewrite retained indices, same kind/arg_pos/order;
dedup(edges): retain FIRST tuple(from,to,kind,arg_pos); no sorting;
rewire(extra,dead): dedup(original edges followed by extra), then without(dead).
```

No generic bypass/edge splicing on deletion. Indexing new_index[e.from/to] panics for invalid index (unlike WL adjacency). Duplicate data edges may prevent `[one]` guards even though consumer sets collapse them. Finite fixture test rewritten indices valid; no input validation. O(V+E log E), O(V+E).

### graph.normalize.error-propagation.rust — shaped match to Try

**Source:** [normalize.rs](../../rstyle/crates/rstyle-core/src/normalize.rs):547–597 `propagations`, `propagate_errors`; pipeline FIRST iff try=true.

```text
for Match m in node order:
 arm_targets=set of all outgoing Ctrl.to, IGNORING arm positions;
 require EXACT2 distinct targets c,r (ascending); swap if c is Return;
 require c=Op detail ctor OR tuple, r=Return;
 require producers(c)==[m], consumers(c)=={r}, producers(r)==[c];
record(m,c,r);
relabel m Try; delete c,r and incident edges; retain all other node fields.
```

No inspection that constructor is Err, match type is Result or first arm yields Ok; ctor tuple also accepted. No requirement both ctrl targets same arm, no return non-locality proof. Negative tests add other controlled work or change return producer → unchanged. Positive explicit fixture gives Param,Try,Macro and edges0→1→2; repeated pass identical, shrinks. Cost O(V E), no recursion. **Fixture design:** non-Result Match with tuple+Return wired as guard also becomes Try.

### graph.normalize.constant-constructors.rust — fold owned literal trees

**Source:** [normalize.rs](../../rstyle/crates/rstyle-core/src/normalize.rs):166–257 `constant_tree`, `constant_root`, `built_from`, `fold_ctors`, `as_ctor`; iff ctor=true then nested pass below.

```text
ctorOp(n)=Op && detail in {ctor,tuple};
valueLeaf(n)=Lit && callee_id=None;
constantTree(n)=ctorOp(n) AND every Data producer p has consumers(p)=={n}
 and (valueLeaf(p) OR constantTree(p)); zero-input ctor qualifies;
root=constantTree(n) AND no consumer itself constantTree;
for roots ascending: descendants=recursively all Data producers plus self;
 dead=all descendants except roots;
redirect incoming Ctrl edges to absorbed descendants to owning root (preserve arg_pos);
relabel roots Ctor; also relabel unit-variant literals Ctor:
 Lit/path/no callee id, last :: segment first char uppercase and any lowercase;
preserve root detail/type/etc; dedup original+redirected edges; compact dead;
then graph.normalize.nested-constructors.rust.
```

`built_from`/constant recursion has no cycle guard/memoization; behavior/cost on cyclic constructor data unresolved, may not terminate. Literal text inside the tree is removed; root `detail` may only say `ctor`, not encode the full value. Ctor details are not holes in alignment. A path constant `LIMIT` stays Lit; `Mode::Fast` becomes Ctor by naming heuristic. Tests pin nested literal constructor→Ctor,Return with one edge, control redirection, shared literal not absorbed. Cost unknown for arbitrary cyclic graphs; repeated recursive edge rescans on trees.

### graph.normalize.nested-constructors.rust — nonconstant constructor splicing

**Source:** [normalize.rs](../../rstyle/crates/rstyle-core/src/normalize.rs):260–297 `splice_nested`; ctor pass, after constant fold.

```text
inner={n: ctorOp(n) && exactly1 distinct Data consumer && that consumer ctorOp};
parent_of(n): follow sole consumer while current in inner; no cycle check;
for edges in order:
 if Data into inner and NOT from inner: redirect to outermost parent, keep arg_pos;
 else if NOT into-inner-Data and NOT from inner: keep;
 else drop;
dedup; remove inner nodes and touching edges.
```

Control into removed inner constructors is dropped, not lifted by this stage. Outermost nonconstant node remains Op (`ctor`/`tuple`), not Ctor. Operand positions may collide when merging multiple levels. Test Call→ctor→ctor→Return reduces to Call,Op,Return and chain edges. Cycles can loop in parent_of; cost unknown generally; O(VE) scans plus chain walks for acyclic fixture.

### graph.normalize.predicates.rust — discard boolean combinators

**Source:** [normalize.rs](../../rstyle/crates/rstyle-core/src/normalize.rs):301–378 `predicate_tree`, `leaves`, `collapse_preds`; pred opt-in.

```text
combinator=Op with detail &&,||,!;
trees={combinator n whose ALL Data producers are Call or recursive predicateTree};
roots=trees with Data consumers disjoint from trees;
leaves(root,neg): traverse producers; flip neg iff current.detail=="!";
 recurse into combinators; emit other producer (normally Call) with current flip;
negated=set call leaves with ANY odd-negation occurrence;
set each negated node.detail="!" (replace prior detail);
for each root outgoing Data edge, each leaf: add leaf→same consumer,arg_pos=0;
dedup original+new; remove ALL tree nodes/incident edges.
```

No guard call returns bool, no ownership/single-use requirement, no short-circuit semantics preserved. AND vs OR erased; shared call negated in one tree marks all uses. Incoming control to removed combinators not transferred. Empty-input combinators vacuously qualify. Recursion no cycle detection; general cost unknown. Tests negated pair→two Call nodes and Branch with Data arg0 each; `!` retained as call detail but **not** compared as a hole by alignment; noncall literal combinator unchanged. **Fixture design:** same predicate calls with && vs || yield identical canonical structure and no boolean-operator hole.

### graph.normalize.if-let.rust — Let contraction

**Source:** [normalize.rs](../../rstyle/crates/rstyle-core/src/normalize.rs):388–413 `contract_lets`; first helper of case opt-in.

```text
pairs=every Data edge Let→Branch in edge order;
branch_of(let)=first pair's Branch;
for each edge:
 if from contracted Let and to its Branch: drop (ANY kind);
 else if from contracted Let: redirect from=Branch;
 else if to contracted Let and Data: redirect to=Branch;
 else if to contracted Let and nonData: drop;
 else keep;
dedup; remove paired Let nodes.
```

No single-consumer/ownership guard; one Let feeding several Branches maps to first. Test if_let vs two_arm_match yields same nodes/edge set under case rules; no generalized semantic assertion. O(E²+V) due to pair scans. **Fixture design:** one Let feeding two Branches exposes first-edge-order mapping.

### graph.normalize.literal-scrutinees.rust — equality pattern erasure

**Source:** [normalize.rs](../../rstyle/crates/rstyle-core/src/normalize.rs):417–449 `literal_scrutinees`; second case helper.

```text
for Branch b: require producers(b)==[op]; inputs=producers(op) in edge order;
require EXACT2 inputs; prefer first input if valueLeaf, otherwise second if valueLeaf;
require op=Op/detail"==", literal consumers={op}, op consumers={b},
 other operand NOT valueLeaf;
add other→b Data arg0; remove op,literal and touching edges; dedup/compact.
```

Literal value/condition equality removed rather than kept as Literal/Op holes. Ctrl into removed comparison/literal dropped. Different literals collapse same scrutinee; inequality is not handled here. O(VE), O(V+E). Positive literal_chain case test; changed scrutinee stays two Cases. **Fixture design:** `x==1` vs `x==2` canonical comparisons have no literal hole.

### graph.normalize.case-labels.rust — Branch/Match to Case

**Source:** [normalize.rs](../../rstyle/crates/rstyle-core/src/normalize.rs):382–384,501–521 `relabel_cases`, `unify_case`; case opt-in, after contraction/equality removal and before flattening.

```text
for every Branch or Match: replace kind with Case; keep all other node fields/edges;
then flatten_else_if.
```

No semantic branch/match exhaustiveness or pattern compatibility validation. Raw Match needed by error propagation and dispatch; dispatch later examines raw prepared PDGs, not this canonical graph. O(V). Test ordinary bool branch retains its condition edge and becomes Call,Case.

### graph.normalize.else-if.rust — same-scrutinee tail flattening

**Source:** [normalize.rs](../../rstyle/crates/rstyle-core/src/normalize.rs):451–499 `arms_of`, `else_if`, `flatten_else_if`; case opt-in tail.

```text
find FIRST parent Case in ascending node index:
 last=max outgoing Ctrl.arg_pos; tail targets at last arm must be EXACTLY ONE child;
 require child Case; parent producers nonempty and EXACT ORDERED producer vectors
 equal child's; child's Data consumers empty;
remove all edges to/from child;
lift outgoing child Ctrl edges to parent with arg_pos=last+child.arg_pos;
dedup; delete child/compact; recursively repeat until no match.
```

Producer equality depends on edge order; tail target count includes duplicates. Child may have additional incoming control owners; deleting child deletes those relationships. No cycle guard other than shrink per successful step. O(V²E) conservative bound across ≤V flattenings. Tests literal chain same graph as match; different scrutinee remains nested. **Fixture design:** identical producer sets with reversed Data edge order do not flatten.

### graph.normalize.unreachable.rust — textual no-input macro removal

**Source:** [normalize.rs](../../rstyle/crates/rstyle-core/src/normalize.rs):526–541 `drop_unreachable`; exit opt-in.

```text
dead={Macro n: macro_name contains "unreachable" AND producers(n) empty};
remove dead/incident edges.
```

Despite comment, no after-loop, reachability or returns guard. Removes any matching macro anywhere, including custom name substring. O(VE). Test no-input unreachable macro removed, same macro with Param Data input unchanged. **Fixture design:** custom `not_unreachable_helper` macro without Data inputs deleted too.

### graph.normalize.range-loops.rust — literal ranges

**Source:** [normalize.rs](../../rstyle/crates/rstyle-core/src/normalize.rs):601–661 `range_loops`; counter opt-in first helper.

```text
for Iterate i: producers(i)==[call]; bounds=producers(call);
require callee_id contains "ops::range::" (NO Call-kind check);
require bounds.len==2; each bound=Lit/no callee/int and consumers={call};
require consumers(call)=={i};
relabel i Loop; detail=bound details in EDGE order joined "..";
remove call and bounds; no control lifting; retain iterate other fields.
```

Inclusive/exclusive range distinctions not encoded in detail. Bounds become no Literal holes because removed. Shrinks away a Call and may fail mining call floor. O(VE), O(V+E). Tests two-node Loop,Call and detail1..3; collection loop unchanged, nonliteral bound stays Iterate.

### graph.normalize.manual-counters.rust — init/step deletion

**Source:** [normalize.rs](../../rstyle/crates/rstyle-core/src/normalize.rs):664–728 `enclosing_loop`, `manual_counter`, `manual_counters`; counter second helper.

```text
for every node step:
 find FIRST incoming Data arg_pos0 amount, FIRST arg_pos1 init;
 walk FIRST incoming Ctrl edges up at MOST4 hops; stop at Loop;
require step Op detail "+=" OR "+==";
require amount and init int value leaves; amount consumed ONLY by step;
require step no Data consumers; no init ownership requirement;
collect(step,init,amount,loop);
for each Data edge from any init not into ANY found step:
 add edge from FIRST associated loop, preserving destination/position;
remove all found step/init/amount nodes; dedup/compact.
```

No check amount==1, no sign/bounds proof, no primitive counter mutation semantics validation. First control-parent order and4-hop cap decisive; multiple steps sharing init use first loop. O(VE), O(V+E), capped ancestry walk. Test manual while matches range **kinds/edges**, not node details or program behavior; step uses fixture `+==`. **Fixture design:** step2 with same shape still deletes;5-level nesting remains unrecognized.

### graph.normalize.loop-guards.rust — sole live arm guard removal

**Source:** [normalize.rs](../../rstyle/crates/rstyle-core/src/normalize.rs):732–775 `loop_guards`, `counter_loops`; counter final helper, after range then manual.

```text
for g: first incoming Ctrl.from owner;
require g Case OR Branch, owner Loop, producers(g)==[op];
inputs(op) EXACT2, include owner; find int valueLeaf bound;
require op Op/detail one of <,<=,==,>=,>,!=;
require bound consumed only by op; op only by g;
require EVERY outgoing Ctrl from g has arg_pos0 (zero arms vacuously true);
lift g's Ctrl body edges to owner unchanged arm position;
remove g,op,bound and touching edges; dedup/compact.
```

No actual while provenance or exit checks. Guard expression erased, comparison/bound details not copied to Loop by this helper. O(VE). Tests manual while/range edges agree; compare tests without owning Ctrl guard only relabel comparison via next stage. **Fixture design:** different guard bounds/operators disappear under this shape.

### graph.normalize.counter-comparisons.rust — operator class with holes

**Source:** [normalize.rs](../../rstyle/crates/rstyle-core/src/normalize.rs):779–796 `compare_class`; cmp opt-in after counter.

```text
for Op/detail in six comparisons:
 require EXACT2 Data producers, any Loop and any int valueLeaf;
replace detail with "cmp:"+old operator; leave edges/type/other fields;
```

No bound ownership or enclosing-loop check here. `wl::label` sees only `op:cmp`; alignment reports suffix as Op hole. Already-prefixed comparison does not match raw set, so second pass unchanged. O(VE). Test `<`/`==` edges/labels agree but details cmp:< /cmp:== survive; noncounter Param unchanged; align test gives O0 `<`→`==` with full coverage.

## WL and matching

### graph.initial-labels.rust — text labels and missing signatures

**Source:** [wl.rs](../../rstyle/crates/rstyle-core/src/wl.rs):41–111 `call_class`, `label`, `edge_tag`, `adjacency`, `graph`; P/L/T.

```text
call_class=normalize(callee_sig).key if present, else callee_id if present, else "?";
node label:
 Call "call:"+call_class; Macro "macro:"+(macro_name or "");
 Lit "lit:"+(lit_kind or ""); Op "op:"+detail before FIRST ':';
 Param "param:"+(coarse type class or ""); other kinds Rust Debug variant name;
labels=FNV(label UTF8);
edge tag=combine(int(kind==Ctrl),arg_pos as u64);
adjacency: only edges with BOTH endpoints<V; append tagged neighbors in edge order;
keep duplicates, self-loops, incoming/outgoing separate.
```

Comment saying names absent has exceptions: missing signature falls back to full callee id, macro names included, ordinary Op detail included (e.g. `+` vs `-`). Nonparam node value types not in labels. Kind `Field`, `Ctor`, `Case` have generic kind-only labels. O(V label/type rendering+E), O(V+E). Tests getter label `call:fn(&Self) -> String`, Dog/Cat round equality, receiver signature change alters label.

### graph.hash-encoding.rust — deterministic lossy hash identity

**Source:** [wl.rs](../../rstyle/crates/rstyle-core/src/wl.rs):12–39 `fnv1a`, `combine`; P/L/T and ledger IDs.

```text
FNV_offset=0xcbf29ce484222325; prime=0x00000100000001b3;
fnv(bytes): fold (hash XOR byte) wrapping_mul prime, u64;
combine(acc,value): FNV fresh offset over acc.to_le_bytes() THEN value.to_le_bytes();
```

Not seeded LSH/equality-preserving interning; hash collisions accepted as label equality, no collision verification. Platform-stable byte layout explicitly little-endian. O(bytes) and O(1) combine. Golden tests empty offset, `a`→0xaf63dc4c8601ec8c, combine order differs1,2 vs2,1; no universal collision guarantees.

### graph.wl-refinement.rust — directed tagged multiset digest

**Source:** [wl.rs](../../rstyle/crates/rstyle-core/src/wl.rs):114–138,173–218 `digest`, `refine`, `histogram`, `Wl::new`; P/L/T.

```text
rounds=[raw labels]; repeat3 refinements (MAX_LEVELS=4 including zero):
 for v using preceding round:
  inparts=sort_u64(combine(edge.tag,prev[neighbor]) for incoming edges);
  inward=fold(combine(prev[v],0x1f),inparts,combine);
  outparts=sort_u64(combine(edge.tag,prev[neighbor]) for outgoing edges);
  new[v]=fold(combine(inward,0x2e),outparts,combine);
hists[k]=ascending(color,count) BTree histogram of each round;
calls=count ORIGINAL PdgNode.kind Call; graph adjacency+rounds+hists retained;
compute diameter separately.
```

Duplicates contribute multiset multiplicity, direction/arg positions matter, no early refinement fixpoint and no light WL instance in core. Cost O(4×(V+Σdegree log degree)); space O(V+E+4V). Finite rotation/independent disconnected statements tests score1000, not semantic equivalence.

### graph.wl-depth.rust — undirected finite-component diameter

**Source:** [wl.rs](../../rstyle/crates/rstyle-core/src/wl.rs):140–171,213–217,232–239 `eccentricity`, `diameter`, `levels`, `weights`; P/L/T.

```text
if V>400: diameter=4 (no BFS);
else diameter=max BFS eccentricity from every node using incoming+outgoing neighbors;
 seen/frontier per start; disconnected nodes unreachable from start ignored; empty→0;
h=(min(diamA,diamB)+1).clamp(1,4);
comparison colors=rounds[h-1]; weights at levels0..h-1 = h,h-1,...,1.
```

Direction respected in refinement but ignored for diameter. Disconnected graph diameter=max finite component, all isolated→0 (only raw score despite all4 precomputed rounds). Large graph shortcut forces4 when paired with another diameter≥3; threshold boundary exactly400 BFS,401 shortcut. Cost diameter O(V(V+E)log V) with BTree frontier upper bound for≤400; O(1) shortcut; O(V) BFS memory. Weights test pins[4,3,2,1]/[1]; edge/disconnected/400 boundary fixtures untested. Comment `CCGraph uses10` not verified paper evidence.

### patterns.wl-similarity.rust — weighted histogram intersection over max size

**Source:** [wl.rs](../../rstyle/crates/rstyle-core/src/wl.rs):241–268 `intersection`, `similarity_milli`; P/L/T.

```text
h=wl-depth; intersect two SORTED histograms by merge:
 equal color adds min(countA,countB); no cross-product;
num=sum((h-k)*intersection(histA[k],histB[k])) for k=0..h-1;
den=sum(h-k)*max(VA,VB); // u64 ordinary arithmetic
return ((num*1000).checked_div(den).unwrap_or(0)) as u32;
```

No comparability check inside similarity; no second verification with smaller denominator; no cosine/string characteristic vector stages. Empty/empty→0, identical nonempty→1000 subject hashes; floor, not round. Cost O(h×distinct histogram entries), O(h) weights. Unrelated audit Call fixture has800≤score<1000; changed receiver reduces score. **Fixture design:** histogram A x:2,B x:3 →intersection2 not6; four same-label isolated nodes vs eight same-label →500 under max denominator, not1000 smaller denominator.

### patterns.pair-gates.rust — normalized node/call floors and ratio

**Source:** [wl.rs](../../rstyle/crates/rstyle-core/src/wl.rs):18–25,270–279 `mineable`, `comparable`; P/L/T before pair selection.

```text
mineable(w)=(nodes>=4 && Call count>=1);
comparable(a,b)=mineable(a)&&mineable(b)&&max(nodes)<=2*min(nodes).
```

Inclusive equality, Call only (Macro not counted). Node minimum not source line setting; arithmetic multiplication unchecked. Does not reject zero edges or unknown signatures. Applied after canonicalization in cluster, raw in examples depending tool. O(1) after Wl construction. Tests6-node animals mineable,1-node Call not;13 vs6 rejects;6 vs6 passes. **Fixture design:**4 vs8 inclusive passes;4 vs9 rejects; folded3-node pair no longer mineable.

### patterns.pair-retrieval.rust — exhaustive/rare-class blocking switch

**Source:** [cluster.rs](../../rstyle/crates/rstyle-core/src/cluster.rs):10–16,61–111 `classes_of`, `block_keys`, `candidate_pairs`, `pairs_to_compare`; P/L.

```text
N=number of PDGs (including nonmineable) supplied after canonicalization;
if N<=400: enumerate every a<b into sorted BTreeSet;
else:
 classes[f]=unique Call call_class strings;
 freq[class]=number of FUNCTIONS containing it (not call occurrences);
 sort each function classes by(freq,class text); choose first2;
 build blocks from chosen keys, indices ascending;
 SKIP WHOLE block if length>1000; otherwise generate all a<b members;
 union/dedup pairs into sorted BTreeSet.
```

Potential recall loss before scoring; optional pair coverage cannot rescue unretrieved pairs. Not LSH; no random seeds. Memory O(N²) pairs for exhaustive, block sum squares worst-case; time O(class counting+sorting+Σblock_size² log pair count). Tiny corpus private-class fixture has zero blocked pairs but exhaustive1;401 private-key functions have zero retrieved pairs. Boundary1000 block kept,1001 dropped source-only distinction. Corpora composition can change another pair's retrieval.

### patterns.pair-selection.rust — WL OR optional coverage

**Source:** [cluster.rs](../../rstyle/crates/rstyle-core/src/cluster.rs):113–141 `pair_selected`, `similar`; P default WL threshold600, coverage alternate off.

```text
for retrieved pairs(a,b) sorted:
 if !comparable: reject (neither acceptance branch bypasses floors);
 else accept if similarity>=threshold_milli;
 if not WL accepted and pair_coverage_milli=Some(floor):
   compute BASELINE align; accept coverage>=floor;
add symmetric adjacency sets for accepted pairs only.
```

Inclusive thresholds; no <=1000 validation here. Defaults threshold600,min_coverage600 are independent gates. Positive fixture WL threshold1001 yields no animals cluster, pair_coverage900 rescues1. No numerical/string filter and no AST bypass in this core pipeline. Cost scoring plus align for WL-rejected opt-in pairs; storage O(accepted pairs).

### patterns.alignment.rust — baseline matching and five experimental variants

**Source:** [align.rs](../../rstyle/crates/rstyle-core/src/align.rs):65–349,435–555 `Ctx`, `ordinals`, `seeded`, `pass`, `settle`, `complete`, `prune`, `align_variant`; P BASELINE only, L/T six variants.

```text
Ctx selects pair-supported deepest WL colors; derive DFS ordinal per graph:
 roots with no incoming edges sorted(color,index); then all indices for cycles;
 DFS outgoing children sorted(edge.tag,color,index), visit each once via stack;
ordinals retained at all at_level contexts (not recomputed for raw colors).
Matching empty fwd/back Option arrays; internal links only unmatched endpoints.
seed(color level): link classes with EXACTLY1 node on EACH side, ascending color.
evidence(a,b): for incoming and outgoing edges of a into ALREADY matched nodes,
 count matching b-edge to image with SAME tag (agree) or missing edge(conflict);
reverse_conflicts analogous b→a; duplicate edges counted, existence not multiplicity matching.
best same-color unmatched b: conflict==0 (FORWARD ONLY), max agree, min b ordinal.
pass: visit unmatched a by a ordinal; update matching immediately;
 evidence-backed pass requires agree>0; greedy pass permits0.
settle: repeat evidence-backed passes to no links, then ONE greedy pass if enabled.
prune: repeatedly compute forward+reverse violations for each linked pair;
 remove maximum(count,a index) with count>0, so HIGHEST a index on ties;
 stop when all mirrored; no optimal maximum matching search.
complete: ONE pass a ordinal over unmatched Call/Lit/Field only;
 candidate b unmatched SAME KIND, agree>0,forward conflict0;
 strict variants additionally reverse conflict0;
 choose max agree/min b ordinal; may have different raw/refined label.
Baseline stages:
 seed(deepest),settle(deepest,greedy=true),prune,
 seed+settle(raw,greedy=false),prune_labels,complete(strict=false),final prune.
LabelsOnly: raw grow(false),prune_labels,complete(false),final.
NoFinalPrune: Baseline minus final.
CompleteChecked: Baseline complete(strict=true).
CoarseToFine: for supported levels deepest DOWN TO0:
 seed+settle(greedy=true ONLY deepest),prune;
 then complete(false),final.
Combined: CoarseToFine with strict complete.
output pairs ascending a; coverage=floor(1000*pairs/max(VA,VB,1)) as u32;
output cumulative Stage after each step, then holes_of on final pairs.
```

Name CoarseToFine actually iterates deepest→raw. Public Matching::link does not enforce uniqueness if misused; internal callers do. Partial matching ignores unmatched edges, no semantic/effect safety check. Empty graphs coverage0. Prune may eliminate recoverable pairs and does not rerun matching after final deletion. Cost conservative unknown tight bound; repeated scans of same-color cross products and neighbor lists, ≤VA growth passes, ≤VA prune deletions; memory O(VA+VB+stages×VA). Tests full six animals pairs, symmetry fixture deterministic and edge consistent, conflicting two pairs prune to1, differing signature still completes6, all six variants give coverage1000/2 holes on ONE fixture. Not general variant equivalence. **Fixture design:** same forward neighbors but extra b→matched edge distinguishes unchecked completion/no-final-prune from strict/final pruning.

### patterns.alignment-holes.rust — substitution table

**Source:** [align.rs](../../rstyle/crates/rstyle-core/src/align.rs):13–43,351–433 `callee_diff`, `text_diff`, `type_diffs`, `holes_of`; P/L/T after final pairing.

```text
for final pairs ascending a:
 callee_diff iff BOTH callee_id present and unequal:
  Method iff a.kind Call and EITHER callee_sig.receiver !=None;
  otherwise FreeFn (also fn-item Lit);
 text_diff: a Lit/no callee -> Literal when details differ;
  Field -> Field detail; Op detail starting cmp: and b also cmp: -> suffix Op diff;
 type_diff iff both ty Some: facts.type-differences.rust;
collect BTreeMap[(kind,a_text,b_text)] -> vector node-pair sites;
stable-sort rows(first a-site,kind), tie inherits BTreeMap key order;
name per-kind counters: Type T,Method M,FreeFn F,Literal L,Field D,Op O starting0.
```

No hole for arbitrary Op changes, Ctor text, Case arm patterns, Call negation detail, missing one callee/type, primitive changes, effect differences. `text_diff` cmp path slices b.detail at byte4 before validating b prefix; malformed public input pair can panic (normal internal same-color Op matches ordinarily imply cmp prefix). Repeated exact triple reuses variable, not general unification constraint. Cost O(pairs×type traversal+hole rows log rows); O(hole sites). Tests Dog/Cat T0,M0, Type sites[(0,0),(2,2)]; identical no holes; cmp operator O0; differing return primitive still6 pairs and Method hole. **Fixture design:** canonical constructors with different inner literal values can produce no holes despite observable difference.

### patterns.cluster-construction.rust — seed stars, medoid and membership ownership

**Source:** [cluster.rs](../../rstyle/crates/rstyle-core/src/cluster.rs):143–182,226–279 `next_seed`, `medoid`, `build`, `cluster`; P/L, min coverage600 default.

```text
canonicalize all; Wl all; retrieve/select adjacency;
free=adjacency keys (isolates absent);
while any free vertex with free neighbors:
 seed=max FREE neighbor count, lowest index tie;
 group=sorted free neighbors of seed PLUS seed (star, not clique or component);
 template=member max SUM WL similarity to all other group members, lowest index tie;
  // medoid ignores optional coverage acceptance and uses WL score only
 align template to every other group member (ascending index);
 keep joined member iff coverage>=min_coverage_milli (default600);
 if at least1 joins: cluster.members=[template,kept others ascending];
  covers=[1000,joined coverages]; columns=tabulation record;
  remove ONLY these accepted members from free; append cluster;
 else remove seed only;
return found IN SEED DISCOVERY ORDER (no largest-first sort).
```

Comment says largest first but code does not sort. No requirement joined member met WL threshold against medoid or was retrieved with medoid; preliminary adjacency only against seed. Thus no guaranteed pairwise similarity, nor threshold relation to final medoid. Each function owns at most one returned cluster. Dropped members stay free and may cluster later. Cost medoid O(group²×WL kernel), align per joined; O(canonical graphs+WL+adjacency). Tests animals one cluster[0,1,2],1000 each; padded Hen coverage floor900 excludes,700 admits; unrelated none. **Fixture design:** seed B links A,C, medoid A; A/C need not pass pair threshold yet C can join by coverage.

### patterns.cluster-columns.rust — merge by template value

**Source:** [cluster.rs](../../rstyle/crates/rstyle-core/src/cluster.rs):184–224 `tabulate`, `columns_of`; P/L cluster downstream candidates.

```text
rows[(hole.kind,hole.a_text)] = (minimum template node index, per-joined optional value);
iterate joined members then their holes:
 for each row/member slot keep FIRST hole.b value (later conflicts ignored);
order rows(site,kind,a_text);
values=[template text]+per-member(found value OR template text);
per-kind numbering reused prefixes T/M/F/L/D/O.
```

Different node sites with same template value collapse; a member mapped same template value to two distinct values keeps first. Missing hole is treated as identical template text, not unresolved alignment evidence. Column count not pairwise hole count. O(hole entries log rows), space O(rows×joined). Tests3 animals columns T0 Dog/Cat/Cow,M0 bark/meow/moo,exactly2. **Fixture design:** same template method at two sites mapped to two member methods yields one first-value column.

## Candidate inference, ranking and final filtering

### patterns.candidate-join.rust — trait evidence versus existing abstractions

**Source:** [candidates.rs](../../rstyle/crates/rstyle-core/src/candidates.rs):95–249,470–489,663–756 `Index`, `judge`, `judge_columns`, `from_cluster`, `existing_trait_for`, `from_dispatch`; P/L. Six registered kinds, five produced here; FnParam reserved/unproduced.

```text
Index by_id=last fact per id; groups=by key; workspace_adts=ALL signature self_ty ids;
judge(column.values): wanted=unique sorted callee ids; defs=found wanted in by_id;
 if EVERY resolved def has sig receiver None: Skip (empty vacuously Skip);
 if missing any wanted or <2 distinct sig.owner: Skip;
 if ALL defs same Some(implements): Suppressed(all N impls...,trait,owner set);
 else keys=normalized sigs present; if exactly1 key in signature groups: Trait(group,defs);
 else Skip. Does not require every def has sig beyond two available owners.
from_cluster: sites sorted(path,line,id); judge only Method/FreeFn columns;
 if any Trait verdict:
  kind=TraitMethod if exactly1 verdict else CapabilitySet;
  lift=MIN group.score among verdicts;
  existing_trait=FIRST hidden column whose owners equal FIRST verdict owners;
  finish with ALL cluster columns contributing holes and all sites;
 else hidden_reason=LAST hidden column reason:
  if starts "all ": emit Suppressed for whole cluster;
  if other reason: no output;
  if None: try GenericFn, then Parameterize, otherwise nothing.
from_dispatch: judge arm callee ids;
 Trait -> EnumDispatch(support=arm count,holes1,coverage1000,lift=group score,
  sites=[containing function]); existing verdict -> Suppressed; Skip -> none.
```

Trait candidates have **no** boilerplate/min-call/max-hole exclusion in this branch; can coexist with unjudged/incompatible other columns. Definition Site dedup is BTreeSet, whole candidates not deduped. Existing trait choice does not reconcile all verdict owner sets. Inputs missing definitions/signatures usually Skip; no automatic unknown warning. Cost lookup/normalization plus finishing; tests trait2 defs/support2, no constructors, all same trait suppressed, same-owner extension rather than unrelated last trait, three sites/defs supported. Refactor text is advisory sketch, not a compilable transformation (e.g. qualifier signatures are not comprehensively rewritten by sketch). **Fixture design:** cluster with one valid trait column and an unrelated literal column still proposes trait.

### patterns.enum-dispatch.rust — analogous receiver calls in raw match arms

**Source:** [dispatch.rs](../../rstyle/crates/rstyle-core/src/dispatch.rs):19–61 `arm_calls`, `dispatches_of`, `find`; P after clustering but on RAW prepared graphs (normalization not applied here); L.

```text
for each Match in node order:
 take outgoing Ctrl edges to Call nodes;
 require matching Match→Call Data arg_pos0 (receives matched value);
 require callee_id Some; class=wl.call_class;
 group(class,arm index), FIRST callee per arm retained in edge order;
 keep class if >=2 DISTINCT callee ids (not necessarily all match arms represented);
 emit line=Match.line,class,arms ascending arm index.
```

Does not establish enum type or exhaustive coverage of arms. Same class may use id fallback; Ctrl duplicates collapse at arm map. Case not accepted, but P uses raw PDG here even when cluster normalization all enabled. O(VE²) conservative with receives full scans; O(arm calls). Tests two arms→class fn(&Self)->String and Dog/Cat callee rows; same callee everywhere none. **Fixture design:** a third arm with no qualifying call still allows partial dispatch.

### effects.candidate-compatibility.rust — function facts, penalty not safety gate

**Source:** [candidates.rs](../../rstyle/crates/rstyle-core/src/candidates.rs):251–278,387–417 `effect_class`, `effect_mismatch`, `finish`; P TraitMethod/CapabilitySet/EnumDispatch finish ONLY.

```text
class(def)=set intrinsic f.effects.kind.name plus "mutation" iff any mutation.escapes;
ignore calls, side-effect Config, transitive summaries, weights, delegated-only writes;
uniform iff consecutive def classes all equal;
if not uniform: one counter-evidence message per verdict listing each def+class
 (empty class SHOWN AS "pure"); mismatch flag halves score, DOES NOT reject;
if lift<500: add low-specificity counter evidence.
```

Unknown/missing evidence not distinguished from empty intrinsic set; text `pure` is not a verified purity claim. GenericFn and Parameterize do not call this function or impose any effect compatibility gate. PDG has no effect field. Exact divergent stage relative to style: before classification/propagation, using different evidence subset. O(def intrinsic+mutation facts), O(distinct kinds). Test dirty escaping mutation lowers score and attaches mismatch; does not assert rejection or safety. **Fixture design:** a definition with only CallEvent std::fs::write versus empty calls gets same class despite style IO effect; incompatible intrinsic effects in parameterize sites still not screened.

### patterns.generic-function.rust — type-hole fallback

**Source:** [candidates.rs](../../rstyle/crates/rstyle-core/src/candidates.rs):493–607,612–620 `call_count`, `forwards_params`, `has_substance`, `generic_fn`, `is_boilerplate`; P fallback/L.

```text
if all sites same trait method AND its first :: crate equals FIRST site.id crate: reject;
for EACH site require substantial and not boilerplate:
 substantial=raw PDG Call count>=2; or count1 AND single_call_guard(true opt-in)
  AND at least one call Data input producer NOT Param;
 missing PDG/no calls: false; no-input one-call counts as pure forward, so false;
 boilerplate=id has segment tests,ffi,raw or starts bindgen; final segment main;
  OR path starts tests/ or contains /tests/;
partition columns into Type and others;
require SOME Type column whose EVERY value is in workspace_adts;
require ALL other columns Method/FreeFn with EVERY value absent from by_id;
create GenericFn, lift0,score=ranking(false)/2 (INTEGER division),
 no definitions/no counter evidence; display ALL Type holes, including external ones.
```

`workspace_adts` means types with signature self_ty facts, not a crate-membership oracle. Generic branch has no max_holes limit and permits all-impls of an **external** trait (unlike parameterize). Uses raw Call count despite normalized cluster possibly deleting calls. Tests type-only2 sites emits generic/lift0/half score; test code and one-call default skip, opt-in Iterate input admits1 candidate but Param input still none; external-only Type not generic; literal/workspace callee holes not generic; external trait emits while same-site-crate trait skips. O(sites×(V+E)+columns×values), no extraction safety validation.

### patterns.parameterize.rust — limited-hole fallback helper suggestion

**Source:** [candidates.rs](../../rstyle/crates/rstyle-core/src/candidates.rs):624–660 `parameterizable`, `parameterize`; P after generic fallback/L.

```text
reject same workspace trait method (as generic branch);
reject ALL sites implements-present (even different trait methods), ANY boilerplate,
 columns.len>max_holes(default3), or ANY not substantial (same raw-call guard);
else Candidate Parameterize, lift0,score=ranking(false)/3 floor;
 holes0 text "nothing (exact clone)"; otherwise describe columns;
 definitions=[],counter_evidence=[]; no effect screening.
```

No required hole kinds, no compile/borrow/lifetime/source rewrite; inferred sameness exceeds what approximate partial alignment establishes. Exact clone permitted if nonboilerplate/substantial. Test external callee A/B emits1 Parameterize and third score; tests/trait forcing skip;4 holes reject cap3,admit cap4; main/raw/ffi/bindgen boilerplate true. O(site guards+columns). **Fixture design:** two substantial bodies same normalized shape differing unsafe/IO effects still eligible; disappearance of ctor literals can produce zero-hole helper suggestion.

### patterns.candidate-ranking.rust — support/lift/coverage with penalties

**Source:** [candidates.rs](../../rstyle/crates/rstyle-core/src/candidates.rs):281–290,547–555,805–819 `score_milli`, `breakdown_of`, `Mined::sorted`; P/L.

```text
support=site count for cluster (or dispatch arm count);
coverage=SUM cluster.coverage_milli / max(member count,1) floor u32;
holes=number of cluster columns; lift=min joined signature-group score or0;
base=(1000*ln(max(support,1))+lift_milli)*coverage_milli/1000 using f64;
if holes>3: base*=3/holes;
if mismatch: base/=2;
score=round(base) as u32 (Rust float cast behavior, no explicit cap);
generic then divides INTEGER score by2; parameterize by3;
sort candidates(-score,Site vector derived order);
stable ties preserve outcome discovery order; suppressed sort(sites,reason).
```

Site derived order path,line,id,name,locator,shape. Sort occurs **before** final locator replacement/id assignment; no sort by candidate id or kind. No score≤1000 guarantee; no candidates-wide uniqueness filter. Coverage sum/medoid total u32 arithmetic may overflow huge synthetic inputs. Tests compare rare/common rank and mismatch penalty; no numeric golden for full ranking. **Fixture design:** holes3 vs4 changes damping; support1,lift0→0; order of same-score identical sites different kinds inherits generation order. Cost O(candidate count log count) plus arithmetic.

### facts.function-locators.rust — stable names with fallback numbering

**Source:** [locator.rs](../../rstyle/crates/rstyle-core/src/locator.rs):12–68 `base`, `assign`, `numbered`; P IDs/ledger status, L.

```text
base(f): find FIRST id segment starts "{impl#";
if absent owner/sig/impl marker: return f.id;
name=all id segments AFTER marker joined ::;
if implements None: owner+"::"+name;
else "<owner as trait-method-id-with-last-segment-removed>::"+name+
 "("+raw rendered params+ ") -> "+raw rendered ret;
assign: sort facts(path,line,id); keep FIRST fact per id via seen set;
count each base; first unnumbered, subsequent #2,#3,...; map by id.
```

Receiver/qualifier flags not in trait signature locator; owner filtering loses Param positions; fallback numbering is source-order dependent. No global collision handling between base strings already ending #2 and generated suffixes. O(F log F+type rendering); tests impl renumber stable, Display vs Debug distinct, generic owners distinct, From<A>/From<B> source swap invariant, identical signatures suffix second by source order, repeated same id not numbered.

### patterns.graph-fingerprint.rust — deepest histogram identity

**Source:** [wl.rs](../../rstyle/crates/rstyle-core/src/wl.rs):220–230 `shape_hash`; [candidates.rs](../../rstyle/crates/rstyle-core/src/candidates.rs):160–171 `site`; P/L/status.

```text
Wl::new(RAW prepared pdg); deepest=hist round3 regardless pair diameter;
hash=FNV_offset; for sorted(color,count): hash=combine(combine(hash,color),count as u64);
Site.shape=Some(format16hex(hash)), None without PDG.
```

Ignores literal values, fields and callee ids when same-signature labels, so shape equality is not body equivalence/change detection. Does not use configured canonicalization; devirtualization can affect raw label when sig replaced. O(WL construction + histogram), no cache sharing with cluster WL. Golden emit_loop hash f440c2186883aa43; rotation/names invariance and structural extra-call difference tested. **Fixture design:** change only string literal text → same shape/id if locator same; ledger may keep dismissal.

### patterns.candidate-identity.rust — truncated FNV of members

**Source:** [ledger/mod.rs](../../rstyle/crates/rstyle-core/src/ledger/mod.rs):189–212 `site_key`, `joined`, `candidate_id`; [candidates.rs](../../rstyle/crates/rstyle-core/src/candidates.rs):758–792 `identified`; P/L.

```text
rename every candidate/suppressed site and definition using corpus-wide locator::assign;
site_key=locator+"@"+(shape OR "-");
site_keys=sort list then join newline (NO dedup);
def_keys=sort definition locator list join newline (NO shape, NO dedup);
text=kind.name+"|"+site_keys+"|"+def_keys;
id=FIRST12 digits of format16hex(FNV1a(text UTF8));
```

48-bit prefix no collision verification. Score, lift, holes, substitution values and definition body shapes absent; membership multiplicity included in hash unlike growth matching sets. No body semantic checksum. Tests id line/member order invariant, shape/members/kind change id, definition shape ignored but membership counted, golden0dafcd1ad065. **Fixture design:** changed substitution literal without shape change keeps id and strict ledger hide. Cost O(member counts log counts+text size).

### patterns.reviewed-ledger.rust — strict and growth filtering

**Source:** [ledger/matching.rs](../../rstyle/crates/rstyle-core/src/ledger/matching.rs):48–163 `matches`, `hiding_entry`, `apply`, `entry_for`, `add`, `prune`; P final filter and CLI ignore/L. Default strict.

```text
matches(id,entry,c): if kinds unequal None;
 if id==c.id: Exact WITHOUT validating stored members;
 else old_sites=set(entry.sites),old_defs=set(entry.definitions);
 current sets=site_key(c.sites),definition locators;
 grew=old_sites subset current_sites && old_defs subset current_defs;
 added=(current_sites.len+current_defs.len).saturating_sub(old total);
 if allow_growth && grew: Exact if added0 else Growth(added); otherwise None;
hiding_entry=min added across matching entries, lexical lowest id tie (BTreeMap order);
apply: partition in ORIGINAL candidate order into kept/hidden; record responsible id/how;
add: replace entry under c.id preserving existing notes;
 strict stores sorted union locators as fns hints ONLY;
 growth stores site keys and definition locator sets; fns=[];
prune: remove entries matching NO candidate in supplied UNFILTERED set.
```

Growth can call equal members Exact even if ids differ; no corroboration of old score/holes/substitutions. Empty old site set possible via public constructed Entry though parse rejects allow_growth empty sites. Cost O(entries×candidates×member set work), no index optimization. Tests strict exact hides only original, growth additions2, removed/reshaped/lost-definition resurrect, split preserving other, reparse still hides, notes retained, prune removes1 gone entry.

### patterns.ledger-schema.rust — version and persisted review contract

**Source:** [ledger/mod.rs](../../rstyle/crates/rstyle-core/src/ledger/mod.rs):15–187 `parse`, `check`, `notes_by_id`, `render`; CLI ignore/status/P load boundary.

```text
TOML deserialize deny_unknown_fields File/Entry; require version==1;
ignore table defaults empty;
id exactly12 LOWERCASE ASCII hex; allow_growth requires nonempty sites;
entry defaults allow_growth=false,reason=None,fns/sites/defs=[],notes skipped by serde;
extract comments: run immediately above entry + comments inside body;
 run above NEXT entry belongs to next entry; unattached comments dropped;
render entries sorted(kind.name,id); sort/dedup each stored list;
 omit false growth,None reason,empty arrays; quote strings via JSON string serializer;
 prepend fixed header+version1; final newline.
```

No site shape/id string format validation, no required reason, no recomputation entry key from members. TOML duplicate-key error external library asserted by test. Cost O(input+list sorting), unknown parser internals. Tests parse strict/growth, invalid version/id/unknown/duplicate/no-growth-sites, deterministic round-trip, quote/backslash preservation, comments following documented ownership (a so-called floating comment directly above entry IS kept). Rendering secondary but persistence semantics audited.

### patterns.ledger-status.rust — advisory current members

**Source:** [ledger/status.rs](../../rstyle/crates/rstyle-core/src/ledger/status.rs):46–152 `current`, `recorded`, `member`, `new_members`, `status`; CLI ignore --status caller, L. Does not change analysis candidates.

```text
current locator map from assign(facts); each record location and RAW graph hash optional;
recorded site string rsplit_once('@'):
 if suffix!="-": locator=prefix,shape=suffix;
 ELSE keep WHOLE site string as locator with None shape;
append plain fns and definitions with no shape; duplicates retained;
member: locator absent Gone;
 present+recorded shape AND current Some DIFFERENT hash -> ShapeChanged;
 present+recorded shape otherwise Unchanged (even current shape None);
 present without recorded shape -> Found;
active=any matches(entry,candidate);
if stale: choose candidate with maximum nonzero locator overlap, LAST on ties,
 WITHOUT kind restriction; new_members=sorted candidate locators minus recorded;
return entries in lexical id order.
```

`locator@-` cannot resolve normal locator because whole string kept; unknown current shape can be shown Unchanged. Advisory stale text says body changed when no active/gone/new member, not a proved cause. O(fact hashes+entries×candidates×sets). Tests live moved location55 Found, changed shape/Gone growth members, stale grown strict new member c, gone text/no entries. **Fixture design:** no-PDG growth entry site `a@-` reports Gone despite fact a present; equal-overlap different-kind candidate can supply stale hints.

### patterns.report-filtering.rust — independent lists and filter order

**Source:** [patterns_report.rs](../../rstyle/crates/rstyle-core/src/patterns_report.rs):39–121 `Options`, `build`, `mine_all`, `all_candidates`, `run`; P CLI above.

```text
Options defaults min_score_milli0,topNone,hide_implements[],params defaults,ledgerNone;
mine_all: merge -> prepare -> hide_implements -> sigmine -> candidates::mine;
all_candidates: return mined.candidates, bypass LEDGER+SCORE+TOP only;
run: ledger=provided or empty; apply to ALL ranked candidates;
 candidate list=kept with score>=min then take top (None usize::MAX);
 ignored=all hidden, include reason/entry id/match/sites; ignored_count=hidden.len;
 suppressed=all mined.suppressed UNFILTERED;
 signature groups=independently score>=min then take SAME top;
```

No style Config.exclude, changed-function filter or dedup here. Top0 yields empty shown lists but retains ignored/suppressed. build() assumes supplied groups already sorted; does not sort. Tests score400 keeps2 of900/500/100;top1 picks a; duplicated identical facts do not duplicate candidate sites; reversed corpus gives stable id12 and populated locators/shapes; ledger hides before min/top, all_candidates still returns candidate at min u32::MAX+dismissed; threshold1001 none versus default1. Cost stages+linear final filtering. Text/JSON omitted details do not change finding selection.

## Supporting and secondary stages

### graph.wl-trace.rust — serialization for walkthrough, not retrieval

**Source:** [wl_trace.rs](../../rstyle/crates/rstyle-core/src/wl_trace.rs):11–325 `Interner`, `recipe`, `interned`, `hist_view`, `trace`; L/T example wl_trace, not P candidate generation.

```text
Wl both RAW graphs; intern color hashes to u32 first-appearance ids across4 levels,
 level then A then B then node order, ONE interner for all levels;
recipes level>0 show prior intern ids of incident VALID edges, sorted(text tag,prev,node);
 histograms count ids; intersection=sum min counts; greedy display pairs match first
 unused equal-color b by index for each a (NOT actual alignment);
weights/scoring h as WL; emit all4 levels, unused weight0;
num=sum weight*intersection; den=sum weights*max nodes; floor1000*num/den or0;
run baseline align_staged REGARDLESS comparable.ok and passed threshold;
emit version2,threshold as metadata, raw graph views (ALL edges), recipe data,
 comparability limits,score,actual alignment stages/pairs/holes.
```

Interner ids equality of hashes only, not collision-free signatures. Recipe text ordering not actual WL digest numeric ordering; renderer must not infer exact FNV byte sequence from displayed order. Invalid edges ignored in computation but still in GraphView. Threshold is not acceptance/output gate. O(WL+align+recipe edge rescans+display greedy VA×VB), trace storage O(4(V+E)). Tests score matches similarity on animals,1000/full-used intersections, shared ids, tagged recipes count edges, stages firstseed/lastfinal and2 holes, serialized repeat deterministic. No light/full equivalence claim.

### patterns.audit-examples.rust — existing measurement/ablation tools

**Source:** all six [examples](../../rstyle/crates/rstyle-core/examples); supporting, opt-in execution; none executed in this audit, no test bodies. Producer fact/corpus provenance not established by tools.

```text
common: deserialize each supplied JSON file as Vec<FnFacts>; fail on read/parse errors;
 only retain present PDGs; no prepare/hide-implements/physical merge unless stated;
 all main errors print tool prefix and exit2.
align_ablation.rs:19–68:
 first fact per id into BTreeMap, sorted id order;
 enumerate EVERY pair; if comparable raw: print WL plus all6 variants' coverage/holes;
 project/id interpolated manually into JSON, not JSON escaped; no acceptance threshold.
norm_pairs.rs:12–64:
 first fact per id BTreeMap; suffix ends_with lookup requires EXACTLY1;
 read nonblank stdin lines split_once(' '), trim ONLY b; each raw/canon measure
 computes alignment EVEN IF noncomparable; print both nodes,cmp,WL,coverage.
norm_sim.rs:20–82:
 first PDG per id HashMap caches RAW+configured canonical Wl/Pdg for this invocation;
 lines split_once TAB; trim ONLY b; absent id -> literal NA;
 WL computed ALWAYS; coverage ONLY comparable else0; report nmax;
 collect all row Results before printing, any malformed line aborts output.
norm_comparable.rs:11–49:
 first present PDG per id HashMap caches canonical Wl;
 full-id TAB pairs, trim b; absent/no PDG→0; only comparable bit output;
 all results collected, malformed line error, no WL acceptance score.
norm_stats.rs:10–44:
 concatenate ALL present-PDG facts, NO dedup;
 output raw mineable count; run each ctor,pred,case,exit,counter,cmp,try,all alone;
 changed=(canonical Pdg != raw including node fields/edge order);
 count mineable_after; sum node counts before/after (NOT means, despite comment).
wl_trace.rs:9–42:
 first PDG per id BTreeMap; lookup uses ends_with, NOT substring despite doc;
 require two suffixes with exactly1 hit each; trace with threshold600 metadata;
 serde_json serialize, no prepare/normalization/comparable gate.
```

Caches keyed by id are process-local and first input occurrence, not cross-run source-invalidating caches; different file order conflicting same ids changes measurements. norm_sim comparability-zeroed coverage is different from norm_pairs/trace unconditional alignment. Statistics counts target duplicates. Cost ablation O(F²×six alignments) potentially expensive, deliberately NOT run; other tools O(fact loading+requested comparisons), norm_stats8 full normalizer/WL passes.

### quality.report-presentation.rust — deterministic diagnostics and selective group display

**Source:** [report.rs](../../rstyle/crates/rstyle-core/src/report.rs):4–219; S rendering/L; secondary presentation contract, not detector.

```text
diagnostic sort(path,line,column,rule_id);
text prints ONE headline per diagnostic (no Detail rows); optional group footer;
list group bodies only when functions.len>1 OR plan.steps.len>1;
count all other groups as independent; list members+plan steps/bundles,
 not soft hints; final summary footer;
JSON pretty serialization: skip empty details,hints,bundles,pass_through;
 skip absent plan; preserve core Report diagnostics/summary/fix_groups.
```

The JSON snapshot metadata assertion_line190 is stale relative to current test311; inspected snapshot payload matches intended fixture structurally, NOT execution claim. Tests pin path/line ordering,2 text lines, step/bundle exact strings, JSON golden with self writes4 lines[3,4,5,6],summary1 violation1 and no groups. Cost linear output except sort; external insta internal comparison unresolved.

## Decisive differences, distinguishing fixtures and deferred comparison

These are **within-Rust contracts or source/comment/historical-claim distinctions**, not invented Go or paper pseudocode. Go/reference columns remain unresolved pending other slices.

| IDs | First differing stage and observable consequence | Minimal distinguishing input (unexecuted unless named test) |
|---|---|---|
| facts.merge | Physical key/first survivor rather than id/fact union; advertised order independence limited | Same key conflicting PDG/escaping mutation; reverse input |
| effects.direct-summary.rust / effects.candidate-compatibility.rust | Candidate compatibility omits CallEvent classification and transitive effects; lowers trait scores only | One definition only std::fs::write call, other none; both empty intrinsic class; style IO differs |
| effects.transitive-export.rust | Trait intersection exact labels not all-kind or may union; possible outward effects lost | Both impls IO but read vs write, or one boundary |
| refactor.call-graph.rust / patterns.devirtualization.rust | Style graph ignores Edge.dynamic and includes impl alternatives; mining static receiver rewrites PDG only | One trait call to statically Cow receiver with Cow/Hen impls |
| refactor.pass-through-parameters.rust | Target-expanded forwarding count >= mention count can overstate pass-through | One trait site with2 targets and caller uses2 but only1 real forward |
| refactor.closed-parameter-bundles.rust | One-round intersections, not full closed-itemset enumeration | abcXY/abcXZ/abcYZ; triple intersection abc absent |
| graph.normalize.pipeline.rust | Actual try pass first; default none | Match/ctor/Return fixture under all vs ctor-before-try |
| graph.normalize.predicates.rust / patterns.alignment-holes.rust | AND/OR structure erased; Call negation detail not a hole | Same calls connected by && vs ||; !Call vs Call |
| graph.normalize.constant-constructors.rust / patterns.alignment-holes.rust | Literal subtree erased; Ctor detail not a literal hole | Err constructor over different strings but same topology |
| patterns.pair-retrieval.rust | Exhaustive≤400,2 rare-key blocking>400,whole blocks>1000 skipped | Existing private-call pair plus padding to401; tested in cluster |
| patterns.wl-similarity.rust | Multiset min, weighted raw-inclusive levels,max-node denominator; not paper equivalence | x hist2 vs3, isolated4 vs8; compare every intermediate, not group count |
| patterns.cluster-construction.rust | Star seed then medoid coverage,not pairwise clique; discovery order not largest-first | B accepted with A,C,medoid changes to A; A/C accepted by coverage alone |
| patterns.cluster-columns.rust | Same template text conflates different substitution sites,first conflicting value retained | Template repeated call M mapped to X/Y in one member |
| patterns.graph-fingerprint.rust / patterns.candidate-identity.rust | Literal/callee detail changes can preserve shape and id; strict ledger retains dismissal | Same locator+graph labels,change literal only |
| patterns.ledger-status.rust | @- parsing and missing current graph displayed inconsistently with matching | Growth site a@- with live a, or old hash with current pdgNone |
| patterns.audit-examples.rust | norm_pairs/trace align nongated; norm_sim coverage0 when incomparable; stats sums not means | Same nongated pair through three tools; duplicate JSON target facts |

**Historical reflection reconciliation scope:** `ccgraph-divergences.md:6–8,12–82` speaks predominantly about Go/Cyclo symbols. Its four-stage/paper-exact, AST, NeighborhoodWL, integer pair keys, light state, merged PR and historical performance statements cannot be confirmed by this Rust slice. Rust core inspected here instead has direct rare-class retrieval, tagged FNV WL, medoid templates, advisory parameterization, no PDG effect flags, and a nonrejecting definition-level effect penalty. These are Rust facts, not contradictions of current Go source. Reported measurements remain unverified historical claims. The effect-safety assertion is not transferable: neither matching nor Parameterize validates behavior preservation or extraction safety.

**Scope-local absence:** no core producer for CFG/PDG extraction, alias/provenance ownership analysis, initialization handling, cyclomatic/cognitive complexity, cosine/Jaro/string characteristic-vector filtering, LSH, NeighborhoodWL, CCGraph-specific clone-pair detector, transitive completeness lattice, changed-function filter or source rewriter was found in the fully read core modules. This is not a repository-wide absence claim. `FnParam` is an enum/ledger-deserializable kind with no construction in `candidates::mine`; reserved rather than an implemented active detector.

**Handoff:** first reconcile paper stage/denominator/label contracts externally; then validate producer coverage and unknown-effect plumbing; add distinguishing fixtures for merge conflict, effect-path mismatch, lossy normalization/holes and blocking boundaries before choosing unified behavior. No phase-two implementation decisions have been made.
