"""Structural CFG policy checks; these do not validate language semantics."""

import copy
import itertools
import json
from pathlib import Path
import unittest

from jsonschema import Draft202012Validator


SCHEMAS = Path(__file__).resolve().parent


class CFGSchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = json.loads((SCHEMAS / "cfg.schema.json").read_text())
        cls.example = json.loads((SCHEMAS / "cfg.example.json").read_text())
        Draft202012Validator.check_schema(cls.schema)
        cls.validator = Draft202012Validator(cls.schema)

    def with_policy(self, policy):
        graph = copy.deepcopy(self.example)
        graph["profile"]["evaluation_order"] = policy
        return graph

    def test_example(self):
        self.validator.validate(self.example)

    def test_supported_policy_combinations(self):
        for short_circuit, unspecified_order in itertools.product(
            ("explicit_branches", "reject"), ("overapproximate", "reject")
        ):
            with self.subTest(short_circuit=short_circuit, unspecified_order=unspecified_order):
                self.validator.validate(self.with_policy({
                    "sequencing": "language_defined",
                    "short_circuit": short_circuit,
                    "unspecified_order": unspecified_order,
                }))

    def test_required_fields(self):
        for field in self.example["profile"]["evaluation_order"]:
            with self.subTest(field=field):
                policy = copy.deepcopy(self.example["profile"]["evaluation_order"])
                del policy[field]
                self.assertFalse(self.validator.is_valid(self.with_policy(policy)))

    def test_unsupported_values_and_types(self):
        for field, value in (
            ("sequencing", "left_to_right"),
            ("short_circuit", "evaluate_all"),
            ("unspecified_order", "choose_one"),
            ("sequencing", None),
            ("short_circuit", True),
            ("unspecified_order", 0),
        ):
            with self.subTest(field=field, value=value):
                policy = copy.deepcopy(self.example["profile"]["evaluation_order"])
                policy[field] = value
                self.assertFalse(self.validator.is_valid(self.with_policy(policy)))

    def test_extra_policy_field(self):
        policy = copy.deepcopy(self.example["profile"]["evaluation_order"])
        policy["sequncing"] = "language_defined"
        self.assertFalse(self.validator.is_valid(self.with_policy(policy)))

    def test_legacy_free_text_and_wrong_object_types(self):
        for policy in ("Evaluate left to right", None, [], {}):
            with self.subTest(policy=policy):
                self.assertFalse(self.validator.is_valid(self.with_policy(policy)))

    def test_old_schema_version(self):
        graph = copy.deepcopy(self.example)
        graph["schema_version"] = "0.1.0"
        self.assertFalse(self.validator.is_valid(graph))


if __name__ == "__main__":
    unittest.main()
