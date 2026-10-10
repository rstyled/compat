# Go patterns: phase-one source audit checkpoint

**Partial — not an exhaustive behavioral audit.** Snapshot: embedded `gstyle` Git HEAD `598c7b03366caa0fef70f66aa58e76222eefb8fa`, clean before and during inspection. This document owns only the Go pattern slice; [coverage, hashes, commands and resumption ledger](../go-patterns-coverage.md) define its denominator. No implementation edits, test execution, baseline regeneration, benchmarks or rewrite execution occurred.

## Record conventions and evidence boundary

All implementation/test links below are relative to **this document**, rooted at `../../gstyle/`; line ranges refer to the recorded HEAD. An ID names an independently changeable contract, not a claim of correctness. Every record inherits the following required fields unless overridden:

- **Rust pseudocode/status:** unresolved in this assigned slice; Rust source was not inspected. Comments saying “port” do not establish parity or Rust activation.
- **Reference pseudocode:** not applicable to downstream abstraction, detectors or rewriting; for graph/clone stages use the explicitly ambiguous [CCGraph reference contracts](#ccgraph-reference-contracts). No original-tool reproduction is claimed.
- **Evidence:** source-verified within the listed regions; test assertions are **unexecuted**. Examples/fixtures are unexecuted designs/inferences, not observed findings. “Implemented” and “production activated” are separate properties.
- **Inputs:** in-memory Go values; no general PDG/schema validator was found in the inspected paths. Valid node indices and sensible nonnegative counts are caller assumptions, not guaranteed at every public boundary.
- **Cost:** source-derived estimates use `n` graph nodes, `e` edges, `F` functions, `P` retrieved pairs, `d` maximum degree; excludes Go package/compiler loading and unreviewed helpers. Bounds are not measurements.

Each record below supplies purpose/output meaning, locations/symbols/ranges, callers/status/activation, inputs/outputs/dependencies, parameters, Go procedure, invariants/limitations/cost, test evidence, examples/divergence/distinguishing fixture and gaps. Pending detector/rewrite IDs in coverage are **discovery assignments**, not completed records.

## Production paths and activation

```text
patterncheck.GetReport: parse format/threshold/cache -> gopatterns.Extract
  -> report conversion (AST + error sites retained, entity locations dropped)
  -> patterns.Run:
       stable first-ID merge -> optional HideImplements
       -> MineGroups
       -> MineCached: normalize (default all OFF) -> full WL/cache
          -> abstraction pair retrieval -> flat OR weighted selection
          -> top-three-template cluster/alignment -> inference/scoring/suppression
       -> type-switch + enum candidates
       -> CCGraphClonesWithAST (raw PDGs, fixed clone threshold 900)
       -> singleFunctionBuilders (including bridge and inconsistent clones)
       -> min-score then top filtering (library options only)

patternfix.Run: parse kind/apply/changed/phased -> Extract
  -> different fixer conversion (AST + error sites dropped, entity locations retained)
  -> same patterns.Run with default Params and no cache
  -> nonnil FixSpec -> --kind -> --changed first candidate site
  -> group by file -> rank by FixKindOrder, line descending within kind
  -> ApplyFix (13 registered kinds; parameterize re-detects all pairs in file)
  -> diff by default or write; optional bounded phased re-mining
```

The command threshold changes abstraction pair selection, **not** the fixed clone threshold. No normalize, neighborhood-WL, pair-coverage, single-call-guard, max-hole, hide-implements, min-score or top CLI flags exist in the inspected patterncheck parser. These remain library inputs. No saved-facts input or reviewed-candidate ledger exists in these two inspected application files; other application/CLI consumers are outside this slice.

## `patterns.orchestration` — preparation, registry execution and final filtering

**Purpose/output:** compose signature groups, abstraction candidates, additional detector candidates and already-abstracted suppressions. **Locations:** [report.go](../../gstyle/domain/patterns/report.go#L71), `Run` 71–95, registry 107–197, `addSingleFunctionCandidates` 202–211, `mergeFacts`/`hideImplements`/`defaultParams`/`keepTop` 249–328. **Callers/status/activation:** implemented, default from both applications. **Inputs:** `[]*FuncFacts`, `Options`; default only when entire `Params` is deeply equal to zero. **Outputs:** ranked candidates, independently filtered signature groups, unfiltered suppressed list. **Dependencies:** signature, cluster, inference, clone and detector records below; no external mining library.

**Parameters/procedure:**
```text
stable-sort facts by ID (nil has ID ""); keep first per ID, do not merge fields
for implementing facts hidden by substring of ID or wildcard "*": shallow-copy, set Implements=false
groups = MineGroups(prepared)
mined = MineCached(prepared, groups, defaultParams(options.Params), cache)
append typeSwitchCandidates; stable-sort by score/sites if nonempty
append enumDispatchCandidates; same sort
compute cloneGroups ONCE = CCGraphClonesWithAST(raw facts' PDGs, names, AST types)
for each registry builder IN DECLARATION ORDER: append returned candidates; same sort
filter groups and candidates independently: score >= MinScoreMilli; append then check Top
leave Suppressed unfiltered
```
**Invariants/limitations:** no candidate deduplication here; bridge proposals can coexist with ordinary parameterize proposals for the same sites. Nil facts survive merge but not all later builders tolerate them. `Top<=0` still admits the first qualifying item because the cap is checked after append. Registry order is not identical to full FixKindOrder: type/enum run before the registry; parameterize also appears inside the later clone builder. **Cost:** sorting `O(F log F)` plus all analyzers; repeated candidate sorts.

**Tests:** report test family indexed, bodies unreviewed; do not infer their assertions from names. **Examples/fixture `GP-01`:** duplicate ID whose first copy lacks PDG and second has it; reverse input order and inspect retained facts. `Top=0` with one candidate distinguishes append-before-cap. **Divergence:** first-ID selection loses evidence rather than union merging; docs' “no duplicates” is not a general property. **Gaps:** external callers of `GetReport` not traced.

## `patterns.fact-conversion` — report/fixer schema loss

**Purpose/output:** turn extracted `FuncPdg` into `FuncFacts`; conversion itself changes reachable findings. **Locations:** [patterncheck/cli.go](../../gstyle/application/patterncheck/cli.go#L118), `toFacts`/`funcFactsOf`/converters 118–203, `GetReport` 71–113; [patternfix/cli.go](../../gstyle/application/patternfix/cli.go#L597), `toFacts`/converters 597–663, `mineCandidates` 393–411; [facts.go](../../gstyle/domain/patterns/facts.go#L14) 14–89, `EffectClass` 189–198. **Activation:** implemented/default, separate variants. **Inputs/outputs:** extraction fields copied to facts; ID and display Name both use extracted qualified Name. **Dependencies:** extraction, orchestration, detectors, clone AST and inference effects.

```text
both: copy identity/ranges, PDG, SigKeyOf, SelfTy, primitive Params,
      guard/enum/type switch and entity/DDD/gostatic hits, SuppressedKinds
neither: set Implements, Mutates or EffectKinds (remain false/false/nil)
report only: copy AstTypes and ErrorCheckSites; entityHits rebuilds each hit but
             omits StructPath/StructLine
fixer only: copies EntityIdentities verbatim (retains StructPath/StructLine);
            does NOT copy AstTypes or ErrorCheckSites
report CLI: DefaultParams with overridden ThresholdMilli; optional WL cache
fix CLI: zero Options.Params -> default parameters; no WL cache
```
**Parameters:** report threshold default 600, allowed 0–1000; cache default false, `.cyclo/patterns-cache.json`, save errors ignored. **Limitations:** summary-level effect mismatch/implements suppression operate on defaults in these production conversions despite node effect bits being present. Clone AST bypass is enabled as API but inert on fixer facts lacking AST. Error-belief builder receives no fixer sites. **Cost:** `O(F + copied hits)`.

**Tests:** [patterncheck cli tests](../../gstyle/application/patterncheck/cli_test.go#L13) 13–109 assert output sections, CreateUser/CreateOrder names, empty success, JSON key, rejected bad options, guard and trait-method output. They do not assert conversion parity. **Examples/fixture `GP-02`:** one extraction with AstTypes, ErrorCheckSites, EntityIdentityHit.StructPath/StructLine; inspect both conversions field-for-field; expect report/fixer losses above. **Divergence:** first differs at conversion, before identical miner code. **Gaps:** no end-to-end observed candidate delta; interface/effect enrichment from other consumers unknown.

## `graph.go-extraction` — selection and expression/data/control facts

**Purpose/output:** typed Go AST to expression-oriented directed PDGs plus AST/type findings. **Locations:** [extract.go](../../gstyle/adapters/gopatterns/extract.go#L100), `Extract`, package loading/query/discovery 100–228, `extractFunc` 245–305, `primitiveParams` 310–325, builder state/node/data/bind/params 327–425; [builder.go](../../gstyle/adapters/gopatterns/builder.go#L36), expression dispatch and helpers 36–339; [pdg.go](../../gstyle/domain/patterns/pdg.go#L13) schema 13–129. **Callers/activation:** implemented, both application defaults. **Inputs:** filesystem root/paths, Go AST/types from `golang.org/x/tools/go/packages v0.47.0`, `packages.LoadSyntax`, Tests not enabled. Internals of external package loader/compiler not inspected. **Outputs:** package iteration/file/declaration order; source relative slash paths, declaration/closing lines; lexical Ctrl edges and def→use Data edges; no execution edges, alias/memory model or reaching-definition fixpoint.

```text
root="" -> cwd, else filepath.Abs
paths empty -> ["."]; reject input containing "..."; stat each path
directory -> absolute directory/"..."; .go file -> "file=" + absolute path; else error
load packages; aggregate top-level package errors, strip root prefixes, abort on errors
for syntax files whose filepath.Rel succeeds, for FuncDecl with Body:
  typed FuncID/SelfTy when available, otherwise simple function name
  create named/unnamed receiver + input Param nodes; do not create result params
  lower body; separately invoke all AST detectors and AstNodeMultiset(whole declaration)
node append -> Ctrl edge from ONLY innermost lexical control frame at arm index
bind(types.Object,node): only if object nonnil, node != -1, binding absent
expr Ident: blank/definition/unresolved -> -1; existing first binding -> its node
BasicLit -> Lit(kind, exact token Value); selector -> Field(name), base Data@0
FuncLit -> opaque Closure (no body); assertion/conversion -> Cast; conversion uses first arg
binary -> Op(class:token), X@0,Y@1; unary -> addr/recv/unary class, X@0
index -> enclosing matching loop element if plain collection+counter binding matches,
         else Op(index:[]), base@0,index@1
slice -> Op(slice:[:]), X/Low/High/Max@0/1/2/3; nil inputs omitted
composite -> Op(composite:{}), values in source element order (key names discarded)
IndexList -> transparent X; KeyValue -> transparent Value; Ellipsis -> Elt; else -1
call: typed function/method/builtin resolution, else empty callee and signature or "_"
  Call effects = effectBits(quality.ClassifyCallee(calleeID)); sig normalization below
  method value receiver@0 then args@1+; free args@0+
  unresolved callee expression, when resolvable as value, @0 then args@1+
```
**Parameters:** effect bits `uint16` mutation/io/network/global/unsafe/time/random/panic/unknown at bits 0–8; map defaults to zero for other quality kinds. **Invariants/limitations:** general `nil`, `true`, `false`, constants/function identifiers without bindings are not Lit values in `ident`; named types erased, value TyClass usually absent except Param. Call arguments preserve positions even when absent inputs are omitted. `TypeSwitch` implicit objects and full quality classifier internals need separate follow-up. **Cost:** AST traversal plus node/edge emission, helper scans; compiler load unknown.

**Tests:** [extract_test.go](../../gstyle/adapters/gopatterns/extract_test.go#L54) 54–191 assert 3 Params, 2 Branches, one Try/Let in CreateUser, DB.Exec signature/callee, errors.New resolution, lexical edges, loop kinds, Defer/Go wrapping, opaque closure node, Match counts, returns and method receiver Data@0. Fixture bodies themselves unreviewed. **Examples/fixture `GP-03`:** `x:=1; x=2; use(x)` retains use→first value, not assignment node. `var x=1; use(x)` skips DeclStmt. `if nil!=err` does not emit a nil Lit. **Divergence:** PDG generation already differs from paper generators/execution and memory dependencies; canonicalization cannot restore missing facts. **Gaps:** package type detector internals mostly unreviewed; classifier call site verified, classifier internals outside owned source scope.

## `graph.go-statements` — assignments, branches and extraction-time loop/Try variants

**Locations:** [stmt.go](../../gstyle/adapters/gopatterns/stmt.go#L11), all symbols 11–508. **Purpose/inputs/outputs:** lower typed statements to the PDG above; default extraction (implemented), no separate opt-in flag. **Dependencies:** expression builder, first-bind map, lexical Ctrl stack. **Parameters:** none; built-in `len` and relational operator predicates are exact below.

```text
Block source order; Expr lower value; Return node with results Data@source position
DeclStmt/Empty/BranchStmt/select and other unhandled statements: no traversal
assignment :=:
  collect nonblank Ident LHS; if exactly one and exactly one RHS and type is not
  tuple length>1 (missing types counts single-valued): bind Def to expr(RHS) ONLY
  otherwise Let fed each RHS, bind every actual Def to same Let
assignment other: Op(assign:= or assignop:token); for each LHS, old bound Ident
  contributes next operand, then paired RHS (or RHS[0] if counts differ);
  no LHS field/index expression lowering, no binding update
inc/dec: Op(inc:++ / dec:--), operand current binding@0
if: lower Init; Try recognition ONLY no Else, one body statement,
  condition Ident != nil (nil on RIGHT), body return same object as sole result
  -> Try fed old binding@0 AND retained Ctrl-arm0 Return fed same binding@0
  else Branch fed condition@0; Body under arm0, Else under arm1
for: lower Init BEFORE recognition; single-name := any RHS, ++ OR -- same counter,
  < <= > >= in EITHER orientation against builtin len(plain Ident collection)
  -> Iterate(collection@0), attempt bind counter (first bind already wins),
     push loop context, lower body under arm0, omit condition/Post
  else Loop fed condition@0; body under arm0; Post lowered AFTER leaving loop frame
range: Iterate(collection@0); key and value attempt bind to same Iterate;
  range key is also counter for collection[key] -> Iterate; Body under arm0
switch: Match(tag@0), clause bodies under arm source index; omit case labels/conditions
type switch: Match(asserted X@0), attempt bind target; clause bodies same; omit types
defer/go: lower Call, then Defer/Go wrapper, Call -> wrapper Data@0
send: Op(send:<-), channel@0,value@1; labeled statement lower enclosed statement
```
**Invariants/limitations:** Init need not be integer/zero, comparison orientation and increment polarity need not be consistent; normalization is structural, not semantic equivalence. Canonical counter `bind` does not overwrite Init, but `collection[counter]` still resolves through loop context. Native Try retains Return while residual normalization deletes it. Assignment `+=` positions from this frontend (old at 0, RHS at 1) differ from manual-counter normalizer expectations (amount at 0, init at 1). **Cost:** linear AST traversal modulo helper calls. **Tests:** extraction assertions above; [normalize tests](../../gstyle/domain/patterns/normalize_test.go#L749) 749–783 test hand-built residual graphs and existing Try, not frontend nil emission. **Fixture `GP-04`:** pair `for i:=5; i>len(xs); i--` versus range, inspect normalized Iterate and omitted condition; contrast native `err!=nil` and residual hand-built Branch. **Gaps:** semantic preservation not established; no CFG/postdominators/branch merges.

## `patterns.signature-shape` — type/signature identities and layer-one groups

**Locations:** [shape.go](../../gstyle/domain/patterns/shape.go#L12), `TypeClass`, `SigClass`, `FuncID`, `ReceiverType` and helpers 12–154; [extract.go](../../gstyle/adapters/gopatterns/extract.go#L235) `SigKeyOf` 235–243; [sigmine.go](../../gstyle/domain/patterns/sigmine.go#L63), grouping/scoring 63–197. **Activation:** implemented/default. **Purpose/inputs/output:** type classes for WL calls/parameters, method buckets and rarity/lift; `SigClass` and `SigKeyOf` are different contracts within this record. **Dependencies:** `go/types`; facts and downstream trait inference.

```text
TypeClass: Basic name; pointer *class; slice [class]; array [class; _] (length erased);
 map[key]value; chan class (direction erased); signature/interface/struct/fallback "_";
 type param "T"+name; Named error without Pkg -> "error";
 Named package path without "." -> short type name; other Named -> "_";
 tuple -> comma-space classes; TypeClass does not generally Unalias
SigClass: receiver first if present, then args; variadic last slice -> ...element;
 "fn("+comma-space classes+") -> "+ () / single class / tuple
FuncID: package path + "." + named receiver type + "." + method, or free name;
 ReceiverType unwrap aliases and one pointer; requires named package -> pkgpath.Type
SigKeyOf: only emitted Param nodes' classes, comma WITHOUT spaces, "fn(...)";
 NO return types or variadic marker; this is the production layer-one key
bucket facts with nonempty SigKey AND SelfTy; total counts eligible inputs
partition inherent versus Implements; sort/dedupe each by ID; require >=2 inherent SelfTy
specificity = max(0, round(1000*ln(total/max(1,inherent+traited count))))
shared = max distinct SelfTy sharing one short method name
boost if shared>=2 = uint64(specificity)/2 * shared / inherentSelfTypes (integer steps)
Score = specificity + boost; groups descending score then key
```
**Limitations:** return-distinct methods can share production SigKey; generic arguments and concrete named identities often erased before holes. Compiler tests with hand-authored richer facts do not prove production enrichment. Eligible total before per-bucket dedup can inflate standalone MineGroups specificity. **Cost:** `O(F log F)` plus recursive type shape traversal.

**Tests:** shape/sigmine test bodies indexed only; extraction `TestStraightLineStructure` asserts full Call SigClass. **Examples/fixture `GP-05`:** methods `A.Get() int` and `B.Get() string` have same extracted Param key; verify layer-one grouping despite different result types. Negative free functions excluded; two methods on only one SelfTy fail floor. **Divergence:** first differs at production signature serialization, not scoring. **Gaps:** Rust raw-shape comparison unresolved.

## `graph.canonicalize` — cloned graph and exact pass order

**Locations:** [normalize.go](../../gstyle/domain/patterns/normalize.go#L43), Rules/ParseRules/Canonicalize and shared helpers 43–264. **Purpose/output:** optional graph rewrites before abstraction hashing/alignment, not CCGraph raw detection. **Status/activation:** implemented, library opt-in; both inspected CLIs default all OFF. **Inputs:** nonnil valid PDG, Rules. **Parameters:** parser accepts trimmed comma names `all,ctor,pred,case,exit,counter,cmp,try`; empty skipped, unknown aborts returning zero Rules. **Dependencies:** next seven records.

```text
clone Nodes and Edges even with no rules
apply at most once each IN THIS ORDER:
  Propagate -> Ctor -> Pred -> Case -> Exit -> Counter -> Cmp
without(dead): preserve surviving node order; compact indices; drop all incident edges
ownedBy(node,consumer): distinct data consumer set equals {consumer}
ctrlParent(node): FIRST incoming Ctrl edge, not uniqueness verification
dedupEdges: exact struct equality, keep first occurrence
```
**Limitations:** comment claiming R1/R2 order is stale; propagation actually first. No cycle/invalid-index guards in recursive tree helpers; no global convergence loop. Idempotence is a finite fixture assertion, not enforced postcondition. **Cost:** cloning `O(n+e)`; per-rule helper scans can be superlinear; general cyclic-input termination unknown. **Tests:** normalize_test.go reviewed 1–260 (fixtures), 650–823 (assertions); 261–649 unreviewed. **Fixture `GP-06`:** Match-ctor-return graph with `try,ctor,case` demonstrates propagation must precede relabel/folding. Empty rules must yield equal contents without mutating source.

## `graph.canonicalize-propagate` — Match and residual nil guards

**Locations:** [normalize.go](../../gstyle/domain/patterns/normalize.go#L899), `matchArms` through `propagateErrors` 899–1114. **Purpose/output:** convert selected Match/Branch to Try. **Activation:** optional `try`, FIRST pass; implemented, residual Go shape may be frontend-unreachable because general nil Ident is omitted. **Inputs/dependencies:** graph.canonicalize helpers; exact Data/Ctrl topology. **Parameters:** two distinct Match Ctrl targets; exact one-producer/one-target guards.

```text
Match: sorted distinct outgoing Ctrl targets must be exactly two;
 choose ctor c and Return r (swap if first target is Return);
 c is Op ctor/tuple/composite; c has sole data producer Match;
 c ownedBy Return; Return has sole producer c
 -> relabel Match Try; delete c,r
Branch: sole producer Op suffix != or ==; exactly two inputs, one Lit(nil,no CalleeID);
 op ownedBy Branch and nil ownedBy op;
 != error arm0 / == error arm1 has exactly one Ctrl target, a Return whose sole producer is x
 -> relabel Branch Try; delete op,nil,Return; append x->Try Data@0
collect matches before edits; dedup extra edges; remove dead/reindex
```
**Limitations:** no requirement that `x` has error type; no Ok/Err identity check on Match ctor. Other arm unrestricted in Go branch case. Native extracted Try is never matched and retains its Return. **Cost:** repeated edge scans `O(ne)` plus removal. **Tests:** `TestExplicitErrorPropagationBecomesTry` 705–713, negative other-arm work/other value 715–737, idempotence 739–747, residual neq/eq 749–773, existing Try 775–783 in [normalize_test.go](../../gstyle/domain/patterns/normalize_test.go#L705). **Fixture `GP-07`:** identical logical error guard hand-built with `Lit(nil)` versus extracted general nil Ident; expect only hand-built residual fold. No end-to-end proof.

## `graph.canonicalize-ctor` — owned constant trees and nested splicing

**Locations:** [normalize.go](../../gstyle/domain/patterns/normalize.go#L270), all helpers `isCtorOp` through `spliceNested` 270–490. **Purpose/output:** fold owned literal construction to Ctor and splice nonconstant nested construction. **Activation:** optional ctor, implemented. **Inputs/parameters:** Op detail class `composite` or suffix `ctor`/`tuple`; value leaf Lit with empty callee. **Dependencies:** graph.canonicalize removal/ownership.

```text
constantTree(n): ctor Op AND every data producer owned exclusively by n and
                is value Lit OR recursively constantTree (zero inputs qualifies)
roots = constant trees with no constantTree data consumer, ascending node order
map recursively all input ancestors (except root) -> root; delete ancestors
root -> Ctor preserving other fields; unit path Lit (no callee, last :: segment
         Unicode uppercase and contains lowercase) -> Ctor
move incoming Ctrl edges targeting absorbed nodes to root; dedup; without(dead)
remaining nested Op ctor with exactly one data consumer that is Op ctor:
  drop edges FROM inner nodes; reroute Data edges TO inner to outermost ctor
  delete inner nodes, incident Ctrl edges drop (not generally rerouted); dedup/reindex
```
**Limitations:** recursive inputs have no visited/cycle guard; constant leaf type not used; textual data lost when operands deleted (root detail remains). Unit-path branch inert on current Go frontend. **Cost:** repeated recursive scans; unknown robust bound for arbitrary cyclic PDG. **Tests:** ctor assertion bodies 261–649 not reviewed; nestedConstant fixture reviewed 92–98. **Fixture `GP-08`:** same literal owned only by ctor versus shared with Call; only first folds. Add Ctrl into nested nonconstant inner ctor to expose dropped-control behavior. Negative/degenerate zero-input composite qualifies.

## `graph.canonicalize-pred` — boolean combinator deletion

**Locations:** [normalize.go](../../gstyle/domain/patterns/normalize.go#L494), `isCombinator` through `collapsePreds` 494–623. **Purpose/output:** remove &&/||/! trees over Call leaves. **Activation:** optional pred, implemented. **Inputs/parameters:** suffix check on Op; no data ownership check. **Dependencies:** helpers above.

```text
predicateTree = Op suffix &&/||/! with all producers Call or recursive predicateTree
collect ALL such combinator nodes; roots have no data consumer in tree set, sort roots
walk leaves, flip negation parity only at !; any negated occurrence marks Call.Detail="!"
for each root outgoing Data edge and each Call leaf:
  copy edge replacing From with leaf, ArgPos=0
append/dedup extras; delete every combinator, reindex
```
**Limitations:** AND versus OR/short-circuit semantics erased; shared combinators may lose nonroot edges, Call negation detail is neither WL label nor a Call text hole. Empty combinators vacuously qualify. Not a semantics-preserving rewrite. **Cost:** repeated edge scans/tree recursion; cyclic termination not guarded. **Tests:** [TestDeferWrappingSurvivesPredicateCollapse](../../gstyle/domain/patterns/normalize_test.go#L795) 795–813 asserts rewired Call inputs and preserved wrapping; other predicate assertion bodies unreviewed. **Fixture `GP-09`:** calls feeding AND versus OR yield same normalized data edges, unless non-observed detail separates them; compare intermediate graphs, not refactor safety.

## `graph.canonicalize-case` — Let contraction, literal scrutinees, flattening

**Locations:** [normalize.go](../../gstyle/domain/patterns/normalize.go#L627), all symbols 627–873. **Purpose/output:** Branch/Match to Case, remove selected match-pattern scaffolding. **Activation:** optional case, implemented. **Inputs/dependencies:** exact edge-order-sensitive producer lists; ownership helpers. **Parameters/procedure:**
```text
map each Let->Branch Data edge to branch (last encountered wins if multiple)
rewrite edges from Let to Branch (drop own Let->Branch); Data into Let -> Branch;
 drop nonData into Let; delete mapped Lets/dedup
for Branch with sole producer Op ==, exactly two inputs, one value Lit and
 nonliteral x, Lit ownedBy Op, Op ownedBy Branch:
 delete Op+Lit; add x->Branch Data@0
relabel every Branch or Match Case
repeat: lowest-index Case parent whose max Ctrl arm has exactly one target child,
 child Case has SAME ordered nonempty data producer list, no Data consumers:
 remove all edges touching child; lift child Ctrl edges to parent with
 ArgPos=parentLastArm+childArm; delete child/reindex; recur
```
**Limitations:** Let contraction has no unique-consumer guard; literal values removed; ordered producer-list equality, not set equality. Actual frontend branch condition nodes can be multiple Ctrl targets, preventing flattening despite source “else if”. **Cost:** `O(ne)` scans per iteration, at most n removals; `O(n²e)` conservative bound. **Tests:** case names indexed only, fixtures `ifLet`, `twoArmMatch`, `literalChain` reviewed 128–203. **Fixture `GP-10`:** same scrutinee inputs in different edge orders preserve nesting; shared Let feeding Branch plus Call exposes contraction without exclusivity.

## `graph.canonicalize-exit` — synthetic unreachable removal

**Locations:** [normalize.go](../../gstyle/domain/patterns/normalize.go#L881), `macroKind`, `dropUnreachable` 881–895. **Purpose/output:** delete selected macro-kind nodes. **Status/activation:** implemented/library opt-in exit; dormant for current Go extractor (no Macro output). **Inputs/parameters/procedure:** any node Kind exactly `"macro"`, Detail containing substring `"unreachable"`, no incoming Data -> delete with incident edges/reindex. No requirement it follows a loop or represents unreachable control. **Dependencies:** removal helper. **Cost:** `O(ne)`. **Tests:** relevant assertion body not reviewed; pMacro fixture 40–43 inspected. **Fixture `GP-11`:** isolated `macro` with detail `not_unreachable_yet` is removed; same macro with incoming Data kept. Paper simplification does not prescribe this rule.

## `graph.canonicalize-counter` — three independently guarded subpasses

**Locations:** [normalize.go](../../gstyle/domain/patterns/normalize.go#L1118), `rangeLoops`, `manualCounters`, `loopGuards`, helpers and fixed composition 1118–1508. **Purpose/output:** Loop as counter identity; delete range bounds/step/guards. **Activation:** optional counter, implemented; Rust-range branch inert for ordinary Go callee IDs. **Inputs/dependencies:** Op suffix parsing, exact operand positions and first Ctrl parent. **Parameters:** enclosing Loop search at most **4** incoming Ctrl hops.

```text
1 range: Iterate sole producer with CalleeID containing "ops::range::";
   that producer sole consumer Iterate; exactly two int-Lit inputs each ownedBy producer
   -> Iterate Kind=Loop, Detail=bound details in producer edge order joined "..";
      delete producer+bounds (does NOT check producer Kind Call)
2 manual: Op suffix +=/+== with int amount@0,int init@1, OR ++/-- with exactly
   one int init@0; amount exclusively owned if present; step has no Data consumers;
   nearest Loop within four FIRST Ctrl-parent hops
   -> map init to Loop (later discovered step overrides earlier); all outgoing init
      Data except to any identified step copied From=Loop; delete init/step/amount
3 guard: Branch or Case whose FIRST Ctrl parent is Loop; sole producer comparison
   < <= == >= > !=; exactly two inputs containing parent Loop and int Lit bound;
   bound ownedBy comparison, comparison ownedBy guard; ALL Ctrl arms ==0
   -> copy outgoing guard Ctrl from Loop; delete guard/comparison/bound
```
**Limitations:** manual += positions mismatch extractor; frontend conventional Loop Post is outside its control frame and condition feeds Loop, not guard Branch. Range normalization uses Rust IDs; no loop semantic/termination guarantee. AllArmZero vacuously true with no arms. **Cost:** repeated scans `O(ne)` plus hop scans, assuming valid acyclic parent/tree traversal. **Tests:** hand-built `whileForm` and `incWhileForm` fixtures inspected; [TestCounterRulesAreIdempotentAndShrink](../../gstyle/domain/patterns/normalize_test.go#L693) 693–703 finite assertions. **Fixture `GP-12`:** compare extracted `for i:=0; i<3; i++` and hand-built incWhileForm; the former's Post lacks Loop Ctrl and may not fold. This is a producer/consumer topology distinction, not Go/Rust parity evidence.

## `graph.canonicalize-cmp` — counted comparison class

**Locations:** [normalize.go](../../gstyle/domain/patterns/normalize.go#L1512), helpers/`compareClass` 1512–1549. **Purpose/output:** normalize comparison detail to cmp class preserving suffix. **Activation:** optional cmp, implemented; largely redundant for frontend comparisons already cmp-prefixed. **Inputs/parameters/procedure:** Op suffix in six compares, exactly two Data producers, at least one Loop and one int value Lit -> Detail=`cmp:`+suffix; clone nodes, retain edges. **Dependencies:** counter graph shape. **Cost:** `O(ne)`. **Tests:** [normalize_test.go](../../gstyle/domain/patterns/normalize_test.go#L658) 658–691 assert equal labels/different cmp details and unchanged noncounter. **Fixture `GP-13`:** raw `<` versus `==` beside Loop/int become same WL Op class but distinct HoleOp; replace Loop with Param for no rewrite. Note frontend already erases comparison operator in labels even without cmp activation.

## `graph.wl-labels` — byte encoding and working graph

**Locations:** [wl.go](../../gstyle/domain/patterns/wl.go#L15), FNV/combine/label/callScope/edgeTag/buildGraph 15–177. **Purpose/output:** comparable uint64 colors and directed tagged adjacency. **Activation:** implemented/default both clone and abstraction pipelines. **Inputs:** valid Pdg; labels below omit names/effects but include call scope. **Dependencies:** type/signature classes. **Parameters:** FNV offset `14695981039346656037`, prime `1099511628211`, uint64 wrap arithmetic; combine hashes 16 LE bytes `(acc,value)`.

```text
Call: "call:"+scope+":"+SigClass; Lit:"lit:"+LitKind; Param:"param:"+TyClass
Op:"op:"+Detail before first ":"; other: Kind string
scope: builtin. prefix -> builtin; remove last dotted callee segment;
 remove last remaining dotted segment if its first byte A..Z;
 empty -> unknown; remainder contains dot -> local; else std
edge tag = combine(kind==Ctrl ? 1 : 0, uint64(ArgPos))
initial colors=FNV1a(UTF8 label); keep incoming and outgoing lists in edge order
skip edges with From>=n or To>=n (negative endpoints NOT rejected)
```
**Limitations:** unexported receiver qualifier scope heuristic can misclassify stdlib methods; unknown EdgeKind hashes like Data. No collision disambiguation; “iff equal sequences” from paper not guaranteed. **Cost:** `O(n+e+label bytes)`. **Tests:** [wl_round2_test.go](../../gstyle/domain/patterns/wl_round2_test.go#L10) 10–50 scope cases/stdlib twins/local name independence, 141–169 cross-scope similarity assertion. **Fixture `GP-14`:** identical graph calling `fmt.Printf` versus local same-signature function changes initial colors; swap operator within same class does not. FNV golden test indexed, not read/executed.

## `graph.wl-refinement-depth` — directional multisets, diameter and full/light state

**Locations:** [wl.go](../../gstyle/domain/patterns/wl.go#L157), digest/refine/histogram/BFS/diameter 157–241, constructors/rounds 243–425. **Purpose/output:** up to four color rounds and sorted histograms; full state usable for alignment versus light state for clone kernel/retrieval. **Activation:** implemented/default; NewWlLight only clone path, NewWl/cache abstraction and inconsistent path. **Parameters:** `maxLevels=4`, `diameterLimit=400`; salts in `0x1f`, out `0x2e`.

```text
digest(own,salt,N,prev): parts=[combine(edgeTag,prev[neighbor]) for every adjacency]
 sort uint64 parts retaining duplicates; acc=combine(own,salt); fold combine(acc,part)
refine[v]=digest(digest(prev[v],inSalt,IN,prev),outSalt,OUT,prev)
diameter: if n>400 return 4; else max BFS eccentricity from EVERY node,
 traversing both IN and OUT, considering only reachable nodes (finite component diameter)
round count h=clamp(diameter+1,1,4); round0=raw labels; h-1 refinements
hist: count each color; sorted uint64 keys
pair levels=clamp(min(a.diameter,b.diameter)+1,1,4)
full keeps graph,rounds,hists,callCount,diameter,charVec,pdg,nodeCount
light computes same graph/refinement then keeps only hists/calls/diameter/supplied charVec/nodeCount
```
**Limitations:** isolated/disconnected graphs d=0 or largest finite component diameter; giant-graph cap not measured diameter. Light is inappropriate for Align/weighted kernel/cache Put (missing graph/rounds/pdg), not a universal drop-in. **Cost:** BFS `O(n(n+e))` below cap, rounds `O(e log d+n)` each, full `O(e+4n)` retained; light transient same construction but fewer retained fields. **Tests:** [wl_opt_test.go](../../gstyle/domain/patterns/wl_opt_test.go#L56) 56–67 two-node chain has two rounds; [perf_regression_test.go](../../gstyle/domain/patterns/perf_regression_test.go#L157) 157–199 finite random-graph BFS/Floyd comparison. No inspected universal full/light equivalence test. **Fixture `GP-15`:** 400 versus 401 isolated nodes gives d=0 versus d=4 and one versus four rounds; compare light/full histograms for each, not only one similarity=1000.

## `graph.wl-flat-score` — weighted histogram intersection and threshold bound

**Locations:** [wl.go](../../gstyle/domain/patterns/wl.go#L427), weights/intersection/SimilarityMilli/similarityAtLeast 427–508. **Purpose/output:** 0–1000 normalized similarity or Boolean threshold, not semantic equivalence. **Activation:** implemented/default clone (900) and abstraction (600). **Inputs/dependencies:** sorted histogram/counts/diameter/nodeCount from previous record. **Parameters/procedure:**
```text
h=pair levels; I_i=sum_color min(countA_i,countB_i); w_i=h-i for i=0..h-1
num=sum uint64(w_i*I_i); den=max(nodeCountA,nodeCountB)*sum w_i
SimilarityMilli=0 if den==0 else uint32(num*1000/den), integer truncation
threshold variant: remaining=h(h+1)/2, bound=min(node counts)
 before each round, reject if floor((num+remaining*bound)*1000/den)<limit
 accumulate round, subtract weight; final floor(num*1000/den)>=limit
 den==0 Boolean returns limit==0
```
**Limitations:** histogram intersection, not cross-product equal-label counts, and MAX count denominator with weight-sum normalization, not paper printed MIN/union formulas. uint64 overflow unchecked. Empty zero-score agrees with zero-threshold Boolean. **Cost:** `O(sum histogram sizes)` with linear sorted merges. **Tests:** [perf_regression_test.go](../../gstyle/domain/patterns/perf_regression_test.go#L223) 223–253 compares threshold to exact score on 60 random graphs, limits 0/600/899/900/901/1000; not proof for malformed/overflow inputs. **Fixture `GP-16`:** hist color c has counts 2 and 3: intersection 2 versus cross-product 6; round0-only graph sizes 2/3 Go 666 versus min-denominator variant 1000 (if using intersection). Exact 900 accepted.

## `graph.wl-projection-score` — control/data variant

**Locations:** [wl.go](../../gstyle/domain/patterns/wl.go#L514), projection/`projHists`/`SimilarityWeighted` 514–612. **Purpose/output:** control-skeleton-weighted score, additional abstraction selector. **Activation:** implemented/default abstraction selector; NOT standard CCGraph Stage 4. **Inputs/dependencies:** full WL with pdg; lazy per-edge-kind histogram cache. **Parameters/procedure:**
```text
if either PDG has no Ctrl edge: return flat score
Ctrl projection: node label=Kind only; Data projection: full original label
keep only selected edge kind, with original arg tags/direction; four rounds ALWAYS
use original full-graph pair levels and max-count denominator for projected scores
return floor((12*ctrlScore + 4*dataScore)/16)
```
**Limitations:** comments mention 1.0/0.6 and data floor 500; actual weights are **12:4 (3:1)** and **no data floor enforced**. All nodes retained even if isolated in projection. Projection cache depends on attached graph and not safe for light instances. **Cost:** lazy construction as refinement; subsequent histogram comparisons linear. **Tests:** [TestWeightedSimilarityBreaksTies](../../gstyle/domain/patterns/wl_round2_test.go#L117) 117–136 actually calls weighted and flat; `TestWeightedKernelRanksLogicOverData` 100–111 calls only **flat**, despite its name/comment. **Fixture `GP-17`:** two same-kind/control graphs with changed Call signatures and low Data projection; record ctrl/data scores and weighted admission at 600 despite data<500.

## `clone.features` — seven-coordinate numerical gate

**Locations:** [wl.go](../../gstyle/domain/patterns/wl.go#L263), characteristicVector/nodeKindIndex/countEdges/cosine 263–326; [ccgraph.go](../../gstyle/domain/patterns/ccgraph.go#L86) 86–92 and filter 180–188. **Purpose/output:** cheap clone candidate decision; used also by abstraction selection. **Activation:** implemented/default except AST bypass. **Inputs/dependencies:** raw clone PDG or canonical abstraction PDG. **Parameters/procedure:**
```text
[Let count, ALL Op count, Branch+Match+Loop+Iterate count, Call count,
 all remaining node kinds count, Ctrl edge count, Data edge count]
cosine=dot/(sqrt(sum squares A)*sqrt(sum squares B)); zero norm ->0
pass >=0.9
```
**Limitations:** Op includes arithmetic/index/send/composite, not just assignments. Case/Ctor/Try are “other”; no execution/reference counts. Does not compare IntroPara/ReturnPara string coordinates. Clone path has **no explicit minimum-node, call-count or scale gate** beyond nonempty; abstraction adds its own gates below. **Cost:** `O(n+e)`, each pair fixed-size cosine. **Tests:** [TestCharacteristicVector](../../gstyle/domain/patterns/wl_opt_test.go#L5) 5–25 exact vector, cosine/charVec 27–54. **Fixture `GP-18`:** one arithmetic Op versus one assignment Op produce same count; one-node noncall clones can pass clone path but fail abstraction Mineable.

## `clone.name-filter` — shortened-name Jaro–Winkler

**Locations:** [ccgraph.go](../../gstyle/domain/patterns/ccgraph.go#L190), nameMatcher/lower bound 190–244, Jaro helpers 350–464; [sigmine.go](../../gstyle/domain/patterns/sigmine.go#L46) shortName 46–51. **Purpose/output:** numeric name similarity/Boolean candidate filter. **Activation:** implemented/default unless AST bypass; missing short name passes. **Parameters:** rune strings, threshold >=0.5, prefix up to 4, factor 0.1 always (no Jaro floor before boost).

```text
use suffix after final "." for each qualified name
empty either -> candidate passes (raw Jaro one-empty=0, both-empty=1)
prefix=equal leading runes max4;
 lowerJ=(prefix/lenA+prefix/lenB+0.5)/3; if prefix>0 and
 lowerJ+prefix*.1*(1-lowerJ)>=.5 -> accept without full search
otherwise greedily match A runes to first unused equal B rune within
 max(0,floor(max(lenA,lenB)/2)-1), inclusive endpoints
t=matched-sequence mismatches/2; J=(m/lenA+m/lenB+(m-t)/m)/3 (m=0 ->0)
JW=J+prefix*.1*(1-J); accept >=.5
workers reuse/clear their own Boolean match buffers
```
**Limitations:** paper string fields reduced to function name only. **Cost:** worst `O(lenA*lenB)`, per-worker scratch max-name length. **Tests:** [ccgraph_test.go](../../gstyle/domain/patterns/ccgraph_test.go#L5) 5–44 basic JW; 83–121 qualified-name rejection/cross-package matches; [perf tests](../../gstyle/domain/patterns/perf_regression_test.go#L68) 68–81 repeated scratch equality; 201–221 5,000 seeded Unicode/name trials comparing optimized exact filter. **Fixture `GP-19`:** qualified `pkg.Type.aaaaaaa` versus `pkg.Type.zzzzzzz` rejects despite long package prefix; omitted name passes. Boundary .5 accepted.

## `clone.ast-bypass` — node-kind multiset and bypass scope

**Locations:** [asthash.go](../../gstyle/domain/patterns/asthash.go#L25) 25–101; [ccpairs.go](../../gstyle/domain/patterns/ccpairs.go#L50) 50–103; [ccgraph.go](../../gstyle/domain/patterns/ccgraph.go#L180) 180–188; report activation 202–205. **Purpose/output:** add candidate pairs irrespective of both cheap filters. **Status/activation:** implemented/default report; library WithAST; fixer conversion omits AST. `astPruneThreshold=.3` is declaration-only in searched slice, no pruning branch.

```text
AstNodeMultiset(whole FuncDecl): walk AST including signature and nested closures;
 skip counting Ident and BasicLit (still recurse); count reflect concrete type names
AstJaccard = sum min / sum max over union keys; both empty ->1, one empty ->0
production dense shapes: shared kind coordinates; missing/empty map -> bypass false
if both nonempty and largest total==0 -> bypass true;
 if min(total)/max(total)<.8 -> false;
 exact inter=sum min; union=totalA+totalB-inter; bypass inter/union>=.8
if bypass -> ccPairFilters.accepts returns TRUE BEFORE cosine AND name;
LSH retrieval and final WL still required
```
**Limitations:** reflection/docs saying bypass only numerical gate are contradicted by early return; AST fingerprint sees closure bodies while PDG is opaque. Adding eligible members changes LSH connected components, so “only adds candidates” does not prove group-count or labeled-recall monotonicity. **Cost:** AST traversal once; dense `O(F*K)` space, up to `O(F²K)` comparisons with size bound. **Tests:** [asthash_test.go](../../gstyle/domain/patterns/asthash_test.go#L27) 27–96 nil/empty/renaming/structure/overlap/bypass; 98–145 weak group-count checks. `TestCCGraphClonesWithASTFindsSyntacticClone` only asserts AST group count not less than plain, **does not establish a gain or cosine failure**; supplied chains 20/8 have similar vectors. [TestASTBypassStillAdmitsDifferentQualifiedNames](../../gstyle/domain/patterns/ccgraph_test.go#L123) 123–130 directly asserts name bypass. **Fixture `GP-20`:** equal AST shapes and identical PDGs, names aaaaaaa/zzzzzzz -> plain no clone, AST clone; 4/5 overlap boundary passes at .8, missing AST does not.

## `clone.pair-storage` — row-owned bitset and cheap pair enumeration

**Locations:** [ccpairs.go](../../gstyle/domain/patterns/ccpairs.go#L13) 13–48; [ccgraph.go](../../gstyle/domain/patterns/ccgraph.go#L131) IDs/filter workers 131–188. **Purpose/output:** unordered candidate membership and sorted participating indices. **Activation:** implemented/default clone. **Inputs/parameters:** sorted usable PDG IDs (nonnull, n>0); workers min(NumCPU,F). **Dependencies:** numerical/name/AST filters.

```text
width=ceil(F/64); allocate F*width uint64 words (full row matrix, not sparse map)
worker w owns rows i=w,w+workers,...; for j=i+1..F-1 if filters accept:
 words[i*width+j/64] |= 1<<(j%64)
has swaps i/j if necessary; members scans nonzero words, marks row and set bits;
 return present indices ascending
```
**Limitations:** add assumes i<j and valid indices; integer allocation multiplication unchecked. Current implementation is **not reflection's int64 pair-key map**. **Cost:** memory `8*F*ceil(F/64)` bytes plus O(F) seen; all F(F−1)/2 cheap comparisons remain quadratic regardless of LSH. **Tests:** [TestCompactPairsAcrossWordBoundaries](../../gstyle/domain/patterns/perf_regression_test.go#L107) 107–123 indices 0/63/64/65/129 and symmetric lookup; 125–155 finite 100 seeded cheap-filter comparisons. **Fixture `GP-21`:** 63/64 boundary pairs and reversed lookup; no runtime/memory measurement claimed.

## `clone.lsh-retrieval` — folded vectors, hyperplanes and component broadening

**Locations:** [lsh.go](../../gstyle/domain/patterns/lsh.go#L21), all algorithms 21–196; [ccgraph.go](../../gstyle/domain/patterns/ccgraph.go#L252), light construction 252–260 and `ccLSHClusters` 277–284. **Purpose/output:** candidate connected components; approximate retrieval distinct from WL label compression. **Activation:** implemented/default clone, even neighborhood variant uses **standard light WL vectors**. **Parameters:** 512 dimensions=4×128; 16 tables×4 normal hyperplanes, `math/rand.NewSource(42)`.

```text
Vectorize: for available round r<4, for color,count:
 vec[r*128+color%128] += count*(4-r); absent rounds all zero
NewLSH: sequential table/hash/dimension draws rng.NormFloat64
signature: bit h=1 if dot(vec,plane_h)>=0
Add all IDs to every table; union EVERY bucket's members to first member;
normalize connected sets, return groups>=2, sorted members and groups by first member
Query API dedupes bucket mates across tables, but ClusterClones does NOT use Query
```
**Limitations:** function pairs in same connected LSH component need not directly share a bucket; final clone stage examines all within-component pairs, subject to cheap membership. Pairs in separate components are never scored even if WL>=900. No completeness guarantee. uint64 signatures, documented numHashes<=64 but constructor does not validate; dimension mismatch not checked. **Cost:** build `O(F*T*H*512)` plus planes `T*H*512`; component candidate verification can still be quadratic. **Tests:** [lsh_test.go](../../gstyle/domain/patterns/lsh_test.go#L43) 43–153 vector dimensions/determinism/one permutation, identical/opposite collision, sorted grouping; [perf test](../../gstyle/domain/patterns/perf_regression_test.go#L83) 83–105 finite bucket-versus-query grouping. **Fixture `GP-22`:** hand-specified bucket chain A-B, B-C demonstrates A-C retrieval broadening; separate components with high final kernel demonstrate potential omission, pair set must be inspected rather than counts. Random generator internals not audited beyond standard API/version.

## `clone.accept-and-group` — final threshold and transitive output

**Locations:** [ccgraph.go](../../gstyle/domain/patterns/ccgraph.go#L46), entry variants/orchestration 46–119, workers/union 293–348, candidate construction 475–543; [lsh.go](../../gstyle/domain/patterns/lsh.go#L133) union/find/sorted groups 133–168. **Purpose/output:** clone groups, then fixed-score group suggestions. **Activation:** implemented/default report and fixer; WithNeighborhoodWL library-only in inspected orchestration. **Inputs/dependencies:** candidate bitset, retrieved components, standard/light or neighborhood scores. **Parameters:** final >=900; suggestion score 750.

```text
if <2 usable IDs -> nil; if cheap candidate members empty ->nil
build light WL only for participating IDs; retrieve LSH components
initialize union-find over all usable IDs
within each component, stripe all i<j; require cheap candidates.has;
 standard similarityAtLeast(900) OR selected neighborhood score>=900 (replacement, NOT union)
collect accepted pairs per worker, apply unions sequentially as messages arrive
return sorted final connected groups size>=2; discard accepted pair list
candidate per group with >=2 resolvable facts: Sites Path/Line/Name ONLY, score750,
 no FixSpec (ID and EndLine left zero)
```
**Limitations:** A~B and B~C joins A,B,C regardless of A~C; no exact isomorphism verifier, and none prescribed by paper. Text says similar names even when bypassed/missing. Output root order normalized but accepted-edge evidence lost. **Cost:** `O(sum component size² * histogram merge)` plus union operations. **Tests:** [ccgraph_test.go](../../gstyle/domain/patterns/ccgraph_test.go#L59) 59–162 clone membership/name cases/empty/determinism. **Fixture `GP-23`:** A-B/B-C pass900 but A-C<900; expect one group, not three verified pair assertions. Compare with paper pair output and abstraction cluster ownership.

## `graph.neighborhood-wl` — optional multi-neighborhood replacement

**Locations:** [neighborhood_wl.go](../../gstyle/domain/patterns/neighborhood_wl.go#L28), all helpers/constructor/kernel 28–213; caller ccgraph 104–109, 265–273. **Purpose/output:** alternate 0–1000 kernel over repeated local neighborhood colors. **Activation:** implemented/library entry WithNeighborhoodWL; not `Run` default. **Inputs:** original WL graph. **Parameters:** k=1,2, weights2,1; exactly **one** refinement, no round-zero aggregation.

```text
for k=1,2:
 for each center: undirected BFS via in/out to <=k hops, includes center,
   workspace generation markers (not clear per search)
   for every neighborhood node u: one original-label refinement, restrict neighbors
     to marked set; preserve direction/tag, digest in then out
   append colors to aggregate (same node counted once for EVERY containing neighborhood)
 sort histogram; total=sum neighborhood sizes
num=2*intersection(H1)+intersection(H2)
den=2*max(total1A,total1B)+max(total2A,total2B)
return 0 if den==0 else floor(1000*num/den)
```
**Limitations:** does not union acceptance with flat kernel; no source-enforced strict-superset property despite comment “K2 strict superset”. Standard-WL LSH still precedes alternate score. **Cost:** worst every neighborhood contains all nodes, `O(n(n+e log d))` compute, temporary O(n²) aggregated colors. **Tests:** [neighborhood_wl_test.go](../../gstyle/domain/patterns/neighborhood_wl_test.go#L5) 5–85 self/deterministic/unrelated/pipeline assertions; gapped comparison 30–49 **logs only**, not recall/superset assertion. **Fixture `GP-24`:** delete a high-degree node, inspect changed totals per k and scores/accepted pairs. Historical extra-group counts do not establish labeled recall.

## `patterns.pair-retrieval` — abstraction blocking and guarded selector

**Locations:** [cluster.go](../../gstyle/domain/patterns/cluster.go#L11), constants/Params 11–51, call classes/blocking/pairSelected/adjacency 71–225; [wl.go](../../gstyle/domain/patterns/wl.go#L615) Mineable/Comparable/CallClass 615–638. **Purpose/output:** undirected adjacency for template clustering, separate from clone retrieval. **Activation:** implemented/default; PairCoverage library experiment. **Inputs:** canonical PDGs/full WL. **Parameters:** defaults similarity600/coverage600/MaxHoles3/no normalization/no SingleCallGuard/no PairCoverage; F<=400 all-pairs, blockCap1000, 2 rarest classes.

```text
F<=400 -> all ascending unordered pairs
else: distinct CallClass per graph (SigClass else CalleeID else "?");
 corpus frequency counts containing functions, sort keys by (frequency,class), take2;
 index keys; skip blocks size>1000; all block pairs sorted/dedup
select only if each graph nodes>=4 AND calls>=1 AND larger<=2*smaller
 require characteristic cosine>=.9 BEFORE all alternative acceptance
 flat>=Threshold OR weighted>=Threshold ->true
 else optional PairCoverage enabled -> Align coverage>=floor; otherwise false
construct symmetric adjacency for selected pairs only
```
**Limitations:** pair-coverage does not bypass size/scale/cosine or retrieval. Moving from 400 to 401 corpus functions can lose previously compared pairs due to private rare keys. Comment “union no lost pairs” applies only to selector inputs after earlier gates. **Cost:** O(F²) small, sum bounded-block pair generation large plus sorted dedup; WL scoring per retrieved pair. **Tests:** [cluster_test.go](../../gstyle/domain/patterns/cluster_test.go#L47) default assertions47–64, threshold550/55192–112, coverage129–159, retrieval174–195. [multitemplate tests](../../gstyle/domain/patterns/cluster_multitemplate_test.go#L49) 49–65 flat-union conditional assertion. **Fixture `GP-25`:** 400/401 functions each with two private call classes; inspect retrieved pair list (400 all,401 none). At1000/1001 common block inspect cap exclusion.

## `patterns.alignment` — seed, grow, prune, completion and ablations

**Locations:** [align.go](../../gstyle/domain/patterns/align.go#L102), context/order/matching/evidence/seeding/grow/prune 102–502, variants/stages/scoring/entrypoints706–823. **Purpose/output:** deterministic partial node bijection and coverage, not maximum isomorphism. **Activation:** implemented/Baseline default; five `AlignVariant` ablations library-only in inspected callers. **Inputs/dependencies:** PDGs and matching **full** WL state; deepest common level, original adjacency. **Parameters:** no numeric cutoff inside Align.

```text
h=WL pair levels; use colors round[h-1]
DFS ordinals: roots (no incoming edge) sorted(color,index); follow out neighbors
 sorted(tag,color,index), smallest first; then remaining cycle/disconnected nodes by index
matching fwd/back=-1
unique seeds: for sorted color keys with exactly one A and one B node, link if both free
pass in A ordinal order: choose free B of same color with no forward conflict;
 score mirrored edges to already matched neighbors; max score then lower B ordinal
settle evidence passes until no move, then optional ONE greedy pass allowing score0
prune: count missing mirrored edges BOTH directions among matched endpoints;
 repeatedly unlink worst pair (highest violations, ties highest A index) until zero
Baseline stages:
  seed deepest -> settle deepest (greedy) -> prune -> seed/raw settle(no greedy)
  -> prune raw -> complete -> final prune
complete: only unmatched Call/Lit/Field A; choose unmatched SAME KIND B (color may differ),
 agree>0 and no forward conflict; max agree/tie ordinal; reverse conflict checked only strict variant
final pairs sorted A index; coverage=floor(1000*pairCount/max(nA,nB,1))
LabelsOnly: raw seed/settle no greedy ->prune; then complete/final
NoFinalPrune: baseline except omit final prune
CompleteChecked: baseline with strict reverse-conflict completion
CoarseToFine: deepest..raw grow+prune EACH level, greedy only deepest; then complete/final
Combined: CoarseToFine + strict completion
```
**Limitations:** greedy/non-optimal, node-index tie dependence in symmetric graphs; forward-only candidate score may later be pruned for reverse edges. Parallel edge multiplicity is counted in violations but hasEdge is Boolean existence; not a multiplicity bijection verifier. Unmatched edge endpoints do not create conflicts. **Cost:** repeated node-pair/adjacency scans, conservative `O(n³*d²)` bound for repeated matching/prune scans; no scalable optimality claim. **Tests:** [align_test.go](../../gstyle/domain/patterns/align_test.go#L271) coverage271–294, symmetric permutation296–328, pruning330–349, differing sig completion351–374, variants405–419, exact stage names422–437. [perf test](../../gstyle/domain/patterns/perf_regression_test.go#L330) 330–343 finite staged/untraced equality. **Fixture `GP-26`:** completion partner with reverse-only conflicting edge; inspect CompleteChecked versus NoFinalPrune before/after final pruning. Single matching survives linked-vs-loose two-node graph, so coverage need not preserve all graph edges.

## `patterns.alignment-holes` — difference taxonomy and column compaction

**Locations:** [align.go](../../gstyle/domain/patterns/align.go#L19), HoleKind/prefix/rank19–88, nodeDiffs/hole tables510–698; [cluster.go](../../gstyle/domain/patterns/cluster.go#L298), table/column helpers298–427. **Purpose/output:** substitutions on matched nodes and multi-member columns. **Activation:** implemented/default alignment/cluster/clone bridge. **Inputs:** alignment pairs, full PDG node fields. **Parameters/dependencies:** type/method/free_fn/literal/field/op/effect; exact triples group pair holes.

```text
callee diff only when BOTH IDs nonempty and unequal;
 method hole if node A Call and either callee's final path segment has >=2 dots,
 otherwise free_fn (also covers function-valued Lit)
Lit text diff only if A.CalleeID empty; Field Detail diff;
Op diff ONLY both Details start cmp: and unequal -> HoleOp(suffixes)
TyClass diff ONLY both nonempty unequal -> one flat Type hole
effect diff ONLY both Call and unequal uint16; zero->pure, flags fixed order names
group by (kind,A,B); collect pair sites in A-index order;
sort pair holes(first A site,rank type/method/free/literal/field/else5); per-kind numbering
cluster columns group by (kind,template-side A), NOT by each site or full value vector;
 first site=min; for each joined member keep FIRST encountered B, others ignored;
 missing hole -> template A; sort(first site,kind rank,template A); number per kind
```
**Limitations:** repeated template value mapping to multiple B values conflates columns; not consistency-enforced anti-unification. Flat TyClass cannot represent nested named type substitutions; production Field/Call often have empty TyClass. Effects excluded from WL but become holes. Pair HoleEffect uses E prefix/rank5; cluster maps OMIT HoleEffect -> implicit rank0 and **X** prefix. Equal pair sort keys lack a tertiary key (effect/op same site/rank could be nondeterministic). **Cost:** O(pairs+holes log holes), columns linear then sort. **Tests:** [align tests](../../gstyle/domain/patterns/align_test.go#L89) 89–269 operator/method/free/literal/type/repeated triple; 376–403 ordering; [effects tests](../../gstyle/domain/patterns/effects_test.go#L29)29–59; [cluster tests](../../gstyle/domain/patterns/cluster_test.go#L216)216–263 template fallback/ordering. **Fixture `GP-27`:** template literal1 twice versus member literal2/literal3 -> two pair triples, one column with first B. Same-site effect+op synthetic hole table exposes missing rank tie; effect cluster column is X0, not E0.

## `patterns.cluster-construction` — top-three templates and ownership

**Locations:** [cluster.go](../../gstyle/domain/patterns/cluster.go#L227), seed/flat total similarity227–297, template ranking433–527, prepare/loop533–583. **Purpose/output:** template-first members, coverage and columns; each function at most one cluster. **Activation:** implemented/default and clone bridge via buildCluster without adjacency. **Inputs/dependencies:** selected adjacency, canonical/full WL, alignment/columns. **Parameters:** top **3** templates, coverage>=600 default.

```text
prepare: Canonicalize all, cache.Get canonical or NewWl and cache.Put
free = all vertices that occur in selected adjacency
while seed exists: choose most positive free-degree, tie lowest input index
 group=seed + free neighbors, ascending (NOT transitive component)
 rank ALL group templates by sum FLAT similarity to other group members descending,
 tie lowest index; try first min(3,group size)
 for each: Align(template,every other group member); join coverage>=MinCoverage
 pick largest joined count, then greatest total coverage; exact tie first ranked template
 if no joined: retire ONLY seed
 else emit template-first cluster (coverage1000), others group order; retire joined+template
return discovery order (NO final largest-first sort despite comment)
```
**Limitations:** no requirement every member pair reaches similarity threshold; a candidate template can be a nonseed, align members not adjacent to it. Coverage keeps topology-aligned pairs, not equivalence. Seed may survive if not selected in winning cluster. **Cost:** flat-ranking comparator recomputes totals; at most3×group-size Align calls per iteration, worst superlinear; no measured bound. **Tests:** [cluster tests](../../gstyle/domain/patterns/cluster_test.go#L74)74–89 star rather than chaining; [multitemplate test](../../gstyle/domain/patterns/cluster_multitemplate_test.go#L11)11–47 only asserts a cluster containing0/1 with coverage floor0; does **not** prove medoid-failure rescue described by comment. **Fixture `GP-28`:** seed A, neighbor templates B/C, group lacking B-C selected edge; inspect accepted members at coverage600 and ownership after first winner. Contrast clone transitive groups.

## `patterns.candidate-inference` — signature join, suppressions, substance and scoring

**Locations:** [candidates.go](../../gstyle/domain/patterns/candidates.go#L344), index344–369, owner/trait judges377–650, effects/score678–713, finish839–881, cluster inference931–1433; [facts.go](../../gstyle/domain/patterns/facts.go#L189)189–198. **Purpose/output:** trait_method/capability_set, generic_fn, parameterize or Suppressed; FixSpecs are proposals, not validated edits. **Status/activation:** implemented/default; fn_param reserved/not constructed in inspected mining code. **Inputs/dependencies:** all facts+sig groups, cluster columns and coverage. **Parameters:** 2 calls substance, SingleCallGuard false, MaxHoles3; score integer/float behavior below.

```text
sort nonnil PDG facts(path,line,ID) before clustering; index facts byID,
 workspace types from nonempty SelfTy, signature groups by key
for method/free columns: distinct values must ALL resolve to facts;
 require some receiver, >=2 owner SelfTy, same owner package (bare names tolerated)
 if all Implements -> hidden "all ... same interface method" (bool, no interface ID)
 else all definitions same SigKey and key found in groups -> trait verdict
>=1 verdict -> trait_method (1) or capability_set (>1); lift=min group.ScoreMilli
no verdict and hidden -> Suppressed if reason starts "all ", else nothing
no hidden -> genericFn before parameterize:
 both reject all Implements, boilerplate, insufficient substance
 substance calls>=2 OR singleCallGuard && calls==1 && any nonParam Data input to call
 boilerplate: ID segments ffi/raw/bindgen*, last segment main, tests ID/path directory;
 no blanket _test.go rule here
 generic: at least one Type column ALL values in workspace SelfTy set;
 all NONtype columns method/free with ALL callees external to fact index;
 other type columns may contain external values; score /2
 parameterize: holes<=MaxHoles, supports zero columns (exact clone); score /3;
 NO compatibleEffects check in ordinary parameterize path
Breakdown coverage=floor(uint32 sum member coverage/member count); support=len sites;
 holes=len columns; base=(1000*ln(max(1,support))+lift)*coverage/1000;
 holes>3 -> multiply3/holes; trait definition effect mismatch ->divide2;
 round float with math.Round ->uint32; low lift<500 adds counterevidence
Fact EffectClass = EffectKinds set + mutation if Mutates; empty treated pure
sort candidates stable descending score then lexicographic Sites(path,line,ID,name);
 suppressed by sites then reason; no dedup
```
**Limitations:** same-interface claim rests only on Implements bool; actual conversions never set it. Summary effects likewise unset; trait mismatch penalty not rejection. Empty Params only globally defaults; partial Params can set MaxHoles0 unintentionally. generic Type membership often impossible with erased/empty production TyClass, but not proven wholly dormant. Site sorting loses template-first member order for display. **Cost:** indexed lookup plus clustering; scoring/output sorting O(C log C); uint32 coverage sum unchecked. **Tests:** candidate family indexed only, assertions not reviewed. **Fixture `GP-29`:** two two-call functions with zero holes -> ordinary exact-clone parameterize; same IO/unknown union changes do not reject ordinary path, while bridge does. Two different interfaces marked Implements=true suppress without identity proof. **Gaps:** no general preservation proof, Rust parity or production generic reachability census.

## `clone.abstraction-bridge` — effect gate and one cluster per group

**Locations:** [cloneparam.go](../../gstyle/domain/patterns/cloneparam.go#L4), all helpers/entrypoints4–114; registry report155–170. **Purpose/output:** derive up to one parameterize candidate per connected clone group; separate from clone detection and AST rewriting. **Activation:** implemented/default both application miners, using their different converted facts. **Inputs/dependencies:** group IDs, corpus facts with PDGs, default/library Params; prepare/buildCluster/parameterize. **Parameters:** effect union must match **before** alignment/subset selection, coverage/default hole/substance limits as above.

```text
require original group>=2; resolve nonnil facts with nonnil PDG in group order; require>=2
OR Effects over ALL nodes of EACH function (not only Call despite comment)
 reject if any union differs from first (unknown equals unknown allowed; zero equals zero)
prepare canonical graphs without cache; buildCluster on ALL group indices,
 bypass ordinary retrieval/Mineable/scale/cosine/similarity adjacency requirements
if joins: sorted sites selected by cluster; call ordinary parameterize (not trait/generic join)
```
**Limitations:** union equality forgets node/ordering/count/location effects and allows missing effects as pure; gate can reject entire group even if a compatible subset could join. Ordinary miner lacks this gate; clone safety not a global refactor property. It calls PDG alignment/columns, **not `AntiUnify`**; AST anti-unification happens only later in fixer and need not act on same sites. Duplicate parameterize proposals not deduped. **Cost:** per-group full prepare, template ranking and <=3 template align passes. **Tests:** [cloneparam_test.go](../../gstyle/domain/patterns/cloneparam_test.go#L32)32–104 too-small/missing/noPDG/candidate/skip; positive fixture's “different literal” is actually **Op.Detail**, not Lit, so that difference does not establish a literal hole. [effects_test.go](../../gstyle/domain/patterns/effects_test.go#L61)61–110 pure/IO equality and classifier assertions. **Fixture `GP-30`:** groupA(IO),B(IO),C(pure) whose A/B align -> whole bridge rejects; ordinary miner may still propose A/B. Equal IO union in different call locations is not safety proof.

## `clone.inconsistent` — banded re-scoring

**Locations:** [inconsistent.go](../../gstyle/domain/patterns/inconsistent.go#L18), entire procedure18–150. **Purpose/output:** retain whole clone groups containing a suspicious pair. **Activation:** implemented/default registry. **Inputs/dependencies:** groups from AST clone path, raw PDGs, fresh full flat WL. **Parameters/procedure:** build full WL for all resolvable group IDs, all unordered pairs, skip missing WL, flag if **900<=flat score<950**, stop on first; candidate with>=2 resolvable Sites(Path/Line/Name), score600, no FixSpec. **Limitations:** no name/AST/LSH/scale checks during re-scoring; reexamines whole connected group, not stored accepted edge list. 899 is not suspicious; 950 is not suspicious. **Cost:** O(group² histogram work)+WL construction. **Tests:** inconsistent test family indexed only. **Fixture `GP-31`:** one pair at949 causes entire group suggestion;950/899 do not. Neighborhood clone groups would still be flat re-scored if library caller supplied them; production not neighborhood.

## `patterns.wl-cache` — semantic key, persisted state and invalidation

**Locations:** [wlcache.go](../../gstyle/domain/patterns/wlcache.go#L24), all methods24–194; cluster prepare533–547; patterncheck openWlCache103–113. **Purpose/output:** reuse full WL rounds but rebuild graph/current attached PDG. **Activation:** implemented/report CLI --cache opt-in; fixer and raw clone detector do not consume this cache. **Parameters:** format/computation version2, FNV uint64, JSON map; missing file cold, version mismatch ignored, parse/read error aborts CLI, save error ignored.

```text
key: FNV fold bytes of each node Kind/TyClass/SigClass/CalleeID/LitKind/Detail
 in node order, append byte0xff separator after EVERY field;
 write "|" separator field then each edge From/To/Kind/ArgPos as strings in edge order;
 OMIT Line and Effects; hex uint64 string, no collision verification
Get nil ->miss without counters; actual miss increments; hit rebuilds working graph,
 hists from stored rounds, attaches CURRENT pdg/nodeCount plus stored diameter/calls/charVec
Put nil no-op; store rounds/diameter/calls/charVec (slice references, not defensive copy)
Load matching version replaces entries; JSON shape not otherwise validated
```
**Limitations:** order-sensitive key despite possible isomorphic reuse; omitted Effects currently absent from WL computation, but current PDG restores effects for holes. Manually bump version, not automatic source hash. Corrupt-but-valid JSON rounds can cause index/shape failures; no semantic validation/collision policy. **Cost:** key O(content bytes), hit graph/hist rebuild; persisted rounds up to4n plus vectors. **Tests:** [wlcache_test.go](../../gstyle/domain/patterns/wlcache_test.go#L23)23–141 hit1000, changed-node miss, line shifts retained, save/load weighted score, missing file, finite cluster member equality. Not universal correctness. **Fixture `GP-32`:** move lines/change Effects -> same key but current effect holes; reorder edges -> different key; valid JSON with short rounds exposes validation gap (design only).

## `detectors.registry` — reachability index, not verified detector contracts

**Locations:** [report.go](../../gstyle/domain/patterns/report.go#L107)107–197 and [candidates.go](../../gstyle/domain/patterns/candidates.go#L43)43–184/207–242. **Purpose/output:** establish union of registered candidate families and activation; **partial record**: most internal procedures/thresholds unresolved. **Inputs:** prepared facts/type options; package/AST hit producers. **Activation:** all builders default once per Run; production reachability conditional on facts; library Implements and effect branches dormant through inspected conversions. **Parameters:** default detector-specific thresholds unresolved except below records. **Go orchestration pseudocode:** call each listed builder once; append/sort results; no run-mode exclusion. **Rust/reference:** unresolved/not CCGraph. **Cost:** sum of builders, internals unknown. **Tests:** all 71 test files enumerated in coverage; names alone do not prove assertions. **Examples/fixture `GP-33`:** construct one hit for each family, test registry inclusion separately from frontend production ability. **Limitations:** registration is not proof of productive guards or FixSpecs.

| Kind / stable ID | Caller and producer | Current classification |
|---|---|---|
| trait_method / capability_set / generic_fn / parameterize | MineCached inference | Implemented default; branch details above |
| fn_param / `patterns.fn-param` | constant only | Reserved, no construction in inspected source |
| type_switch / `detectors.type-switch` | Run before registry; AST TypeSwitches | Default wiring, internals unreviewed |
| enum_dispatch / `detectors.enum-dispatch` | Run before registry; AST EnumDispatches | Default wiring, internals unreviewed |
| guard_clause / `detectors.guard` | registry, AST GuardClauses | Default wiring, internals unreviewed |
| primitive_obsession / `detectors.primitive` | registry, Params | Default wiring, internals unreviewed |
| value_object / `detectors.value-object` | registry, Params | Default wiring, internals unreviewed |
| factory / `detectors.factory` | registry, FactoryLits | **Dormant unsatisfiable**, verified below |
| specification / `detectors.specification` | registry, SpecRules | Domain procedure verified below; frontend unreviewed |
| missing_identity / entity_identity / mutable_identity / `detectors.entity` | registry, type options/entity hits | Wiring verified, internals unreviewed |
| domain_service / `detectors.domain-service` | registry, package type option | Wiring verified, internals unreviewed |
| anemic_model / `detectors.anemic` | registry, type option + service option | Wiring verified, internals unreviewed |
| aggregate / repository / `detectors.ddd` | registry, AggregateMods/DbCalls | Domain procedure below; frontend unreviewed |
| nilerr / forcetypeassert / typednil / `detectors.gostatic` | registry, extracted hits | Wrappers/suppression verified; AST predicates unreviewed |
| dependence_cluster / `detectors.dependence-cluster` | FindDepClusters -> DepClusterCandidates | Default wiring, internals unreviewed |
| mined_rule / `detectors.association` | BuildCallSets -> MineRules -> FindViolations | Default wiring, thresholds/internal algorithm unreviewed |
| deviant_behavior / `detectors.error-beliefs` | collect sites, overwrite FuncID=f.ID -> MineErrorBeliefs -> FindBeliefViolations | Default report; fixer sites dropped; internals unreviewed |
| ccgraph_clone / `clone.accept-and-group` | shared cloneGroups + bridge | Verified stages above |
| inconsistent_clone / `clone.inconsistent` | shared groups + raw PDGs | Verified band above |
| taint_flow / `detectors.taint` | FindTaintFlows -> candidates | Default wiring, internals unreviewed |
| barrier_slice / thin_slice / chop / `detectors.slicing` | respective Find -> candidates | Default wiring, traversal/config internals unreviewed |
| alattin_rule / `detectors.disjunctive` | call sets -> MineDisjunctiveRules -> violations | Default wiring, internals unreviewed |
| obligation / `detectors.obligation` | FindObligationViolations -> candidates | Default wiring, internals unreviewed |

32 declared kinds: 31 nonreserved kinds accounted at wiring level; productive reachability **not** verified for every kind. Thirteen fixer registrations below are narrower than those 31.

## `detectors.ddd` / `detectors.factory` / `detectors.specification` — domain hit grouping variants

**Locations:** [ddd.go](../../gstyle/domain/patterns/ddd.go#L14), all symbols14–360. **Purpose/outputs:** domain-level suggestions from already extracted hits; no compiler semantic analysis here. **Activation:** default registry; implemented, **factory dormant**. **Inputs/dependencies:** FuncFacts.AggregateMods/DbCalls/FactoryLits/SpecRules; AST producers unreviewed. **Parameters/procedure:**
```text
aggregate: sorted unique nonempty type names per function -> each type pair ->
 set of function IDs; require support>=2; candidate score400, coverage1000,
 support distinct IDs, no FixSpec; sort support desc then Observation
repository: each function with DbCalls nonempty -> one candidate score400,
 support raw hit count, sorted unique displayed Call texts; no FixSpec
factory: h.TypeName nonempty AND NumFields>=5 AND NumFields<=4 AND HasLogic;
 impossible for every integer -> no qualified groups/candidates in current implementation
 latent grouping keyed(TypeName,DeclFile), distinct ID support>=2, score450,
 FixSpec File=DeclFile, Line=first encountered hit.Line; helpers still callable directly
specification: nonempty RuleKey+TypeName -> group by(rule key,type), distinct function IDs;
 first encountered hit/file retained; support>=2 ->score450, coverage1000;
 FixSpec first hit with type/varname/cond/rulekey params; sorted support then Observation
```
**Limitations:** factory dormant is not absent implementation or test failure; changing thresholds deferred to later phases. Key/first-hit selection depend on input ordering (Run prepares ID order). Specification group does not require same file despite one primary FixSpec. **Cost:** aggregate sum per-function type-pair counts; other grouping linear in hits plus sorting. **Tests:** ddd/specification families indexed only, assertions not reviewed. **Examples/fixture `GP-34`:** field counts4/5 both fail factory; positive aggregate two IDs modifying A/B, negative one ID; same specification key/type in two files shows single primary file. **Divergence:** actual activation predicate contradicts optimistic “factory exists/runs” summaries; reference not applicable.

## `detectors.gostatic` — hit wrappers and narrow suppression language

**Locations:** [domain gostatic.go](../../gstyle/domain/patterns/gostatic.go#L30)30–143; [adapter gostatic.go](../../gstyle/adapters/gopatterns/gostatic.go#L504), suppression504–564 (AST detectors1–499 **unreviewed**). **Purpose/output:** report extracted bug hits with per-function comment suppression. **Activation:** implemented/default wrappers; detector semantics partial. **Inputs:** SuppressedKinds and three hit lists. **Parameters:** scores nilerr800/forcetypeassert700/typednil750, support1, coverage1000.

```text
read ONLY FuncDecl.Doc comments; aggregate parsed known kinds (no dedup)
//lint:ignore prefix: whitespace tokens; trim one trailing comma; stop at first
 token not exactly nilerr/forcetypeassert/typednil (reason begins)
// cyclo-allow( prefix: require "):"; comma-split interior, trim, retain known kinds
for each wrapper: if exact kind present in suppressed slice skip WHOLE function;
 else candidate per hit with hit-line site/range, function ID/name; no FixSpec;
 sort local candidates by site Line, then global orchestration sort
```
**Limitations:** compact `nilerr,typednil` is not two lint-ignore tokens; no wildcard/global suppression for clone/graph/domain families from this parser. Unknown directives silently ignored. Wrapper inference not proof frontend hit is correct. **Cost:** linear comments/hits + sorts. **Tests:** nilerr/typednil/force assertion families index-only; no assertion proof claimed. **Fixture `GP-35`:** `//lint:ignore nilerr, typednil reason` versus `//lint:ignore nilerr,typednil reason`; only spaced tokens parsed; same directive does not suppress clone suggestions.

## `rewrite.dispatch` / `rewrite.orchestration` — application mechanics and re-mining

**Locations:** [fixdispatch.go](../../gstyle/adapters/gopatterns/fixdispatch.go#L16)16–58; [patternfix cli.go](../../gstyle/application/patternfix/cli.go#L63), phases63–363, mine/filter378–446, apply448–535, parser574–595; [candidates.go](../../gstyle/domain/patterns/candidates.go#L207)207–254 rank. **Purpose/output:** FixSpec -> source transform/diff/write, not verified semantic preservation. **Activation:** implemented/fix opt-in, dry-run default; --apply writes; --phased optional. **Inputs/dependencies:** candidate specs, filesystem, unreviewed per-kind transforms; external gitchanged.NewDiff/Touched internals unresolved. **Parameters:** four phases, at most3 cycles; no test/typecheck invocation in application orchestration.

```text
ApplyFix nil/unknown -> error; otherwise dispatch
13 keys: guard_clause,value_object,parameterize,trait_method,capability_set,
 enum_dispatch,generic_fn,anemic_model,primitive_obsession,type_switch,
 entity_identity,factory,specification (trait/capability share applier)
parseSpec parses file with comments; parser success != compiler/semantic proof
mineCandidates full extraction/default Run; keep nonnil FixSpec and requested kind
--changed AFTER mining: require Sites nonempty; test ONLY Sites[0] range in diff
group specs by File (map iteration, not sorted); sort rank then Line DESC within kind
apply sequentially to updated bytes; per-spec error warning/skip; count only byte changes
--apply write file0644; else show diff; no atomic multi-file transaction/rollback
phases:
  guard+primitive; value; factory/spec/missing/entity/service/anemic/type/enum/trait/capability/generic;
  parameterize
first cycle EACH phase mines all requested paths; later nonparameter phases prior-cycle dirty files;
 parameterize always all opts.paths; update dirty only at END of cycle
phased applyAndTrack: file error silently continues, context cancellation returns partial count;
 runPhasedCycle checks context before next phase; no guaranteed surfaced error in final phase
phased dry-run: single mine, group specs by phase, apply each group to ORIGINAL file bytes
```
**Limitations:** file ordering nondeterministic; across-kind stale line coordinates can shift despite within-kind bottom-up order. Accepted --kind missing_identity/domain_service etc need not have a dispatch key/FixSpec. Same-file parameterize dispatcher re-detection below contradicts “no re-detection” docs; dry-run phased result does not simulate cumulative applied phases. **Cost:** multiple compiler loads and file parse/transforms, internals unknown. **Tests:** application/patternfix and dispatch test bodies indexed only. **Fixture `GP-36`:** two files/specs and same-file cross-kind edits that shift lines; trace spec ordering and failures. One changed nonfirst site of multi-site candidate does not retain spec. **Gaps:** no behavior-preservation proof; every per-kind rewrite body except small parameterize entry remains unreviewed.

## `rewrite.ast-antiunify` — limited syntax generalization

**Locations:** [antiunify.go](../../gstyle/domain/patterns/antiunify.go#L18), all symbols18–450; caller [paramfix.go](../../gstyle/adapters/gopatterns/paramfix.go#L1326)1326–1350. **Purpose/output:** template AST plus ordered per-occurrence substitutions; not PDG clone bridge. **Activation:** implemented/fixer call (partial wiring below), library API. **Inputs:** AST nodes, optional identifier name map (not symbol objects). **Parameters:** fresh `holeN`, no memoization/coalescing identical substitution pairs.

```text
nil both ->nil; one nil or concrete-type mismatch/unsupported ->fresh Ident hole
Ident same name OR renames[A.Name]==B.Name ->copy A name; else hole
BasicLit same Kind+Value ->copy; else hole
Binary same Op -> recursively X,Y, else hole
Call same arity -> recursively Fun,Args; Ellipsis NOT compared/copied
Assign same Tok and LHS/RHS lengths -> recurse lists; otherwise whole-node hole
ExprStmt recurse X; Return same result length recurse, else whole hole
If recurse Cond/Body/Else; Init NOT visited/copied
For recurse Init,Post as statements, Cond as expr, Body as block; rejects certain nil results
IncDec same Tok ->recurse X, else whole-node hole
DeclStmt: only GenDecl same Tok/spec count and ValueSpecs equal names+Ident-only types
 (both nil types equal); initialization Values NOT compared; return original A declaration
Block: equal lengths; recurse corresponding statements; if any becomes nonStmt ->nil
unifyStmt cannot represent an Ident hole as statement ->nil (substitution already appended)
unifyExpr nil/nonExpr fallback creates fresh expression hole; partial substitutions not rolled back
TemplateString returns fmt.Sprintf("%T",template), NOT a rendered template
```
**Limitations:** Selector/Unary/Range/Switch/etc unsupported; no claim “most specific” or reconstructability for arbitrary AST. Nil typed Block handling can dereference nil after blocksCompatible(nil,nil)=true if called that way. Missing If.Init, call Ellipsis, declaration initializers violate general preservation of fields. **Cost:** O(visited syntax) with allocation per fresh hole; no optimality proof. **Tests:** antiunify test bodies indexed only. **Fixture `GP-37`:** `if x:=f(); ok {g()}` versus same no Init produces template without Init; `var x int=1` versus `=2` compares equal declarations; variadic/nonvariadic same call args loses Ellipsis. These are unexecuted source consequences, not instructions to fix during audit.

## `rewrite.parameterize` — inspected prefix and explicit rewrite safety gap

**Locations:** [paramfix.go](../../gstyle/adapters/gopatterns/paramfix.go#L54), FixParameterize/collect/guards54–270, antiUnifyHoles1326–1350; [fixapply.go](../../gstyle/adapters/gopatterns/fixapply.go#L92) `applyParameterizeFix`92–103. **Status:** partial record; rewrite helpers271–1325 and other fixapply symbols **unreviewed**. **Activation:** default Parameterize dispatch in fix, plus library function; re-detection observed in source, no execution. **Purpose/inputs/output:** source rewrite of same-file free-function pairs, may differ from miner's selected group. **Parameters:** maxParamHoles3, adjacent functions, same signature/no closures/no named results (called helpers' details unresolved).

```text
dispatch ignores candidate site/group/line: parse file, FixParameterize(..., candidates=nil)
free funcs only, Body nonnil; source declaration order; all i<j pairs
nil candidate allowlist ->all; nonempty list ->only Parameterize site's Name pairs both directions
skip funcs already used by name; pairAllowed; paramEdit:
 sameSignature helper passes, no FuncLit in either body, no named results;
 buildRenames; antiUnifyHoles -> discard returned TEMPLATE, use only substitutions
 require substitution sides ast.Expr; diffPair requires 1..3 holes and ALL sides Ident
 require only whitespace or closed comments between function ranges
 build replacement helper (UNREVIEWED); on success mark both used; range a.Pos..b.End
apply collected text edits (UNREVIEWED helper), format.Source or error
```
**Limitations:** exact-clone zero-hole proposal from miner cannot pass diffPair. Literal-hole proposal cannot pass allIdentHoles. Source allowlist uses display Name which production often qualifies while free function declaration uses simple name, but dispatcher passes nil regardless. Global grouping/proposal does not ensure actual fix selection; unrelated adjacent pair may be rewritten after a spec passes --changed. `format.Source` only syntax/format, not compile/semantics. **Cost:** pair enumeration O(fileFuncs²), helper cost unknown. **Tests:** paramfix family indexed only; no “safe extraction” accepted as verified conclusion. **Fixture `GP-38`:** candidate points at unchanged/nonadjacent pair while another adjacent eligible pair exists in same file; dispatch scans all. Compare miner zero/literal holes with rewrite rejection. Finish helpers before any safety conclusion.

## CCGraph reference contracts

Primary source [CCGraph PDF](../../ccgraph_paper.pdf), SHA-256 recorded in coverage. Read-only `pdftotext -f 3 -l 4` and `-f 5 -l 7` run; existing [paper-pages.txt](../paper-pages.txt) inspected lines150–610 as discovery/transcription, not original-tool output. Page numbers below are **1-based PDF**.

```text
GENERATION (p3 §2.1; p7 §4.1): directed node/edge-labeled function PDGs,
 control/data/execution relationships; Frama-C for C, TinyPDG for Java, DOT conversion.
 Generator version, pointer/memory/control details unresolved; do not invent them.
SIMPLIFY (p5 §3.2): remove system/assistant nodes AND incident edges;
 merge called-function sub-PDG to Fun_Call; exact taxonomy/rewiring unresolved.
FEATURES (p5 Table1): CtrlEdges,ExcEdges,DataEdges,DeclNodes,AssignNodes,CtrlNodes,
 StateNodes,OtherNodes,Reference count; strings ReturnPara,IntroPara,Name.
 State/function-call taxonomy, reference count and parameter serialization unresolved.
FILTER (pp5–6 Alg1/§3.3): minimum and ratio gates; preserve TWO alternatives:
 prose: size/scale -> numerical cosine (.9 reported) -> string JW (reject<.5)
 literal Alg1: size< L reject; min/max<T reject; numerical>GS accept/continue;
              ELSE string>GN accept (GS/GN reversed relative input names).
 node threshold in Alg1 versus six-source-line setting; exact scale T not specified;
 “ten times” is example, not chosen cutoff. String aggregation unspecified.
WL (pp3–4 §2.3, pp6–7 Alg2/§3.4): grammar-category initial labels;
 own label + sorted neighbor label multiset; equality-preserving compression iff
 same sequence; neighborhood direction/edge-kind policy unresolved; depth chosen
 according to smaller PDG diameter, zero/disconnected convention unresolved.
 SCORE alternatives: §2.3 base equal-label cross-product node-pair count,
   sum levels0..h; §2.4 preliminary kernel/|V1 union V2| (union meaning ambiguous);
   Alg2 per iteration samelabel/total, weight=(h-i+1)/h, weighted sum,
   no weight-sum normalization shown, strict >T; round0 policy ambiguous.
 VERIFY (p7 §3.5): printed kernel/min(|V1|,|V2|), >=.9; relation to preliminary
   union/Alg2 score unresolved. Not exact subgraph isomorphism.
 OUTPUT (p5 Fig4,p6 Alg2): clone PAIRS, not transitive groups or refactor proposals.
```

| Stage/IDs | First source-backed difference in Go | Consequence / distinguishing fixture | Rust |
|---|---|---|---|
| graph.go-extraction/go-statements | lexical expression graph, first binding, no execution/memory edges | GP-03/04: reassignment/alias/execution facts already differ | Unresolved |
| graph.canonicalize-* | default off, structural abstraction rewrites, not system/sub-PDG simplification | GP-06/09, cannot call these paper simplification | Unresolved |
| clone.features/name-filter | 7 not9 numeric, only Name not3 strings, no explicit clone size/scale gates | GP-18/19, intermediate coordinates/decisions differ | Unresolved |
| clone.ast-bypass | bypass BOTH numerical/string filters; default report | GP-20, different accepted cheap pairs | Unresolved |
| graph.wl-labels/refinement-depth | FNV collision possibility, explicit salts/direction/edge positions, depth4 cap | GP-14/15, label equivalence/depth differs or paper unresolved | Unresolved |
| graph.wl-flat-score | histogram min vs cross-product, max-count+weight-sum denominator | GP-16, 2/3 count scores differ | Unresolved |
| clone.lsh-retrieval | random hyperplane connected-component retrieval not paper hash compression | GP-22, can omit score-worthy pairs | Unresolved |
| clone.accept-and-group | no separate printed min-count verification, outputs components | GP-23, connectivity does not prove pair/clique relation | Unresolved |
| graph.neighborhood-wl / clone.abstraction-bridge | additional alternate kernel and downstream proposal | GP-24/30, keep distinct from paper clone contract | Unresolved |

These are **divergent / intentionally language-specific / reference-underspecified** comparisons, not implementation equivalence results. Full original-tool reproduction unavailable in this slice.

## Reflection claim reconciliation (scoped checkpoint)

Source document [ccgraph-divergences.md](../../ccgraph-divergences.md). Claim IDs use `clone.claim.*` for discoverability. Historical revision, corpus/config/commands/hardware/raw outputs absent from reflection; PR/merge status not fetched. All performance/quality numbers remain **reported historical claims**, not observed results.

| Claim ID; document range/type | Reconciliation against current source | Remaining evidence |
|---|---|---|
| clone.claim.base;6–8 fidelity/order | **Contradicted-current**: paper has9+3 features, no random-hyperplane retrieval requirement; Go raw clone no explicit min/ratio gate, AST bypass, histogram/max normalized kernel and group output | Paper ambiguity/original tool still unresolved; thresholds alone insufficient |
| clone.claim.ast;14–21 attribution/activation/bypass | **Partially-supported** multiset/Jaccard>=.8 API; **contradicted-current** “only Stage1” and opt-in-production reading: early return skips names; Run uses WithAST | Deckard attribution not verified from original Deckard; runtime .86→1.58s/648 and24→24 unverified historical |
| clone.claim.neighborhood;25–36 method/status/quality | **Confirmed-current procedure** per-node1/2-hop/one round and replacement900; **library-only** in inspected Run; **unverified** PR38/superset/recall-win | Tests log gaps, not superset;24→26/27→29/489→507,127→128 and lossless claims historical only |
| clone.claim.keys;40–46 representation/memory | **Superseded current representation** uint64 row bitset, not int64 map; cannot verify historical string/int transition | 3–4×/70%,5M/VM/OOM fixed lacks artifacts; no measurements reproduced |
| clone.claim.light;50–57 retained-state/equivalence | **Partially-supported** light omits graph/rounds/pdg, reuses vector, retains calls+charVec too; flat score/vector only need its retained fields | Similarity1000 one example not general proof; weighted/alignment/cache not valid consumers;40–55MB historical unverified |
| clone.claim.bridge;62–70 capability/count/status | **Confirmed-current** default group->PDG alignment->parameterize; **partially-supported wording** actual AST AntiUnify not called in bridge, only downstream fixer | 24 clones+36 proposals/PR38 historical, no raw output; no safety or realizability conclusion |
| clone.claim.effects;74–82 extraction/status/safety | **Contradicted-current status** effect schema/builder/alignment/bridge gate present in clean requested HEAD; **partially-supported** callee classifier bits and union equality | “prevents unsafe” unproved: unknown/missing defaults, union loss, ordinary parameterize ungated; classification internals and rewrites unfinished |
| clone.claim.summary;88–101 memory/scale/coverage | Summary numerical/status conclusions inherit above gaps; **unverified-historical** no newly observed scale/quality gain | Connected group count not labeled recall; no benchmark executed |

## Priority distinguishing fixtures and handoff

`GP-01`–`GP-38` above are designs, not newly implemented fixtures. Highest priority:

1. **GP-02/03/04:** conversion fields and real frontend first-binding/nil/loop topology versus hand-built unit PDGs. These identify earliest information loss.
2. **GP-20/22/23:** AST name bypass, actual LSH retrieved/omitted **pair sets**, and transitive group versus verified pairs. Compare intermediates, not group counts.
3. **GP-16/17:** duplicate-color count conventions, denominators/round0 and weighted data-floor absence; preserve paper alternatives.
4. **GP-27/30:** repeated-template substitution conflicts and effect union equality versus per-node effects; ordinary and bridge paths differ.
5. **GP-34/37/38:** dormant factory; AST anti-unify ignored fields; proposal versus actual file-wide rewrite. Review unfinished rewrite helpers before safety claims.

Next source audit work (still phase one, before phase-two specification): complete detector internals/test bodies, normalization middle test region, classifier producer boundary, all rewrite helpers/test families, fixture contents and external application callers. Do not choose final unified behavior from this checkpoint.
