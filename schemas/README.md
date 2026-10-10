# PDG interchange draft

`pdg.schema.json` is a JSON Schema Draft 2020-12 structural contract, version
`0.1.0`. It is a starting point, not a finalized CCGraph profile or a claim that
existing Go/Rust producers conform. No existing graph format is replaced.

## Representation

- A document represents one function. IDs are opaque navigation/reference keys,
  never matching labels. Node and edge IDs are graph-local; symbol, definition,
  and memory-location IDs have separate document-local namespaces.
- Nodes represent operations or analysis entities. Symbols represent bindings;
  definitions represent individual produced versions of a binding or location.
  A reassignment must not reuse the previous definition ID.
- The extraction profile must define statement/expression/mixed granularity,
  scope identity, node category requirements, merge representation, and supported
  language constructs. `original_kind` retains frontend kinds separately from
  normalized categories. Source-backed nodes require spans; synthetic nodes
  require provenance and may also have spans.
- Spans use half-open UTF-8 byte offsets. Paths are navigation information;
  `content_identity` records known content identity or explicit missing evidence.
- The graph is a directed multigraph. Parallel edges are retained, including
  repeated operands. Edge IDs distinguish occurrences; arrays are not source
  order. Self-edges may be meaningful for loop-carried dependencies.
- Data edges run producer to consumer. Control edges run controller to controlled
  operation. Execution edges run prerequisite to constrained operation. Each edge
  names a versioned semantic policy; execution is not implicitly source order.
  CFG successor relations are not dependency edges and are not in the base edge
  enum. Export a separate CFG if required.
- `operand_position` is zero-based under the profile's operand ordering. Interface
  positions are zero-based within inputs/outputs. Receivers and captures have
  explicit roles; a profile must define their ordering and string serialization.
- Known facts carry values; unknown/unsupported/not-applicable facts carry reasons.
  A known count of zero differs from missing evidence. `reference_count` requires
  a versioned counting policy. `variadic` currently uses a string fact; a profile
  must define its vocabulary (a future revision may introduce typed boolean facts).
- Capability descriptions must explain scope and approximations. Empty arrays do
  not establish absence: consult capability and interface completeness evidence.
  No schema default silently fills in an unknown fact.
- Namespaced annotations/extensions preserve effects, ownership, types, calls and
  additional facts. They do not affect base labels, filtering, or counts unless a
  named, versioned matching profile explicitly includes them.

## Semantic validation required beyond JSON Schema

Implement a validator alongside producer integration. It must check:

1. Unique IDs in each namespace and valid node/edge/symbol/definition/location/
   source references. Scope IDs must obey the extraction profile's scope model.
   Provenance origin IDs may refer to an external input graph only when a
   transformation profile defines that reference context.
2. Span bounds (`start <= end`, both within identified source bytes), source
   content identity, and source/provenance consistency.
3. Category-specific attributes: declarations identify bindings; reads identify
   accesses; assignments identify writes/definitions; computations identify
   operators; controls identify constructs/outcomes; calls identify resolution
   evidence; interface nodes identify positions; merges identify incoming values
   under the declared representation. The draft intentionally does not freeze
   these into a single frontend-independent extraction interpretation yet.
4. Definition ownership, legal dependency subtypes, operand positions, branch
   outcomes, and loop-carried facts according to the profile. Omitted optional
   edge attributes mean unrecorded, not false or zero.
5. Interface ordering and completeness; distinct definitions on reassignment;
   branch merges, loop-carried definitions, return and call dependencies using
   extraction fixtures, not just structural assertions.
6. Required profile capabilities and evidence. Missing required evidence must
   produce a diagnostic or `non_conformant`, never automatic conformance. A
   `conformant` claim must be checked rather than trusted. JSON Schema alone
   cannot prove completeness or correct reaching-definition analysis.

## Separate CCGraph profile still needed

Do not derive paper labels or features directly from this schema's categories.
A CCGraph profile must define and version:

- Projection/simplification rules and removed/collapsed node/edge provenance.
- Declaration/assignment/control/state/other categories, resolving the state/call
  terminology explicitly.
- Nine numerical features: `NumOfCtrlEdges`, `NumOfExcEdges`, `NumOfDataEdges`,
  `NumOfDeclNodes`, `NumOfAssignNodes`, `NumOfCtrlNodes`, `NumOfStateNodes`,
  `NumOfOtherNodes`, `NumOfReference`; counts before/after projection, multiplicity,
  and the reference-count policy.
- Three string features: `ReturnPara`, `IntroPara`, `Name`; parameter names/types,
  ordering, receivers, captures, separators, and unknown/empty behavior.
- Initial labels, dependency handling, optional annotations admitted into labels,
  and WL refinement/filtering policies.

Unknown reference counts or incomplete interfaces block a profile requiring
those features. Omitting execution edges is not paper fidelity.

## Serialization and deterministic comparison

Encode JSON as UTF-8. Object key order is irrelevant. Profiles must declare which
arrays are ordered (interfaces/operands) versus unordered collections
(nodes/edges/symbols). For stable snapshots, sort unordered collections by ID;
this is serialization stability, not graph equivalence across producers.

Cross-producer comparison must ignore navigation IDs/spans unless the test is
specifically about provenance. Compare graph structure with edge multiplicity,
operand roles, and profile-selected labels under an explicit node correspondence
or graph-equivalence procedure. For WL, compare label-equivalence partitions at
each iteration, not implementation-specific numeric hashes. Round-trip tests must
preserve facts, unknown evidence, parallel edges, and extension data.

## Next contract milestones

Add category-specific profile constraints, a semantic validator, and positive/
negative fixtures (unknown evidence, branch merges, loops, calls, parallel edges,
and invalid references). Resolve paper ambiguities before naming a conformant
CCGraph profile. A binary transport can be added later without changing these
semantics if measurements justify it.
