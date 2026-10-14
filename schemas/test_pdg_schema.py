"""Structural single-profile PDG checks; these do not certify extraction semantics."""

import copy
import hashlib
import json
from pathlib import Path
import unittest

from jsonschema import Draft202012Validator


SCHEMAS = Path(__file__).resolve().parent


class PDGSchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = json.loads((SCHEMAS / "pdg.schema.json").read_text())
        cls.example = json.loads((SCHEMAS / "pdg.example.json").read_text())
        Draft202012Validator.check_schema(cls.schema)
        cls.validator = Draft202012Validator(cls.schema)

    def graph(self):
        return copy.deepcopy(self.example)

    def definition(self, name):
        return Draft202012Validator({"$defs": self.schema["$defs"], "$ref": f"#/$defs/{name}"})

    def test_example_and_unchanged_version(self):
        self.validator.validate(self.example)
        self.assertEqual(self.schema["properties"]["schema_version"]["const"], "0.1.0")
        self.assertEqual(self.example["profile"], {"id": "compat.rust.hir-r0", "version": "0.1.0"})
        self.assertEqual(self.example["extraction_evidence"]["conformance"]["status"], "not_evaluated")

    def test_example_source_identity_and_spans(self):
        source = self.example["producer"]["configuration"]["source_text"].encode("utf-8")
        identity = "sha256:" + hashlib.sha256(source).hexdigest()
        self.assertEqual(self.example["sources"][0]["content_identity"]["value"], identity)
        for record in [self.example["function"], *self.example["nodes"]]:
            span = record["source_span"]
            self.assertEqual(span["source_id"], "src")
            self.assertTrue(0 <= span["start"] <= span["end"] <= len(source))
        span = self.example["nodes"][0]["source_span"]
        self.assertEqual(source[span["start"]:span["end"]], b"1")

    def test_root_profile_is_required_and_closed(self):
        graph = self.graph()
        del graph["profile"]
        self.assertFalse(self.validator.is_valid(graph))
        for profile in (None, [], {}, {"id": "example"}, {"version": "0.1.0"},
                        {"id": "", "version": "0.1.0"}, {"id": "example", "version": ""},
                        {"id": "example", "version": "0.1.0", "edge_policy": "other"}):
            with self.subTest(profile=profile):
                graph = self.graph()
                graph["profile"] = profile
                self.assertFalse(self.validator.is_valid(graph))

    def test_only_root_profile_can_select_extraction_semantics(self):
        def profile_refs(value, path=()):
            if isinstance(value, dict):
                for key, child in value.items():
                    if key == "$ref" and child == "#/$defs/profile":
                        yield path
                    yield from profile_refs(child, (*path, key))
            elif isinstance(value, list):
                for index, child in enumerate(value):
                    yield from profile_refs(child, (*path, index))

        self.assertEqual(list(profile_refs(self.schema)), [("properties", "profile")])
        self.assertNotIn("policy", json.dumps(self.example))

    def test_per_record_policy_fields_are_rejected(self):
        for path in (
            ("function", "reference_count"),
            ("function", "interface_completeness"),
            ("nodes", 0, "evidence"),
            ("nodes", 0, "provenance"),
            ("edges", 0),
            ("edges", 0, "evidence"),
            ("edges", 0, "provenance"),
            ("extraction_evidence", "capabilities", "reference_counting"),
        ):
            with self.subTest(path=path):
                graph = self.graph()
                record = graph
                for key in path:
                    record = record[key]
                record["policy"] = copy.deepcopy(graph["profile"])
                self.assertFalse(self.validator.is_valid(graph))

    def test_count_facts_preserve_known_zero_and_unavailable_reasons(self):
        validator = self.definition("countFact")
        for value in (0, 1, 100):
            with self.subTest(value=value):
                validator.validate({"status": "known", "value": value})
        for status in ("unknown", "unsupported", "not_applicable"):
            with self.subTest(status=status):
                validator.validate({"status": status, "reason": "Count unavailable."})
                self.assertFalse(validator.is_valid({"status": status, "value": 0}))
        for fact in ({"status": "known"}, {"status": "known", "value": -1},
                     {"status": "known", "value": True}, {"status": "known", "value": "0"},
                     {"status": "known", "value": 0, "reason": "Unknown."},
                     {"status": "unknown"}, {"status": "unknown", "reason": ""}):
            with self.subTest(fact=fact):
                self.assertFalse(validator.is_valid(fact))

    def test_evidence_statuses_remain_independent(self):
        for status in ("supported", "approximated", "unsupported", "unknown", "not_applicable"):
            with self.subTest(status=status):
                graph = self.graph()
                graph["nodes"][0]["evidence"]["status"] = status
                graph["edges"][0]["evidence"]["status"] = "approximated"
                self.validator.validate(graph)
        validator = self.definition("capability")
        for evidence in ({"status": "unknown"}, {"status": "supported", "description": ""},
                         {"status": "conformant", "description": "Wrong status."}):
            with self.subTest(evidence=evidence):
                self.assertFalse(validator.is_valid(evidence))

    def test_provenance_origins_and_details_remain(self):
        validator = self.definition("provenance")
        for origin in ("source", "desugaring", "macro_expansion", "analysis", "projection"):
            with self.subTest(origin=origin):
                validator.validate({
                    "origin": origin, "description": "Origin details.",
                    "origin_node_ids": ["literal"],
                    "origin_spans": [{"source_id": "src", "start": 21, "end": 22}],
                })
        self.assertFalse(validator.is_valid({"description": "Missing origin."}))

    def test_edge_families_share_root_profile(self):
        for kind in ("data", "control", "execution"):
            with self.subTest(kind=kind):
                graph = self.graph()
                graph["edges"][0]["kind"] = kind
                self.validator.validate(graph)

    def test_single_conformance_assessment(self):
        for status in ("conformant", "non_conformant", "not_evaluated"):
            with self.subTest(status=status):
                graph = self.graph()
                graph["extraction_evidence"]["conformance"] = {"status": status, "reasons": ["Assessment reason."]}
                self.validator.validate(graph)
        for assessment in (
            [], [{"profile": self.example["profile"], "status": "not_evaluated", "reasons": []}],
            {"profile": self.example["profile"], "status": "not_evaluated", "reasons": []},
            {"status": "non_conformant", "reasons": []},
            {"status": "non_conformant", "reasons": [""]},
            {"status": "not_evaluated"}, {"reasons": []},
            {"status": "unknown", "reasons": []},
        ):
            with self.subTest(assessment=assessment):
                graph = self.graph()
                graph["extraction_evidence"]["conformance"] = assessment
                self.assertFalse(self.validator.is_valid(graph))
        for status in ("conformant", "not_evaluated"):
            graph = self.graph()
            graph["extraction_evidence"]["conformance"] = {"status": status, "reasons": []}
            self.validator.validate(graph)


if __name__ == "__main__":
    unittest.main()
