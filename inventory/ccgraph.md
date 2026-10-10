# CCGraph source/reference audit — phase one

## Scope, snapshot and evidence

**Complete for this bounded source/reference slice; partial relative to the workspace-wide phase-one inventory.** This record covers the supplied CCGraph PDF, its comparison to current Go clone detection and Rust WL abstraction mining, and the six reflection extensions. It does not certify the entire analysis inventory, semantic equivalence, original-tool reproduction, benchmark quality or refactoring safety. The accompanying [claim ledger](claims.md) reconciles every distinct reflection assertion, including duplicate summary assertions.

Audit date: 2026-10-10. Only `inventory/ccgraph.md`, `inventory/claims.md` and the permitted `inventory/paper-pages.txt` are owned/written by this audit. No implementation, dependency, baseline, branch or commit was changed.

| Input | Recorded identity |
|---|---|
| Go, independently versioned, clean | `598c7b03366caa0fef70f66aa58e76222eefb8fa`; tree `ae78c5840f334be4ac6825752ef014cc61c99405` |
| Rust, independently versioned, clean | `2c4752ca9c7b992e66d21380600a69f597133687`; tree `5165f9e4ed7ce12fdc7a8d606d954e323fe25775` |
| Parent | Inputs and child directories were untracked; parent HEAD does **not** identify child contents. Children have their own clean tracked snapshots. |
| PDF | SHA-256 `abfd1f66cdac144cfd6a7e6626b0d9bbd302dc603b641afe23ab24e9dc4160c9`; 12 pages; DOI `10.1145/3324884.3416541` |
| Inventory prompt | SHA-256 `a9eb84a87ee9a0a874d4b7911f34010dcbfb41d592c51ae36fc97deea4a1f2c5` |
| Unification plan | SHA-256 `0d07e270158727981af7fb040b733dcb399be033d3a5d35a1da27b91213ac0d4` |
| Reflection | SHA-256 `5d6a20e0b7eef947eb6600790ba79f28cf8e57d9b22bb4df9436f84365eca7c4` |
| Go dependency locks | `go.mod`: `fd2a6d6efea5a2a2941286e993c76157766d0f378aa9ce6a70bfe37c0fa37524`; `go.sum`: `da397e994a67a4ac36550c9e9add6d32eec6d8fdd59d3e0b9ac769ac869d03e8` |
| Rust lock | `Cargo.lock`: `0129fef746f9afd3e157db8f8ea12b3f7f30241396fd64f9a21cbf069f542d5c` |

Instructions read: [inventory prompt](../PHASE_ONE_INVENTORY_PROMPT.md), [unification plan](../ALGORITHM_UNIFICATION.md), [Go AGENTS.md](../gstyle/AGENTS.md) (the only discovered `AGENTS.md`). Claims in these inputs were leads, not proof.

### Observed commands versus unexecuted tests

Actually run: `pdfinfo ccgraph_paper.pdf`; installed `/opt/homebrew/bin/pdftotext -layout ccgraph_paper.pdf inventory/paper-pages.txt`; `pdftotext -v` (Poppler 26.06.0); Python standard-library SHA-256 and page splitting; read-only `git --no-pager` history/show/diff/ancestry/tree queries and `git --no-optional-locks status --short` on both children. The 12 form-feed-delimited pages were preserved in [paper-pages.txt](paper-pages.txt), replacing page separators with `=== PDF PAGE n (1-based) ===` headings; no semantic text repair. Extract SHA-256: `e250ac309eda6703a09c9680c10a8645878da8739a78c9b834f81b9c4e8424e7`.

Tool versions queried: Go `go1.26.2 darwin/arm64` (module requests Go 1.25.0); host Rust `1.99.0 (b940084d7 2026-09-28)` and Cargo `1.99.0`; installed project-pinned `nightly-2026-09-30` reports `rustc 1.101.0-nightly (5c543b0b8 2026-09-29)` via `rustup run`. No build/test/analyzer/benchmark command was run: this was a read-only source/reference audit. All test names below denote **inspected assertions, not passing results**. No dependency install or network fetch occurred.

Relevant dependencies: Go extraction uses `golang.org/x/tools/go/packages` v0.47.0 and Go typed AST; WL, Jaro–Winkler and LSH are in-project code (LSH uses standard-library `math/rand`). Rust driver uses pinned rustc-internal HIR/typeck APIs; core facts/report use locked `serde` 1.0.229 and `serde_json` 1.0.151 (`globset` 0.4.20, `toml` 0.9.12+spec-1.1.0, test `insta` 1.48.0). Compiler/package-loader and serializer internals were not audited. No Frama-C/TinyPDG/GraphKernels version, original CCGraph executable, generator `.dot` corpus or author configuration was supplied or pinned by this audit.

## Decisive findings

1. **Neither current engine is paper-exact.** Go has seven numerical features, only a function-name string, no explicit clone size/scale gate, AST bypass, candidate-retrieval LSH and connected groups. Rust is an abstraction miner, not a separately wired CCGraph clone-pair detector.
2. **The PDF is not a unique executable specification.** Prose AND versus Algorithm 1 OR/reversed threshold names, three different score presentations, multiplicity, round zero and diameter/encoding policies remain unresolved.
3. **Go production reporting enables AST bypass.** The bypass skips **both numerical and name filters**. The plain library API does not establish the CLI default. Fixer conversion omits AST counts and therefore differs from report conversion.
4. **Today’s pair store is a row-word bitset, not an int64-key map.** Local history verifies string → integer → word-store implementations; reported memory/OOM results are not observed audit results.
5. **Full/light WL share the relevant construction and score procedure**, but light retains more than three fields and cannot substitute for alignment/cache/weighted-projection consumers. No current test referencing `NewWlLight` was found.
6. **Effect fields/extraction are merged into current Go source**, despite the reflection’s “not merged” statement. Equality of coarse effect unions, especially equal unknown unions, does not establish safety.

## Reference contracts and all 12 features

All paper citations below use **1-based PDF pages**, not journal/printed page numbers. Equations in the supplied PDF are unnumbered; they are identified by definition/section and displayed expression rather than invented equation numbers.

### `CC-R01` generation and `CC-R02` simplification

**Explicit reference:** p.3 §2.1/Definition 2.1: directed graph `G=(V,E,μ,δ)` with node types and dependency edge types. Control edges connect a controlling node to a node whose execution it controls. Data dependencies cover shared-variable use and assignment/use, including indirect pointers. Execution dependency means one node may execute only after another. Function-level generation: p.4 §3.1. **Reported implementation setting:** p.7 §4.1 uses Frama-C for C and TinyPDG for Java, `.dot` import, Python parsing, Python/C++ matching, Ubuntu 14.04 LTS, quad-core CPU and 8GB memory. These are the paper’s environment, not this audit’s or Cyclo’s benchmark environment.

p.5 §3.2.1 removes automatically generated system and assistant-parameter nodes **and incident edges**. §3.2.2 collapses called-function sub-PDGs into one `Fun_Call` node. Node taxonomy, boundary recognition and redirection/parallel-edge policies are not supplied precisely. The text says merging loses no structural information; that is a paper claim, not a proved invariant. Do not equate our expression transparency/normalization with these generator-specific operations.

### `CC-R03` feature extraction (p.5 Table 1; p.6 §3.3.1)

| Coordinate, exact paper spelling | Paper description | Current Go mapping/absence | Current Rust CCGraph-stage status |
|---|---|---|---|
| `NumOfCtrlEdges` | Control dependency edges | `vec[5]`, Ctrl count | No characteristic-vector stage |
| `NumOfExcEdges` | “excute dependency edges” | **Absent**, no execution edge kind | **Absent**, no execution edge kind |
| `NumOfDataEdges` | Data dependency edges | `vec[6]`, Data count | No characteristic-vector stage |
| `NumOfDeclNodes` | Variable declaration nodes | `vec[0]`, Let; simple `:=` is transparent, so not all declarations | No characteristic-vector stage |
| `NumOfAssignNodes` | Assignment nodes | `vec[1]`, **all Op nodes**, including arithmetic/index/send, not only assignment | No characteristic-vector stage |
| `NumOfCtrlNodes` | Control nodes | `vec[2]`, Branch/Match/Loop/Iterate; Try is counted as other | No characteristic-vector stage |
| `NumOfStateNodes` | “function state nodes” | `vec[3]`, Call; provisional analogy only | No characteristic-vector stage |
| `NumOfOtherNodes` | Other types | `vec[4]`, remaining node kinds | No characteristic-vector stage |
| `NumOfReference` | Number of reference variables | **Absent**, TyClass is not a reference-variable counter | **Absent** as a characteristic feature, even though raw types exist |
| `ReturnPara` | Return parameters | **Absent** from string filtering | No string filtering stage |
| `IntroPara` | Incoming parameters | **Absent** from string filtering | No string filtering stage |
| `Name` | Function name | Short function/method name only | No Jaro–Winkler stage |

Table 1’s “function state” conflicts with §3.3.1’s taxonomy “function call.” Reference variables may mean distinct referenced variables, occurrences, or reference/pointer-typed variables; none is selected here. Parameter string serialization (names/types/order/separators, multiple returns, receiver, normalization) and aggregation over three string fields are unspecified. Missing features must not silently become zero/empty in a purported faithful reference profile.

### `CC-R04` size/scale, `CC-R05` numerical and `CC-R06` string filters

p.5 Algorithm 1 defines `L` as a **node-number** threshold, rejects `sizeof(G)<L`, rejects `min/max<T`. p.6 §3.3.1 reports a **six-source-line** implementation setting (p.8 §4.3.3 repeats excluding fewer than six lines). “one PDG size is 10 times” is an example, **not a declared cutoff**. `T` itself is not fixed in the supplied paper.

p.6 §3.3.1 reports numerical cosine threshold 0.9, after size/scale. p.6 §3.3.2 compares the string parts **within numerically classified categories** and rejects Jaro–Winkler ratios **less than 0.5**. The displayed Jaro equation is `J=(m/|a| + m/|b| + (m-t)/m)/3`, `t` half the transpositions. Displayed Winkler equation is `JW=J+L·P·(1-J)`, default `P=0.1`, `P≤0.25`. Matching window, prefix length cap, zero matches/empty strings and field aggregation are not executable definitions here.

**Conflict:** Algorithm 1 input declares `GS=string threshold`, `GN=numerical threshold`, but lines 8–12 accept if **number similarity > GS**, otherwise if **string similarity > GN**. `CONTINUE` after numerical success implements **OR**, not sequential AND. A “corrected OR” is a distinct interpretation, not the literal algorithm. Algorithm 1 uses strict `>`; string prose retains exactly 0.5. Keep all alternatives.

### `CC-R07` labels, `CC-R08` refinement/compression, `CC-R09` depth/weights

p.6 §3.4 hashes grammar-category initial labels; Algorithm 2 lines 5–8 collects/sorts neighboring labels, prepends own label and compresses. Lines 9–11 require `f(s(v))=f(s(w))` **iff** `s(v)=s(w)`. p.4 Fig.3 shows a common compression dictionary across the two graphs. The graphs are directed and edge-labeled, but the exact use of incoming/outgoing edges, dependency types and operand positions in the WL sequence is not given. Per-node updates appear inside a loop; synchronous versus in-place storage must be explicit in a reference profile.

p.6 §3.4 says “local sensitive hashing” for **label-sequence compression**. It does **not** prescribe a separate random-hyperplane **candidate-retrieval** stage. Approximate compression that merges unequal sequences also contradicts Algorithm 2’s iff constraint unless treated as a different policy.

p.7 §3.4 dynamically selects iteration count according to “the diameter of the smaller PDG,” weight `(h-n+1)/h`. This could select the smaller-by-node-count graph’s diameter or mean the smaller diameter; tie-breaking is not stated. Directed versus underlying-undirected diameter, disconnected/unreachable pairs, path length in nodes versus edges, zero diameter and caps are unspecified. No four-level/400-node cap is prescribed by the paper.

### `CC-R10` kernel/score, `CC-R11` verification and `CC-R12` output

- p.3 §2.3 displays `kr(G1,G2)=Σ_i Σ_j σ(S1,i,S2,j)`; p.4 Definition 2.5 displays `kWL^(h)=k(G1(0),G2(0))+…+k(G1(h),G2(h))`, base kernel counting “same label pairs.” Literal equal-label **cross-product** is `Σ_c A_c·B_c`, not histogram intersection `Σ_c min(A_c,B_c)`. One-to-one equal-label matching has the intersection count but an additional matching contract if structure is enforced.
- p.4 Definition 2.6 (union equation): `similarity=kWL^(h)/|V1∪V2|`, claims range `[0,1]`, uses “bigger than” threshold. Union requires a notion of cross-graph vertex identity or matching. The sum of cross-products over rounds does not generally fit that range.
- p.6 Algorithm 2: after refinement, `ki=sizeof(samelabel(v))/sizeof(total(v))`, `wi=(m-i+1)/m`, `k=Σ_i ki·wi`, accept `k>T`. Definitions of samelabel and total, round-zero inclusion, iteration indexing and normalization by `Σ wi` are absent. For identical graphs with `ki=1`, `m=3`, literal weights `1,2/3,1/3` give `k=2`, contradicting a bounded similarity if no further normalization occurs.
- p.7 §3.5 first refers back to §2’s ratio to total nodes, **then** displays `sim=kWL^(h)/min(|V1|,|V2|)` as an asymmetric Dice coefficient; final acceptance is explicitly **≥0.9**. Does this supplement a preliminary gate, replace it, or use an already normalized kernel? Not specified consistently. Do not normalize twice or replace min with max without recording an interpretation.
- p.5 Fig.4 and p.6 Algorithm 2 output **clone pairs**, not connected components, abstraction proposals, templates or rewritten code. The displayed nested pair loops do not settle self-pair exclusion, duplicate reverse pairs or output ordering.

**No final exact subgraph-isomorphism verifier is prescribed.** “Verifying” in §3.5 is the score/threshold step; approximate matching does not prove behavioral equivalence.

## Paper-stage reference pseudocode (schematic; no policy selected)

This is a trace contract, **not** an implemented reference engine. Undefined policy names below are explicitly unresolved because the PDF lacks a unique choice.

```text
REFERENCE(source_files, generator_config, policy):
  graphs = GENERATOR(functions(source_files), generator_config)  # R01, pp.3–4/7
  for G in graphs:
    remove policy.SYSTEM_AND_ASSISTANT_NODES(G) and their incident edges
    for each policy.CALLED_SUBPDG_BOUNDARY(G):
      collapse to Fun_Call; redirect edges using policy.CALL_REWIRING  # R02, p.5
    Pnum[G] = [#CtrlEdges,#ExcEdges,#DataEdges,#Decl,#Assign,#Ctrl,
               #State,#Other,policy.REFERENCE_COUNT(G)]             # R03 Table 1
    Pstr[G] = [policy.RETURN_SERIALIZATION,policy.INPUT_SERIALIZATION,Name]

  pairs = policy.PAIR_ENUMERATION(graphs)  # self/reverse duplicates/order unresolved
  for (A,B) in pairs:
    if policy.SIZE(A)<L or policy.SIZE(B)<L: continue  # nodes vs six lines
    if min(policy.SCALE_SIZE(A),policy.SCALE_SIZE(B)) /
       max(policy.SCALE_SIZE(A),policy.SCALE_SIZE(B)) < Tscale: continue
    N = dot(Pnum[A],Pnum[B])/(norm(Pnum[A])*norm(Pnum[B]))
        # policy.ZERO_NORM required
    S = policy.STRING_AGGREGATION(JW fields(Pstr[A],Pstr[B]))
        # JW=J+prefix_length*0.1*(1-J), window/prefix/empty policies required
    accept_preprocessing = one of:
      PROSE_AND:          numerical_meets_0.9(N) AND S >= 0.5
      LITERAL_ALGORITHM1: N > GS OR S > GN     # GS=.5, GN=.9 per input meanings
      CORRECTED_OR:       N > GN OR S > GS     # an interpretation, not printed code
    if not accept_preprocessing: continue

    h = policy.DEPTH(policy.DIAMETER, policy.SMALLER_PDG(A,B))
    colors[A],colors[B] = grammar_category_labels(A,B)
    hist[0] = counts(colors)   # explicit trace; scoring inclusion remains a policy
    for r in policy.REFINEMENT_INDICES(h):
      prev = colors if policy.SYNCHRONOUS else policy.IN_PLACE_STORAGE
      for v in A and B:
        sequence = own_label(v) + sort(policy.NEIGHBOR_ENCODING(v,prev))
        colors[v] = common_equality_preserving_compression(sequence)
                    # Alg.2 iff; hash collision handling required
      hist[r] = counts(colors)
      Kcross[r] = sum_c hist[A,r,c]*hist[B,r,c]
      Kinter[r] = sum_c min(hist[A,r,c],hist[B,r,c])  # alternative, not literal double sum
      samelabel[r] = policy.MATCH_COUNT(Kcross[r],Kinter[r],one_to_one_matching)
      total[r] = policy.TOTAL_COUNT(A,B,hist[r])
      ki[r] = samelabel[r]/total[r]
      wi[r] = (h-r+1)/h   # one-based refined rounds; zero/index policy unresolved

    Kdefinition = sum over policy.KERNEL_ROUNDS (including 0 under Def.2.5)
                  of policy.BASE_KERNEL
    Kalgorithm2_literal = sum_r ki[r]*wi[r]   # no weight-sum division shown
    Kalgorithm2_normalized_alternative = Kalgorithm2_literal/sum_r wi[r]
    preliminary_union_sim = policy.KERNEL_FOR_VERIFY / policy.VERTEX_UNION(A,B)
    final_min_sim = policy.KERNEL_FOR_VERIFY / min(|A.nodes|,|B.nodes|)
    decision = policy.VERIFICATION_COMPOSITION(
      Kalgorithm2_literal > Tmatch,
      preliminary_union_sim > Tmatch,
      final_min_sim >= .9)
    emit trace(features, gates, label classes, counts, h, weights, all scores, decision)
    if decision: emit (A,B) as a clone pair
```

Retaining these alternatives is required: choosing AND, intersection, normalized weights, undirected diameter, collision-safe synchronous refinement and min verification would create a **documented interpretation**, not prove original-tool fidelity.

## Current source contracts and activation

### Source index (line numbers tied to snapshots above)

These aliases are used in the fidelity matrix and claim ledger; links go to the actual files.

| Alias | Location and inspected contract |
|---|---|
| G1 | [ccgraph.go](../gstyle/domain/patterns/ccgraph.go): constants 25–38; APIs 40–63; `ccGraphGroups` 74–119; usable IDs 132–141; candidates/AST early return 153–188; name matching 191–244/352–464; light WL/retrieval 252–284; pair verification/union 293–339; candidate conversion 477–514; input conversion 528–543 |
| G2 | [wl.go](../gstyle/domain/patterns/wl.go): constants/hash/labels/tags/refine 15–177; histograms/diameter 184–241; state 244–261; seven features/cosine 265–326; full/light construction 329–389; depth/intersection/flat score/early bound 412–508; control/data projections 524–602; mineable/comparable **abstraction** gates 615–624 |
| G3 | [ccpairs.go](../gstyle/domain/patterns/ccpairs.go): `newCCPairs/add/has/members` 13–48; AST coordinate/count/bypass 56–103 |
| G4 | [asthash.go](../gstyle/domain/patterns/asthash.go): thresholds 25–36, `AstNodeMultiset` 42–60, overlap/Jaccard 74–101 |
| G5 | [lsh.go](../gstyle/domain/patterns/lsh.go): vector 21–47; seeded hyperplanes/signatures 70–105; union/find/groups 134–168; connected bucket components 174–196 |
| G6 | [neighborhood_wl.go](../gstyle/domain/patterns/neighborhood_wl.go): attribution comment 14–19 (not external proof); k/round constants 35–40; BFS 75–106; filtered digest/colors 111–145; histograms 151–167; weights/score 171–213 |
| G7 | [cloneparam.go](../gstyle/domain/patterns/cloneparam.go): resolve/prepare/align 4–33; bridge/rejection 53–78; union-equality effects 84–100; per-group candidates 105–114 |
| G8 | [report.go](../gstyle/domain/patterns/report.go): `Run` 71–94; clone builders 155–169; AST-enabled orchestration 202–211; merge-by-ID 249–260 |
| G9 | [align.go](../gstyle/domain/patterns/align.go): node differences 516–648, effect holes 594–616; hole grouping 657–698; baseline stages/final max-size coverage 744–813 |
| G10 | [cluster.go](../gstyle/domain/patterns/cluster.go): defaults 44–51; pair selection 184–206; columns 317–427; top-three templates/coverage 433–512; canonical/full-WL preparation 533–548 |
| G11 | [pdg.go](../gstyle/domain/patterns/pdg.go): nodes 13–59; only Data/Ctrl 64–69; flags/Effects 76–113; no execution edges 123–129. [facts.go](../gstyle/domain/patterns/facts.go): AstTypes/effect summary fields 28–40 |
| G12 | [extract.go](../gstyle/adapters/gopatterns/extract.go): loader/discovery 100–169; `extractFunc` 245–304; lexical control/bindings/params 327–425. [builder.go](../gstyle/adapters/gopatterns/builder.go): bits 14–31; expressions/opaque closures 36–51; calls/effects 257–282. [stmt.go](../gstyle/adapters/gopatterns/stmt.go): assignments 78–172; if/Try 175–263; loops 265–416; return/wrappers 495–508 |
| G13 | [patterncheck/cli.go](../gstyle/application/patterncheck/cli.go): extraction/Run 71–97, `funcFactsOf` including AstTypes 128–154. [patternfix/cli.go](../gstyle/application/patternfix/cli.go): `toFacts` **without AstTypes** 598–627 |
| G14 | [stdlib.go](../gstyle/domain/quality/stdlib.go): curated table (e.g. strings/bytes/maps/slices marked None 30–39), `ClassifyCallee` 518–531; [local_calls.go](../gstyle/domain/quality/local_calls.go): `prefixKind` 117–125; [evaluate.go](../gstyle/domain/quality/evaluate.go): `NormalizeCallee` 323–328 |
| G15 | [candidates.go](../gstyle/domain/patterns/candidates.go): parameterize guards/proposal/FixSpec 1184–1248. [paramfix.go](../gstyle/adapters/gopatterns/paramfix.go): rewrite entry/allowlist 54–157; safety/diff 167–222; `antiUnifyHoles` 1326–1350. [antiunify.go](../gstyle/domain/patterns/antiunify.go): entry/fresh holes/dispatch 18–135 |
| R1 | [facts.rs](../rstyle/crates/rstyle-core/src/facts.rs): node/edge/PDG schema 235–309 (no node effect field); optional PDG 352–354; merge-by-location/name 365–369 |
| R2 | [wl.rs](../rstyle/crates/rstyle-core/src/wl.rs): constants 12–25; labels/hash/tags 27–69; graph/refine 85–130; histograms/diameter 132–171; full four-level construction 185–202; depth/intersection/score/gates 232–279 |
| R3 | [patterns_report.rs](../rstyle/crates/rstyle-core/src/patterns_report.rs): merge/prepare/mine 69–77; ledger/filter 98–120. [candidates.rs](../rstyle/crates/rstyle-core/src/candidates.rs): six candidate kinds 16–23, PDG clustering 822–836, parameterize 624–660, effect-summary scoring 251–290 |
| R4 | [cluster.rs](../rstyle/crates/rstyle-core/src/cluster.rs): defaults 32–42; rare-call blocking/caps 61–111; pair selection 115–124; single-medoid join 226–243; canonicalization/group ownership 247–279 |
| R5 | [pdg.rs](../rstyle/crates/rstyle-driver/src/pdg.rs): transparent method names 26; build/params/link/bind 169–317; paths/calls 370–468; for_each/macros/local/branch/match/generic assignments 478–669; edge dedup 217–225. [extract.rs](../rstyle/crates/rstyle-driver/src/extract.rs): function eligibility/typeck facts/optional PDG 24–84 |
| R6 | [prep.rs](../rstyle/crates/rstyle-core/src/prep.rs): generated/suppressed removal, static trait-call devirtualization 23–102 |

### `CC-G01` Go frontend adaptation (G11–G13)

Implemented/default report extraction; typed-AST package loader. Function declarations with bodies are discovered per loaded package; closures are opaque PDG nodes, though AST multiset traversal descends into their ASTs. Emit receiver/parameters first, then recursively lower the body. `node(n)` attaches a Ctrl edge from the **innermost lexical** control owner/arm; `data(from,to,pos)` omits missing producers (`none=-1`). `bind` records only the first producer per `types.Object`. Single-valued single-name `:=` resolves transparently to RHS; destructuring emits Let. `=` and compound assignment emit Op with old binding and RHS operands but **do not update the binding**; increment emits an Op without binding update. Branches do not introduce reaching-definition merge/phi nodes. A later use still points to the original producer. This is not a complete flow-/alias-/memory-sensitive PDG or post-dominator control-dependence graph.

Known counter/range loops become Iterate; generic loops become Loop; certain `if err != nil {return err}` become Try. Calls carry signature class, callee ID and one classifier effect bit; resolved receiver occupies argument 0, unresolved callable value may occupy 0. Fields/index/operators/conversions have expression nodes; `defer`/`go` wrap Call with a Data edge. No callee-body sub-PDG expansion or execution edges. Report retains AstTypes and node effects; fixer retains the same PDG pointer/effects but drops AstTypes. Independent function summary `Mutates`/`EffectKinds` are not populated by the inspected report conversion, and are not a substitute for node flags.

### `CC-G02` Go clone retrieval/verification/output (G1–G5/G8)

Purpose: similar-function **groups**, then fixed-score report candidates. Production `patterns.Run → addSingleFunctionCandidates → CCGraphClonesWithAST`; API `CCGraphClones` disables AST; API `CCGraphClonesWithNeighborhoodWL` disables AST and replaces only final scoring. No inspected non-test caller of that neighborhood API was found. Clone thresholds are fixed, independent of abstraction `Params.ThresholdMilli`.

```text
GO_CLONES(pdgs,names,ASTcounts,useNeighborhood):
  ids = sorted IDs having nonnil PDG and at least one node
  if len(ids)<2: return nil
  vec[i] = [Let, Op, Branch|Match|Loop|Iterate, Call, remaining, CtrlEdges, DataEdges]
  shape[i] = dense AST-kind counts on shared coordinates (missing map → no bypass)
  name[i] = Unicode runes of shortName(names[id])
  P = zero words[len(ids)*ceil(len(ids)/64)]
  striped workers evaluate every i<j:
    if shape[i].bypass(shape[j]): P.add(i,j); continue
    if cosine(vec[i],vec[j])<.9: continue    # zero norm → cosine 0
    if either name empty: accept
    else accept JW(name[i],name[j])>=.5
      # greedy matching within max(floor(maxlen/2)-1,0); half transpositions
      # prefix ≤4 runes, boost .1; lower-bound shortcut accepts safely above threshold
    if accepted: P.add(i,j)
  # No six-line, minimum-node, minimum-call, or explicit scale-ratio gate here.
  if P.members empty: return nil
  for i in P.members: flatWL[i] = NewWlLight(pdg[i],vec[i])
  vector[i] = 512 zeros
  for retained round r, color c with multiplicity count:
    vector[i][128*r+c%128] += count*(4-r)
  build 16 tables × 4 Gaussian random hyperplanes, math/rand seed 42
  bucket signature bit=1 iff vector dot plane>=0
  retrieve connected components of bucket co-occurrence (not merely direct bucket mates)
  for every i<j within each retrieved component:
    if not P.has(i,j): continue
    if useNeighborhood: score = neighborhood_score(i,j)
    else: test flat weighted score>=900, with upper-bound early rejection
    if accepted: union IDs in final parent map
  return final components of ≥2, members sorted, groups sorted by first member
```

`AstNodeMultiset` visits the **whole FuncDecl**, including signature and nested bodies, skipping Ident/BasicLit nodes and counting reflected node-type names. It is a multiset, not an AST hash/ordered tree representation. Jaccard is `Σ min(counts)/Σ max(counts)`; missing maps disable bypass even though standalone `AstJaccard(nil,nil)=1`. Dense bypass accepts two present all-zero maps and otherwise first checks `min(total)/max(total)≥.8`, then Jaccard ≥.8. Counts are assumed nonnegative; no input validation establishes this for arbitrary library maps. The unused `astPruneThreshold=.3` is not an active prune stage. The early `return true` at G1:181–182 means bypass skips **cosine and JW**.

Candidate-set monotonicity is source-backed: adding AST bypass never removes a candidate bit. With fixed graphs/hashes, adding indexed vertices cannot split retrieval components or remove previously checked accepted pairs. However group **count** need not be monotone (components may merge), and workload increases are possible, not guaranteed. Do not turn this into labeled-recall evidence.

Cost, source-derived: cheap filter enumerates `n(n−1)/2`; AST pair work O(k) shared kinds, name work up to O(length product). Pair words allocate **`8*n*ceil(n/64)` bytes** plus struct/slice overhead, irrespective of survivor count; at n=7,592 the words alone are 7,227,584 bytes (not a measured RSS). Retrieval vectors cost O(n·512·16·4) for projections; component verification may still reach O(n²). This is not an unconditional avoidance of quadratic work.

### `CC-G03` / `CC-U01` Go and Rust flat WL (G2/R2)

Both implement the following structural procedure; **labels and retained state differ**, so this is not byte-identical whole-engine parity:

```text
hash(bytes) = 64-bit FNV-1a, offset 14695981039346656037, prime 1099511628211
combine(x,y) = hash(LE64(x) || LE64(y)), unsigned wrapping multiplication
edgeTag(kind,pos) = combine(kind==Ctrl ? 1 : 0, uint64(pos))
raw[v] = hash(language_specific_label(node[v]))
in/out adjacency retains multiplicity and tags; invalid high endpoints skipped
D = max finite BFS distance in underlying undirected graph
    (both incoming/outgoing), max over components; empty/edgeless →0
    if node_count>400: D=4 without BFS
Hpair = clamp(min(DA,DB)+1,1,4)
GO retained levels = clamp(D+1,1,4); RUST retained levels=4 always
round[0] = raw
for each retained subsequent round, synchronously:
  partsIn = sorted [combine(edgeTag, prev[neighbor]) for incoming edges]
  x = fold(combine, combine(prev[v],0x1f),partsIn)
  partsOut = sorted [combine(edgeTag, prev[neighbor]) for outgoing edges]
  next[v] = fold(combine, combine(x,0x2e),partsOut)
  hist[round] = sorted color→count
I(r) = sum_c min(histA[r,c],histB[r,c])
w(r) = Hpair-r, for r=0..Hpair-1          # raw round has largest weight
score_milli = floor(1000 * sum_r w(r)*I(r) /
                    (max(nodesA,nodesB)*sum_r w(r)))
zero denominator →0
```

Go labels: `call:<builtin/std/local/unknown>:<SigClass>`, `lit:<LitKind>`, `op:<Detail before colon>`, `param:<TyClass>`, otherwise lower-case NodeKind value. Call scope uses the presence of a dot in the stripped package path, an implementation heuristic, not resolved stdlib ownership. Effects and literal values are excluded. Rust: `call:<normalize(callee_sig).key>` or **callee ID if signature missing**, or `?`; `macro:<macro_name>`; `lit:<lit_kind>`; `op:<detail before colon>`; `param:<class_of(type)>`; otherwise Debug NodeKind (`Let`, `Branch`, etc.), not Go’s lower-case spelling. Thus raw-kind labels and signature-less named calls need explicit adaptation before cross-language color equivalence can be expected. Rust frontend emits bare operator details (`+`, `=`, etc.) whereas Go usually emits coarse `arith`, `assign`, etc.; optional normalizers do not erase all such differences by default.

FNV compression is deterministic but finite 64-bit hashes have possible collisions; neither inspected implementation stores original sequences to enforce the paper’s **iff** collision policy. Go negative endpoints are not checked before adjacency indexing (Rust endpoints are unsigned); malformed library graphs are not generally validated here. Numerical accumulation uses uint64/u64 for similarity; arbitrary-size overflow is not guarded by these scorers. Within practical allocation limits this is an engineering assumption, not a reference guarantee.

Go `similarityAtLeast` stops when `(accumulated + remaining_weight*min_nodes)*1000/den < limit`, otherwise computes the same integer-thousandths verdict; for two empty graphs it returns `limit==0` while `SimilarityMilli` returns zero. Clone inputs are nonempty and use 900. Full/light relevant fields follow the same buildGraph/diameter/refine/histogram functions; light keeps `hists`, `calls`, `diameter`, supplied `charVec`, `nodeCount`, omitting `graph`, `rounds`, `pdg`. Structural source reasoning supports equal flat score/vectorization for the same graph and correct supplied features, absent overflow/collision issues common to both; it is not a measured memory reduction or all-consumer replacement proof.

BFS diameter costs O(V·(V+E)) below the cap; refinement costs O(H·(V+E+Σ_v deg(v)log deg(v))), histograms up to O(H·V log V); flat pair intersection O(H·(distinctColorsA+distinctColorsB)). Rust’s BFS uses BTreeSet frontiers, adding ordered-set costs. Light drops retained adjacency/colors but still constructs them transiently; it does not skip refinement construction.

### `CC-G04` neighborhood alternative (G6/G1)

For k=1,2, for **every root** collect up-to-k-hop nodes by BFS over incoming+outgoing edges. Within that induced node set, calculate **one synchronous tagged directed WL refinement** from the original raw labels for every included node. Aggregate **all** resulting colors across all roots (overlapping neighborhoods repeat node colors). Let totals[k] be this color multiplicity. Weights are 2,1. Score is `floor(1000*(2·intersection(H1A,H1B)+intersection(H2A,H2B))/(2·max(total1A,total1B)+max(total2A,total2B)))`, zero denominator→0. Construction scans per-neighborhood adjacency and sorts filtered neighbor labels; worst-case dense/nearly full neighborhoods repeat whole-graph work V times per k. No theorem makes k=2 a superset of flat-kernel accepted pairs. The **retrieval index still uses flat WL vectors**, so a neighborhood-high-scoring pair can be lost at the shared preprocessing/retrieval stages.

### `CC-U02` Rust activation versus Go abstraction mining

R3: report merges facts by path/line/column/name (first equal occurrence), removes suppressed/generated facts, devirtualizes static trait calls, mines signatures and candidates. Optional PDGs are only extracted under the driver’s `with_pdg` gate (R5). R4: canonicalize under disabled-by-default rewrite flags; build full WL. For ≤400 PDGs compare all pairs; above 400 use two rarest call classes per function (frequency then lexicographic tie), skip blocks >1000. `comparable` requires ≥4 nodes and ≥1 Call in each graph and size ratio ≤2. Select at flat WL ≥600, or optional alignment-coverage fallback; no nine-feature/cosine/JW/LSH clone stage. Choose free seed with most free neighbors (lowest index tie), select seed+neighbors, choose single highest-total-flat-similarity medoid (lowest index tie), retain members with alignment coverage ≥600; remove joined members from free set, otherwise retire seed. Output candidates/suppression/ledger filtering, **not CCGraph clone pairs**.

Go’s separate abstraction cluster similarly has 600/600 defaults but adds seven-feature cosine gate and accepts flat **OR** control/data projected score. Actual projection weights are **12:4** (3:1), despite a nearby outdated 1.0/0.6 comment; when either graph has no control edges it falls back to flat. Go tries up to three templates ranked by total similarity and chooses most joins, then total coverage, preserving first ranked on equal outcomes. Neither these projections nor template clustering are paper verification. The source-derived comparison scope is flat kernel arithmetic given identical histograms/counts/diameters, not equality of frontend output, candidate sets or clusters.

### `CC-G05` clone bridge and `CC-G06` effects (G7–G15)

```text
GO_BRIDGE(group,facts,params):
  require ≥2 IDs, resolve ≥2 facts with PDGs
  compute OR of Effects on ALL nodes per original function
  if unions differ: reject group             # before alignment or subset selection
  canonicalize per params.Normalize; construct FULL WL
  try up to top 3 templates, align others via baseline Align
  retain joins with coverage≥params.MinCoverageMilli (default 600)
  choose most joins, then total coverage; require at least one join
  derive columns from aligned node differences, not AST AntiUnify
  reject same-interface/forced implementations, boilerplate, too many columns (>3 default),
         or insufficient body substance
  emit Parameterize candidate, sites and textual helper proposal (+FixSpec)
```

Effects: nine uint16 flags (mutation, IO, network, global, unsafe, time, random, panic, unknown; none=0). `ClassifyCallee` normalizes the ID and selects longest matching configured/default prefix (later equal-length match wins); no prefix→Unknown. `effectBits` maps that single Kind to one bit; unrecognized Kind→None. Ordinary Call extraction sets it. There is no local-callee transitive effect-summary propagation into the inspected PDG nodes. Non-call mutations/sends etc. do not acquire flags through this path. Hand-built/older missing flags default to zero, indistinguishable from known pure. Equal Unknown unions pass compatibility; multiplicity, targets, execution order and per-position correspondence are ignored. All nodes are ORed, despite the comment describing “Call node Effects.”

Aligned Call effect differences create `HoleEffect`; kinds are not WL labels or CCGraph filters. Alignment hole names use E, but cluster column rank/prefix maps omit HoleEffect (G10:342–367): columns fall back to **X** prefix and zero map-rank. This is a current plumbing gap, not evidence that all effect-hole presentation is complete. An original group rejected for a union mismatch is not retried on compatible subsets.

The actual AST anti-unifier is separately invoked by `FixParameterize → diffPair → antiUnifyHoles → AntiUnifyWithRenames` (G15). The inspected rewrite path considers same-file free functions, signature/closure/named-result and adjacency guards, 1–3 substitutions which must all be identifier expressions; identical bodies or literal/non-expression holes are rejected, and `format.Source` is not semantic validation. Thus a PDG proposal, or even an “exact clone” proposal, does not establish an applicable rewrite. The Bulychev–Minea paper itself was not supplied/read; attribution is documented, not externally fidelity-verified.

Rust has function-level effect facts and a mismatch scoring path (R3:251–290), but no corresponding PdgNode flags/HoleEffect/clone-bridge compatibility guard in the inspected CCGraph-related path. Equal Go/Rust function names do not make those safety contracts equivalent.

## Stage fidelity matrix

Statuses describe **source**, never passing conformance. Fixture IDs are specified below.

| ID → paper contract | Go current | Rust current | First difference → consequence → evidence/fixture |
|---|---|---|---|
| R01 generation | Typed expression AST graph | HIR/typeck expression graph | Generator/schema; both lack execution edges and full reaching-definition/memory model → different graph/feature/labels. G11–12/R1/R5; F01/F02 |
| R02 system removal/call collapse | No imported system/sub-PDG simplify stage on clone path; raw PDGs | No imported reference simplify stage; optional language normalizers for miner | Input and operation mismatch; transparency is not Frama-C/TinyPDG simplification. G1:89/G10:533; R4:247; F03 |
| R03 nine numeric features | Seven, Op≠assignment-only, no references/execution | Absent characteristic stage | Feature extraction before any thresholds → cosine/candidates differ. G2:265–304; R3–4; F04 |
| R03 three strings | Name only; missing names pass; short-name normalization | Absent | String fields discarded/absent → parameter distinctions cannot reject. G1:191–244; F05 |
| R04 size and scale | Only nonempty PDG/≥2 IDs in clone API | Miner ≥4 nodes, ≥1 Call, ratio≤2 | Explicit reference gate absent vs different miner units → tiny clones accepted in Go; Rust filters no-call graphs. G1:132/R2:271; F06 |
| R05/R06 filter composition | `(AST bypass) OR (cosine≥.9 AND nameJW≥.5)` | Neither filter | Bypass alters both filters; plain AND resembles prose only, not Alg.1. G1:180; F07/F08 |
| R07 grammar labels | Signature/scope/type/operator classes | Signature/type/macro classes, fallback names, Debug kinds | Enriched/language-specific initial classes → raw equivalence differs. G2:50/R2:51; F09 |
| R08 refinement | Tagged incoming/outgoing FNV | Same digest structure, different labels | Direction/tags/operand positions are explicit native choices; finite hash collisions cannot enforce iff. G2:112–177/R2:67–130; F10 |
| R09 depth | Finite undirected diameter, clamp to4, skip BFS >400; include raw level | Same selected depth; always retain4 rounds | Choice of diameter/zero/caps/round-zero not explicit reference → selected rounds differ. G2:228–241/412; R2:163/232; F11 |
| R10 counts and weights | Intersection, weights H..1 including raw, weight-sum normalization | Same flat arithmetic over its own histograms | Base-count/round/normalization differ from literal definitions → especially repeated labels/identical graphs. G2:436–508/R2:241–268; F12/F13 |
| R08 versus retrieval | Additional flat-vector LSH connected components | Rare-call blocking in abstraction miner, no LSH | Reference candidate enumeration replaced by retrieval → potential omissions, corpus sensitivity. G5/R4; F14 |
| R11 verification | One max-node normalized flat or neighborhood score ≥900 | Miner flat threshold600 + alignment coverage600 | No separate union/min score step → containment/threshold decisions differ. G1:103–109/R4:115–124; F15 |
| R12 output | Connected clone groups, fixed score750 candidates, bridge | Template clusters and ranked abstraction proposals | Pair relation lost; A~B/B~C need not imply A~C. G1:118/506; R3–4; F16 |
| Extension: neighborhood | Go-only library alternative, same flat retrieval | No corresponding source implementation/caller found | Kernel extension, not paper or externally validated WLKS. G6; F17 |
| Extension: compact/light | Bitset + hist-only retained WL fields | Full WL | Optimized representation; score path source-consistent, not all-consumer substitution. G2–3/R2; F18 |
| Extension: alignment/bridge/effects | PDG bridge + coarse union rejection; separate AST fixer | Abstraction alignment/candidates, no clone bridge/node flags | Detection≠anti-unification≠safety; separate policies/outputs. G7/G9/G15/R1/R3; F19/F20 |

## Concrete distinguishing fixtures (designs, not executed)

Each fixture should save **intermediates**, not merely report group counts. Graph fixtures should supply common logical labels independently of native language label encodings when testing arithmetic.

| ID | Concrete input and distinguishing expected trace |
|---|---|
| F01 | One parameter p, assignment `p=1`, then `use(p)`, versus no assignment. Native later use still depends on original Param/initial binding, not assignment; a reaching-definition reference should differ. Repeat field/pointer writes to expose unavailable memory modeling. |
| F02 | Two side-effecting calls in opposite order, no data/control relation. Native graph multisets may agree because no execution edges; an execution-dependency generator distinguishes order. Do not label arbitrary reorderings semantically safe. |
| F03 | Imported graph Entry→statement→Exit plus assistant param and a two-node callee sub-PDG with external boundary edges. Record node deletion/incident edges and each possible call rewiring. No native clone-path operation implements this import contract. |
| F04 | Set all twelve Table-1 features on a golden reference graph; pair differs only by 10 execution edges or 5 reference variables. Nine-field cosine can differ; native seven-field Go vectors are unchanged. Add arithmetic Op versus assignment Op: Go puts both in assign coordinate; reference should distinguish taxonomy. |
| F05 | Equal names and structural PDGs but incoming parameter strings `int a` versus `String z`, or return strings differing. Name-only Go cannot see them; concatenate/all-fields/min-field JW policies disagree. Supply empty one/both names: native pair filter passes, standalone JW("x","")=0. |
| F06 | Two identical one-node Call PDGs, equal names, source lines 5/6/7 supplied separately. Go clone API can accept the tiny equal vectors/score; Rust miner fails 4-node floor; paper node L versus line setting yields distinct gates. Repeat ≥4-node **no-Call** graphs and ratio just below/at/above2; do not infer paper10x. |
| F07 | Precomputed (N,S)=(.95,.1),(.8,.8),(.4,.95): prose AND rejects all; literal reversed Algorithm1 accepts all; corrected OR accepts all. Add (.8,.1): literal accepts, corrected OR rejects. At N=.9/S=.5 record strict vs inclusive comparisons separately. |
| F08 | Identical Go 20-node Op chains; names `aaaaaaa`/`zzzzzzz`; AST counts both `{Return:1,Call:2}`. Plain clone path rejects by JW; AST path accepts candidate and equal-WL group, demonstrating **name bypass**. For .8 boundary shapes `{A:4}`/`{A:5}` accept; `{A:4}`/`{A:6}` reject. Missing maps do not bypass. |
| F09 | Same Call signature but std `strings.Join` versus local `example.org/pkg.Join`: Go raw call labels differ by scope. Missing-signature Rust calls `k::a`/`k::b` differ by fallback ID; Go same scope/empty SigClass can agree. Isolated Let/Branch use lower-case versus Debug labels; compare classes, not assumed identical hashes. |
| F10 | Graph A: Param→Call Data arg0; B: reverse edge; C: Ctrl edge; D: Data arg1. Native first-round hashes distinguish; undirected/untyped/unpositioned reference alternatives can merge them. Test duplicate identical edges and deliberately injected compression collision, which equality-preserving dictionary must disambiguate. |
| F11 | Directed chain of3, fork with unreachable pairs, isolated3 nodes, empty graph, disconnected two chains, and 400/401-node edgeless graphs. Native finite undirected diameter is2/2/0/0/component max; 401 skips BFS with stored D4 and selected H4. An isolated node has raw-only H1. Pair a 4-node chain (D3) with larger 6-node star (D2): smaller-by-size versus min-diameter policy picks3 versus2. |
| F12 | Raw hist A={x:2,y:1}, B={x:3,z:1}. Cross-product=6; intersection/label-only one-to-one=2. Repeated-label self graph x:3 has cross-product9 vs intersection3; a naive min3 denominator yields3 vs1, exposing the range contradiction. |
| F13 | Three post-refinement levels with ki=1: literal Algorithm2 score2, normalized-weight alternative1. Add raw-only match I0=10, refined I1=I2=I3=0, equal nodes10: native H4 score400; refined-only variant0. Save actual round labels and whether h counts refinements or stored levels. |
| F14 | Native all-candidate evaluation versus seeded retrieval, asserting trace contains every queried pair and connected-bucket components. Inject bucket relations A–B/B–C but no A–C: retrieval still compares A–C if candidate bit present. Construct near-flat pair across all bucket signatures to test missed direct components. Rust corpus: 400 vs401 functions with two private rare classes each; all-pairs versus blocking omission as asserted in R4 tests. |
| F15 | Raw-only hist A={x:10}, B={x:10,y:10}, matching count10: min denominator score1; max denominator .5; histogram-union denominator .5; disjoint vertex union cardinality30 gives1/3. Native gives500, fails900, while min interpretation passes. Equal size hist A={x:9,z:1}, B={x:10} gives native900 (at boundary), accepted; strict >.9 rejects. |
| F16 | Edgeless same-class nodes A=9,B=10,C=11 (no Calls needed for Go clone API), equal/missing names; scores A–B900, B–C909, A–C818, proportional raw vectors share LSH signature. Go returns one group of3 with only two accepted edges, not three verified pairs. Paper pair output must preserve {(A,B),(B,C)}. More accepted edges can reduce group count. |
| F17 | Gap-base graph plus one/two disconnected unrelated calls and one/two node deletions. Compare flat/neighborhood aggregated multiplicities/scores at900, before grouping. Existing test logs are not assertions of a universal superset; independently verify equal Stages1–3 and measure accepted **pair sets**, not groups. |
| F18 | Empty/isolated/disconnected/directed/401-node PDGs: construct full/light using same charVec; compare diameter, count, histograms, Vectorize and scores against third graphs. Deliberately wrong supplied charVec must not be treated as equal Comparable behavior. Attempt light on alignment/projection/cache consumers is unsupported. Test pair bits at(0,64),(63,129),(64,65). |
| F19 | Aligned equal-shape Calls with Effects IO versus0: detection unaffected, effect hole produced, clone bridge rejects. Same IO union but swapped effect positions/counts or both Unknown: compatibility passes, so do not infer semantic safety. Local helpers pure/IO both unresolved flags and non-call direct writes show completeness gaps. Save effect-hole E in Alignment versus X in Cluster column. |
| F20 | PDG exact clones with ≥2 Calls may produce `parameterize` proposal; AST fixer rejects zero substitutions. PDG literal hole may produce proposal; fixer rejects non-identifier holes. Add cross-file or method sites to show same-file/free-function rewrite boundary; no proposal is an executable proof. |

## Existing test evidence and limitations

**Inspected, unexecuted** test families:

- [ccgraph_test.go](../gstyle/domain/patterns/ccgraph_test.go): `TestJaroWinklerIdentical/Empty/Similar/Different/Threshold`; clone similar/name/empty/determinism cases; `TestQualifiedNamesDoNotBypassNameFilter`, `TestQualifiedNamesMatchAcrossPackagesAndReceivers`, and particularly `TestASTBypassStillAdmitsDifferentQualifiedNames` (123–130).
- [asthash_test.go](../gstyle/domain/patterns/asthash_test.go): nil/name/structure/Jaccard/overlap tests and bypass tests. `TestCCGraphClonesWithASTMatchesPlain` compares **group counts**, not full groups; `TestCCGraphClonesWithASTFindsSyntacticClone` only checks `len(withAST)>=len(plain)`, does not assert charVec actually fails or a new accepted pair exists.
- [wl_opt_test.go](../gstyle/domain/patterns/wl_opt_test.go): `TestCharacteristicVector`, `TestCosineSimilarity`, `TestCharVecSimilar`, `TestDiameterBasedRounds`; these test native seven features, not Table1 conformance.
- [perf_regression_test.go](../gstyle/domain/patterns/perf_regression_test.go): `TestNameMatcherReusesBuffers` (68–81); `TestBucketClusteringMatchesQueries` (83–105); `TestCompactPairsAcrossWordBoundaries` (107–123); `TestPairFiltersMatchOriginalPipeline` (125–155, random count maps/cosine/name oracle); `TestDiameterMatchesShortestPaths` (157–199, finite undirected distances); `TestNameBoundMatchesExactFilter` (201–213); `TestWLBoundMatchesExactScore` (223–233); `TestAlignmentWithoutTraceMatchesStaged` (330–343). These compare local procedures, not the original CCGraph engine. No current `*test.go` reference to `NewWlLight` was found in Go-wide search.
- [neighborhood_wl_test.go](../gstyle/domain/patterns/neighborhood_wl_test.go): self/determinism/unrelated/pipeline assertions; `TestNeighborhoodWLGappedClones` **logs** scores (28–49) without assertions of improvement or retained pairs.
- [cloneparam_test.go](../gstyle/domain/patterns/cloneparam_test.go): small/missing IDs/no PDGs/produces candidate/per-group skip tests. The “literal hole” fixture creates an **Op** with detail `lit:1` versus `lit:2` (9–25), not a Lit node; the production assertion does not validate a literal substitution column.
- [effects_test.go](../gstyle/domain/patterns/effects_test.go): eight test functions: flag powers/distinctness, effect difference match/mismatch/noncall, pure/IO compatibility cases and stdlib classification. `TestEffectBitsMapping` checks constants, **not adapter `effectBits` mapping or frontend population**. No general safety proof or complete effect-extraction fixture follows.
- Rust [wl.rs](../rstyle/crates/rstyle-core/src/wl.rs): golden hash, names/order invariance, extra-call/signature-change, weights, size/scale tests (295–415); [cluster.rs](../rstyle/crates/rstyle-core/src/cluster.rs): columns, coverage, 400/401 blocking, pair-coverage/normalization assertions (301–457); [facts.rs](../rstyle/crates/rstyle-core/src/facts.rs): optional/sparse serde PDG roundtrip (420–449); [patterns_report.rs](../rstyle/crates/rstyle-core/src/patterns_report.rs): dedup/ID/ledger/params tests (320–418). None are paper conformance/reproduction experiments.

The [AST benchmark document](../gstyle/benchmark-ast-prefilter.md) and [neighborhood benchmark document](../gstyle/neighborhood-wl-benchmark.md) are local **reported historical artifacts**, introduced at `5d914be`; no raw seven-run arrays, pinned corpus content/configuration or reproduced commands are available from those documents. Reflection claims and limits are individually reconciled in [claims.md](claims.md).

## Unresolved policies and phase-two handoff

Prioritized, **not chosen**:

1. Pin original CCGraph/tool/library/generator revisions and `.dot` fixtures if obtainable; otherwise explicitly call a future profile an interpretation, not reproduction. The supplied PDF’s URLs are leads, not pinned artifacts.
2. Resolve AND/literal reversed OR/corrected OR, threshold inclusivity, node-vs-line size, scale T, reference/state taxonomy, parameter serialization/aggregation and missing strings.
3. Resolve cross-product/intersection/one-to-one semantics, Algorithm2 total, weight normalization and iteration zero; choose how Algorithm2, preliminary union and final min equations compose without silently repairing the paper.
4. Resolve directed/edge/operand neighborhood encoding, synchronous labels, collision handling, smaller-PDG selection, disconnected/zero diameter and depth caps.
5. Implement stage-level traces/fixtures F01–F20 later; no conformance runner or new tests were added here. Preserve pair sets before grouping, compare exhaustive versus optimized retrieval and distinguish frontend adaptation from matching fidelity.
6. Reproduce historical measurements only after identifying revision, corpus hash, extraction/filter configuration, hardware/memory/CPU, commands, repetitions, raw pair/group results, labels and peak-memory method. Group growth is not labeled recall; speedup ratios are not elapsed-time percentage changes.
7. Audit effect completeness and proposal-to-rewrite boundaries independently, including cluster effect-column names/ranks. Equal unions and approximate clones do not make extraction safe.

Coverage: **12/12 PDF pages extracted/read; 9/9 numerical and 3/3 string features explicitly accounted for; 12/12 reference stage IDs plus 8 current/variant records above; 20/20 concrete fixture designs; 80/80 reflection claim IDs plus 6 supplemental claim IDs in the companion ledger.** Alignment internals beyond the traced baseline stages/difference/coverage contracts, all normalization rule bodies, unrelated detectors, loader/compiler/library internals and full rewrite correctness remain outside this slice. There are **no observed algorithm runtime results or passing conformance tests** in this audit.
