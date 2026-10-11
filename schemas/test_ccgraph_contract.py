"""Static contract/oracle consistency checks, NOT analyzer conformance or quality tests."""

import copy
from collections import Counter, deque
from fractions import Fraction
import json
from pathlib import Path
import re
import unittest

from jsonschema import Draft202012Validator


HERE = Path(__file__).resolve().parent


def load(path):
    return json.loads((HERE / path).read_text())


def fraction(pair):
    return Fraction(*pair)


def diameter(graph):
    """Small fixture-only shortest-path check; no production matching implementation."""
    successors = {node: [] for node in graph["nodes"]}
    for source, target, _ in graph["edges"]:
        successors[source].append(target)
    maximum = 0
    for start in successors:
        distances = {start: 0}
        queue = deque([start])
        while queue:
            source = queue.popleft()
            for target in successors[source]:
                if target not in distances:
                    distances[target] = distances[source] + 1
                    queue.append(target)
        maximum = max(maximum, max(distances.values()))
    return maximum


def round_histograms(a, b, h):
    # Literal structural tuples avoid implementation-specific hash assumptions.
    colors = [dict(a["nodes"]), dict(b["nodes"])]
    rounds = [(Counter(colors[0].values()), Counter(colors[1].values()))]
    family_order = {family: i for i, family in enumerate(("data", "control", "execution"))}
    for _ in range(h):
        next_colors = []
        for graph, previous in zip((a, b), colors):
            incoming = {node: [] for node in previous}
            outgoing = {node: [] for node in previous}
            for source, target, family in graph["edges"]:
                incoming[target].append((family_order[family], previous[source]))
                outgoing[source].append((family_order[family], previous[target]))
            next_colors.append({
                node: (previous[node], tuple(sorted(incoming[node])), tuple(sorted(outgoing[node])))
                for node in previous
            })
        colors = next_colors
        rounds.append((Counter(colors[0].values()), Counter(colors[1].values())))
    return rounds


def jw(a, b):
    """Exact fixture arithmetic for the specified convention, not a library oracle."""
    if a == b:
        return Fraction(1)
    if not a or not b:
        return Fraction(0)
    a, b = sorted((a, b), key=lambda text: (len(text), text))
    window = max(0, max(len(a), len(b)) // 2 - 1)
    matched_a = [False] * len(a)
    matched_b = [False] * len(b)
    for i, char in enumerate(a):
        for j in range(max(0, i - window), min(len(b), i + window + 1)):
            if not matched_b[j] and char == b[j]:
                matched_a[i] = matched_b[j] = True
                break
    m = sum(matched_a)
    if not m:
        return Fraction(0)
    sequence_a = [char for char, matched in zip(a, matched_a) if matched]
    sequence_b = [char for char, matched in zip(b, matched_b) if matched]
    transpositions = Fraction(sum(x != y for x, y in zip(sequence_a, sequence_b)), 2)
    jaro = (Fraction(m, len(a)) + Fraction(m, len(b)) + (m - transpositions) / m) / 3
    prefix = 0
    for x, y in zip(a[:4], b[:4]):
        if x != y:
            break
        prefix += 1
    return jaro + Fraction(prefix, 10) * (1 - jaro)


def reachable(edges, start):
    result = {start}
    while True:
        extended = result | {target for source, target, _ in edges if source in result}
        if extended == result:
            return result
        result = extended


def dominators(vertices, edges, root, reverse=False):
    predecessors = {node: set() for node in vertices}
    for source, target, _ in edges:
        if source in vertices and target in vertices:
            if reverse:
                source, target = target, source
            predecessors[target].add(source)
    result = {node: ({root} if node == root else set(vertices)) for node in vertices}
    while True:
        updated = {root: {root}}
        for node in vertices - {root}:
            assert predecessors[node], (node, "missing path to analysis root")
            updated[node] = {node} | set.intersection(*(result[p] for p in predecessors[node]))
        if updated == result:
            return result
        result = updated


def immediate(dominance, node):
    candidates = dominance[node] - {node}
    return max(candidates, key=lambda ancestor: len(dominance[ancestor])) if candidates else None


def cfg_paths(edges):
    successors = {}
    for source, target, kind in edges:
        successors.setdefault(source, []).append((target, kind))

    def walk(node, path, outcomes):
        assert node not in path, "R0 fixture CFG must be acyclic"
        path = path + [node]
        if node == "X":
            yield path, outcomes
            return
        for target, kind in successors.get(node, []):
            new_outcomes = dict(outcomes)
            if kind in ("true", "false"):
                new_outcomes[node] = kind
            yield from walk(target, path, new_outcomes)

    return list(walk("E", [], {}))


class CCGraphContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.profile = load("ccgraph-profile.json")
        cls.matching = load("fixtures/ccgraph-matching.json")
        cls.extraction = load("fixtures/rust-r0-extraction.json")

    def test_versions_and_unexecuted_claims(self):
        self.assertEqual(self.profile["profile"], {"id": "compat.ccgraph.strict", "version": "0.1.0"})
        self.assertEqual(self.matching["matching_profile"], self.profile["profile"])
        self.assertEqual(self.extraction["extraction_profile"], self.profile["rust_extraction_profile"])
        for name in ("cfg", "pdg"):
            schema = load(f"{name}.schema.json")
            Draft202012Validator.check_schema(schema)
            self.assertEqual(schema["properties"]["schema_version"]["const"], self.profile["schema_versions"][name])
            self.assertEqual(self.extraction["schema_targets"][name], self.profile["schema_versions"][name])
        self.assertEqual(self.profile["status"], "specified_not_implemented")
        self.assertEqual(self.matching["validation"]["analyzer_execution"], "not_run")
        self.assertEqual(self.extraction["validation"]["semantic_support"], "unknown")
        self.assertTrue(all(case["execution_status"] == "not_run" for case in self.extraction["cases"]))

    def test_agreed_settings(self):
        self.assertEqual(self.profile["defaults"], {
            "minimum_projected_nodes": 1, "minimum_size_ratio": 0.8,
            "numerical_threshold": 0.9, "string_threshold": 0.5,
            "final_threshold": 0.9, "scoring": "smaller_graph_overlap",
        })
        self.assertEqual(self.profile["scoring"]["experimental"], ["cross_product_cosine"])
        self.assertEqual(self.profile["wl"]["round_weight"], "h+1-r")
        self.assertIsNone(self.profile["wl"]["refinement_cap"])
        self.assertIsNone(self.profile["wl"]["graph_size_fallback"])
        self.assertFalse(self.profile["wl"]["include_operand_positions"])
        self.assertFalse(self.profile["wl"]["include_branch_outcomes"])
        self.assertEqual(self.profile["gates"]["composition"], "sequential-AND")
        self.assertEqual(self.profile["gates"]["comparison"], ">=")
        self.assertFalse(self.profile["gates"]["preliminary_wl_gate"])

    def test_complete_explicit_category_mapping(self):
        categories = load("pdg.schema.json")["$defs"]["node"]["properties"]["category"]["enum"]
        self.assertEqual(set(self.profile["category_mapping"]), set(categories) - {"entry", "exit", "memory_summary"})
        self.assertEqual(self.extraction["encoding"]["matching_labels"], self.profile["category_mapping"])
        self.assertEqual(set(self.profile["category_mapping"].values()), {"DECL", "ASSIGN", "CTRL", "STATE", "OTHER"})
        self.assertEqual(len(self.profile["numerical_features"]), 9)
        self.assertEqual(self.profile["numerical_features"][1], "NumOfExcEdges")
        self.assertEqual(self.profile["numerical_features"][-1], "NumOfReference")

    def test_projection_counts_are_hand_consistent(self):
        for case in self.matching["projection_cases"]:
            with self.subTest(case=case["id"]):
                nodes = case["input"]["nodes"]
                kept = [node for node in nodes if not node.get("administrative", False) and node.get("reachable", True)]
                kept_ids = {node["id"] for node in kept}
                expected = case["expected"]
                self.assertEqual(kept_ids, set(expected["retained_nodes"]))
                self.assertEqual({n["id"] for n in nodes} - kept_ids, set(expected["removed_nodes"]))
                edges = [e for e in case["input"]["edges"] if e[0] in kept_ids and e[1] in kept_ids]
                self.assertEqual(Counter(map(tuple, edges)), Counter(map(tuple, expected["edges"])))
                families = Counter(e[2] for e in edges)
                labels = Counter(self.profile["category_mapping"][n["category"]] for n in kept)
                references = {symbol for n in kept if n["category"] == "read" for symbol in n.get("read_symbols", [])}
                vector = [families["control"], families["execution"], families["data"],
                          labels["DECL"], labels["ASSIGN"], labels["CTRL"], labels["STATE"], labels["OTHER"], len(references)]
                self.assertEqual(vector, expected["features"])

    def test_interface_serialization(self):
        for case in self.matching["interface_cases"]:
            with self.subTest(case=case["id"]):
                for source, field in (("inputs", "IntroPara"), ("outputs", "ReturnPara")):
                    serialized = json.dumps(case[source], ensure_ascii=False, separators=(",", ":"))
                    self.assertEqual(serialized, case["expected"][field])
                self.assertEqual(case["name"], case["expected"]["Name"])

    def test_variadic_schema_is_boolean(self):
        schema = load("pdg.schema.json")
        validator = Draft202012Validator({"$defs": schema["$defs"], "$ref": "#/$defs/parameter"})
        item = {"position": 0, "role": "return", "name": {"status": "not_applicable", "reason": "unnamed return"},
                "type": {"status": "known", "value": "()"}, "variadic": {"status": "known", "value": False}}
        validator.validate(item)
        item["variadic"]["value"] = "false"
        self.assertFalse(validator.is_valid(item))

    def test_jaro_winkler_hand_worked_values_and_symmetry(self):
        for case in self.matching["jaro_winkler_cases"]:
            with self.subTest(case=case["id"]):
                expected = fraction(case["expected"])
                self.assertEqual(jw(case["a"], case["b"]), expected)
                self.assertEqual(jw(case["b"], case["a"]), expected)

    def test_directed_diameter(self):
        for case in self.matching["diameter_cases"]:
            with self.subTest(case=case["id"]):
                self.assertEqual(diameter(case["graph"]), case["expected"])

    def test_pair_depth(self):
        for case in self.matching["depth_cases"]:
            with self.subTest(case=case["id"]):
                sizes, ds = case["sizes"], case["diameters"]
                h = min(ds) if sizes[0] == sizes[1] else ds[0 if sizes[0] < sizes[1] else 1]
                self.assertEqual(h, case["expected"])

    def assert_scores(self, rounds, sizes, h, expected):
        weights = list(range(h + 1, 0, -1))
        overlap = [sum(min(a.get(c, 0), b.get(c, 0)) for c in a.keys() | b.keys()) for a, b in rounds]
        cross = [sum(a.get(c, 0) * b.get(c, 0) for c in a.keys() | b.keys()) for a, b in rounds]
        self_a = [sum(count * count for count in a.values()) for a, _ in rounds]
        self_b = [sum(count * count for count in b.values()) for _, b in rounds]
        for field, actual in (("weights", weights), ("overlap_per_round", overlap), ("cross_per_round", cross),
                              ("self_a_per_round", self_a), ("self_b_per_round", self_b)):
            self.assertEqual(actual, expected[field], field)
        matched = Fraction(sum(w * m for w, m in zip(weights, overlap)), sum(weights))
        self.assertEqual(matched / min(sizes), fraction(expected["overlap_score"]))
        if "larger_coverage" in expected:
            self.assertEqual(matched / max(sizes), fraction(expected["larger_coverage"]))
        kab = sum(w * k for w, k in zip(weights, cross))
        kaa = sum(w * k for w, k in zip(weights, self_a))
        kbb = sum(w * k for w, k in zip(weights, self_b))
        self.assertEqual(kab, expected["cosine_score"]["numerator"])
        self.assertEqual(kaa * kbb, expected["cosine_score"]["sqrt_denominator"])
        self.assertLessEqual(kab * kab, kaa * kbb)

    def test_wl_stage_expectations(self):
        for case in self.matching["wl_cases"]:
            with self.subTest(case=case["id"]):
                a, b = case["a"], case["b"]
                sizes = [len(a["nodes"]), len(b["nodes"])]
                ds = [diameter(a), diameter(b)]
                h = min(ds) if sizes[0] == sizes[1] else ds[0 if sizes[0] < sizes[1] else 1]
                self.assertEqual(h, case["expected"]["h"])
                self.assert_scores(round_histograms(a, b, h), sizes, h, case["expected"])

    def test_histogram_scoring_expectations(self):
        for case in self.matching["histogram_score_cases"]:
            with self.subTest(case=case["id"]):
                self.assertEqual(len(case["a"]), case["h"] + 1)
                self.assertEqual(len(case["b"]), case["h"] + 1)
                for a, b in zip(case["a"], case["b"]):
                    self.assertEqual(sum(a.values()), case["sizes"][0])
                    self.assertEqual(sum(b.values()), case["sizes"][1])
                self.assert_scores(list(zip(case["a"], case["b"])), case["sizes"], case["h"], case["expected"])

    def test_exact_inclusive_boundaries(self):
        for case in self.matching["boundary_cases"]:
            with self.subTest(case=case["id"]):
                t = Fraction(case["threshold"])
                if case["kind"] == "ratio":
                    sizes = case["sizes"]
                    accepted = min(sizes) > 0 and Fraction(min(sizes), max(sizes)) >= t
                elif case["kind"] == "rational":
                    accepted = fraction(case["score"]) >= t
                elif case["kind"] == "mean":
                    accepted = sum(map(fraction, case["fields"])) / 3 >= t
                else:
                    accepted = case["dot"] ** 2 >= t ** 2 * case["norm_product"]
                self.assertEqual(accepted, case["expected"])

    def test_navigation_and_collection_order_invariance(self):
        original = self.matching["wl_cases"][0]["a"]
        renamed = {"nodes": {"z": "ASSIGN", "q": "DECL"}, "edges": [["q", "z", "data"]]}
        rounds = round_histograms(original, renamed, 1)
        self.assertTrue(all(a == b for a, b in rounds))
        for case in self.matching["wl_cases"]:
            a, b = copy.deepcopy(case["a"]), copy.deepcopy(case["b"])
            a["edges"].reverse()
            b["edges"].reverse()
            self.assertEqual(round_histograms(a, b, case["expected"]["h"]),
                             round_histograms(case["a"], case["b"], case["expected"]["h"]))

    def test_extraction_fixture_references_and_rejections(self):
        ids = [case["id"] for case in self.extraction["cases"]]
        self.assertEqual(len(ids), len(set(ids)))
        for case in self.extraction["cases"]:
            with self.subTest(case=case["id"]):
                expected = case["expected"]
                if expected["eligibility"] == "ineligible":
                    self.assertEqual(expected["conformance"], "non_conformant")
                    self.assertTrue(expected["diagnostics"])
                    continue
                self.assertTrue(expected["exact_graph"])
                nodes = {node[0]: node[1] for node in expected["nodes"]}
                self.assertEqual(len(nodes), len(expected["nodes"]))
                definitions = {d[0]: (d[1], d[2]) for d in expected["definitions"]}
                self.assertEqual(len(definitions), len(expected["definitions"]))
                symbols = {s[0] for s in expected["symbols"]}
                for symbol, defining_node in definitions.values():
                    self.assertIn(symbol, symbols)
                    self.assertIn(nodes[defining_node], ("formal_input", "declaration", "assignment"))
                read_symbols = set()
                reaching_edges = []
                for read, defs in expected["read_definitions"].items():
                    self.assertEqual(nodes[read], "read")
                    self.assertTrue(defs)
                    same_symbol = {definitions[d][0] for d in defs}
                    self.assertEqual(len(same_symbol), 1)
                    read_symbols.update(same_symbol)
                    reaching_edges.extend((definitions[d][1], read, d) for d in defs)
                self.assertEqual(len(read_symbols), expected["reference_count"])
                self.assertEqual(Counter(reaching_edges), Counter(map(tuple, expected["pdg_edges"]["reaching_definition"])))
                for edges in expected["pdg_edges"].values():
                    for edge in edges:
                        self.assertIn(edge[0], nodes)
                        self.assertIn(edge[1], nodes)

    def test_extraction_dominance_and_control_expectations(self):
        for case in self.extraction["cases"]:
            expected = case["expected"]
            if not expected.get("exact_graph"):
                continue
            with self.subTest(case=case["id"]):
                edges = expected["cfg_edges"]
                vertices = reachable(edges, "E")
                self.assertIn("X", vertices)
                dom = dominators(vertices, edges, "E")
                postdom = dominators(vertices, edges, "X", reverse=True)
                operations = vertices - {"E", "X"}
                execution = [(immediate(dom, n), n) for n in operations if immediate(dom, n) in operations]
                self.assertEqual(Counter(execution), Counter(map(tuple, expected["pdg_edges"]["execution"])))
                control = []
                for p, successor, outcome in edges:
                    if p not in vertices or outcome not in ("true", "false") or successor in postdom[p]:
                        continue
                    n = successor
                    while n != immediate(postdom, p):
                        if n in operations:
                            control.append((p, n, outcome))
                        n = immediate(postdom, n)
                self.assertEqual(Counter(control), Counter(map(tuple, expected["pdg_edges"]["control"])))
                paths = cfg_paths(edges)
                self.assertTrue(paths)
                self.assertEqual({n for path, _ in paths for n in path}, vertices)

    def test_extraction_reaching_definition_expectations(self):
        for case in self.extraction["cases"]:
            expected = case["expected"]
            if not expected.get("exact_graph"):
                continue
            with self.subTest(case=case["id"]):
                edges = expected["cfg_edges"]
                vertices = reachable(edges, "E")
                nodes = {node[0]: node[1] for node in expected["nodes"]}
                definitions = {d[0]: (d[1], d[2]) for d in expected["definitions"]}
                initial = {d for d, (_, n) in definitions.items() if nodes[n] == "formal_input"}
                generated = {}
                for d, (symbol, n) in definitions.items():
                    if nodes[n] != "formal_input":
                        generated[n] = (symbol, d)
                incoming = {n: set() for n in vertices}
                outgoing = {n: set() for n in vertices}
                while True:
                    next_in, next_out = {}, {}
                    for n in vertices:
                        defs = set(initial) if n == "E" else set().union(*(outgoing[p] for p, t, _ in edges if t == n and p in vertices))
                        next_in[n] = defs
                        if n in generated:
                            symbol, definition = generated[n]
                            defs = {d for d in defs if definitions[d][0] != symbol} | {definition}
                        next_out[n] = defs
                    if next_in == incoming and next_out == outgoing:
                        break
                    incoming, outgoing = next_in, next_out
                for read, defs in expected["read_definitions"].items():
                    symbol = definitions[defs[0]][0]
                    self.assertEqual({d for d in incoming[read] if definitions[d][0] == symbol}, set(defs))
                for field, sets in expected.get("local_definition_sets", {}).items():
                    calculated = incoming if field == "in" else outgoing
                    for n, bindings in sets.items():
                        for symbol, defs in bindings.items():
                            self.assertEqual({d for d in calculated[n] if definitions[d][0] == symbol}, set(defs))

    def test_merge_frontiers_and_guard_availability(self):
        key = "compat.rust.hir-r0:guards"
        for case in self.extraction["cases"]:
            expected = case["expected"]
            if not expected.get("exact_graph"):
                continue
            with self.subTest(case=case["id"]):
                nodes = {node[0]: node[1] for node in expected["nodes"]}
                edges = expected["cfg_edges"]
                paths = cfg_paths(edges)
                alternatives = []
                for site in expected["value_sites"]:
                    self.assertEqual(nodes[site["pdg_node_id"]], "merge")
                    self.assertEqual(nodes[site["controller_pdg_node_id"]], "control")
                    observed = [set() for _ in site["alternatives"]]
                    for path, outcomes in paths:
                        successor = site["cfg_successor_node_id"]
                        if successor not in path:
                            continue
                        def selected(dnf):
                            return any(all(outcomes.get(atom["controller_pdg_node_id"]) == atom["outcome"] for atom in term) for term in dnf)
                        active = [selected(alt["annotations"][key]) for alt in site["alternatives"]]
                        self.assertEqual(selected(site["annotations"][key]), any(active))
                        self.assertLessEqual(sum(active), 1)
                        for i, is_active in enumerate(active):
                            if is_active:
                                frontier = path[path.index(successor) - 1]
                                self.assertIn(frontier, site["alternatives"][i]["completion_cfg_node_ids"])
                                observed[i].add(frontier)
                    for i, alt in enumerate(site["alternatives"]):
                        self.assertEqual(observed[i], set(alt["completion_cfg_node_ids"]))
                        self.assertEqual(len(alt["completion_cfg_node_ids"]), len(set(alt["completion_cfg_node_ids"])))
                        for n in alt["completion_cfg_node_ids"]:
                            self.assertTrue(any(p == n and t == site["cfg_successor_node_id"] for p, t, _ in edges))
                        alternatives.append((alt["value_pdg_node_id"], site["pdg_node_id"],
                                             0 if alt["outcome"] == "true" else 1,
                                             alt["outcome"], site["controller_pdg_node_id"]))
                self.assertEqual(Counter(alternatives), Counter(map(tuple, expected["pdg_edges"]["value_alternative"])))

    def test_normative_document_links(self):
        for name in ("ccgraph-profile.md", "rust-extraction-profile.md", "ccgraph-decisions.md", "rust-capabilities.md"):
            for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", (HERE / name).read_text()):
                if not target.startswith(("https://", "http://", "#")):
                    self.assertTrue((HERE / target.split("#")[0]).exists(), (name, target))


if __name__ == "__main__":
    unittest.main()
