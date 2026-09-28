import copy
import json
from pathlib import Path
import tempfile
import unittest

import library as lib


def sample(schema):
    if "const" in schema: return schema["const"]
    if "enum" in schema: return schema["enum"][0]
    if schema["type"] == "object": return {k: sample(v) for k, v in schema["properties"].items()}
    if schema["type"] == "boolean": return False
    if schema["type"] == "integer": return schema["minimum"]
    raise AssertionError(schema)


class LibraryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name)
        # Synthetic only: this is not a playable or approved real-world rulebook.
        self.raw = b"# Synthetic test rules\n\n<!-- rule.test -->\n\nSynthetic source evidence.\n"
        self.mechanics = sample(lib.MECHANICS)
        self.validation = {"schema_version": 1, "coverage": [
            {"mechanic_path": p, "passage_id": "rule.test", "quote": "Synthetic source evidence."}
            for p in lib.leaves(self.mechanics) if p != "schema_version"],
            "unresolved": [], "limitations": ["Synthetic fixture; not approved for play."]}
        self.examples = {"schema_version": 1, "cases": [{"id": "synthetic", "situation": "Test",
            "expected": "Test only", "passage_ids": ["rule.test"]}]}
        self.manifest = {"schema_version": 1, "ruleset_id": "9c4c7715-4d86-4eba-84fb-3e83fb3e9870",
            "revision": 1, "alias": "synthetic", "name": "Synthetic", "edition": "Test",
            "sport": "flag_football", "organization": "Test", "language": "en",
            "effective_from": "2026-10-03", "parent": None,
            "provenance": [{"title": "Synthetic", "url": "https://example.com/",
                "version": "test", "retrieved_on": "2026-09-28", "attribution": "Test",
                "redistribution": "original_work", "rights_statement": "Synthetic test fixture"}]}
        self.write()

    def write(self):
        (self.path / "rules.md").write_bytes(self.raw)
        files = {"rules.md": lib.sha(self.raw)}
        for name, data in [("mechanics", self.mechanics), ("validation", self.validation), ("examples", self.examples)]:
            payload = lib.canonical(data)
            (self.path / f"{name}.json").write_bytes(payload + b"\n")
            files[f"{name}.json"] = lib.sha(payload)
        self.manifest["files"] = files
        self.manifest["schema_sha256"] = lib.sha(lib.canonical(lib.SCHEMAS))
        self.manifest.pop("release_sha256", None)
        self.manifest["release_sha256"] = lib.sha(lib.canonical(self.manifest))
        (self.path / "manifest.json").write_bytes(lib.canonical(self.manifest) + b"\n")

    def test_valid(self):
        self.assertEqual(lib.check(self.path)["revision"], 1)

    def test_schemas_are_valid(self):
        for schema in lib.SCHEMAS.values(): lib.Draft202012Validator.check_schema(schema)

    def test_generated_schemas_match_source(self):
        for name, schema in lib.SCHEMAS.items():
            self.assertEqual(lib.load_json(lib.ROOT / "schemas" / "1" / f"{name}.schema.json"), schema)

    def test_changed_markdown(self):
        (self.path / "rules.md").write_bytes(self.raw + b"changed\n")
        with self.assertRaisesRegex(ValueError, "hash mismatch"): lib.check(self.path)

    def test_metadata_bound(self):
        altered = copy.deepcopy(self.manifest)
        altered["effective_from"] = "2026-10-10"
        (self.path / "manifest.json").write_bytes(lib.canonical(altered))
        with self.assertRaisesRegex(ValueError, "Release hash"): lib.check(self.path)

    def test_unknown_mechanic(self):
        self.mechanics["clock"]["gss_button"] = True
        self.write()
        with self.assertRaises(ValueError): lib.check(self.path)

    def test_missing_mechanic(self):
        del self.mechanics["mercy"]["leading_blitz_allowed"]
        self.write()
        with self.assertRaises(ValueError): lib.check(self.path)

    def test_warning_boolean_not_integer(self):
        self.mechanics["penalties"]["delay_of_game"]["warnings_per_team_per_game"] = True
        self.write()
        with self.assertRaises(ValueError): lib.check(self.path)

    def test_float_rejected(self):
        with self.assertRaises(ValueError): lib.canonical({"seconds": 25.0})

    def test_duplicate_json(self):
        (self.path / "bad.json").write_text('{"a":1,"a":2}')
        with self.assertRaisesRegex(ValueError, "Duplicate"): lib.load_json(self.path / "bad.json")

    def test_unsafe_integer(self):
        with self.assertRaises(ValueError): lib.canonical(9007199254740992)

    def test_unresolved_blocks(self):
        self.validation["unresolved"] = ["25 or 30 seconds?"]
        self.write()
        with self.assertRaises(ValueError): lib.check(self.path)

    def test_missing_source(self):
        self.validation["coverage"].pop()
        self.write()
        with self.assertRaisesRegex(ValueError, "Every mechanic"): lib.check(self.path)

    def test_wrong_quote(self):
        self.validation["coverage"][0]["quote"] = "Invented evidence"
        self.write()
        with self.assertRaisesRegex(ValueError, "Evidence quote"): lib.check(self.path)

    def test_unknown_example_passage(self):
        self.examples["cases"][0]["passage_ids"] = ["rule.invented"]
        self.write()
        with self.assertRaisesRegex(ValueError, "Unknown example"): lib.check(self.path)

    def test_duplicate_anchor(self):
        with self.assertRaises(ValueError): lib.passages(self.raw + b"<!-- rule.test -->\n")

    def test_crlf_rejected(self):
        with self.assertRaises(ValueError): lib.passages(self.raw.replace(b"\n", b"\r\n"))

    def test_html_rejected(self):
        with self.assertRaises(ValueError): lib.passages(self.raw + b"<script>alert(1)</script>\n")

    def test_symlink_rejected(self):
        target = self.path / "mechanics.json"
        target.unlink()
        target.symlink_to(self.path / "examples.json")
        with self.assertRaisesRegex(ValueError, "symlinks"): lib.check(self.path)

    def test_private_file_rejected(self):
        (self.path / "prompt.txt").write_text("Private")
        with self.assertRaisesRegex(ValueError, "Unexpected"): lib.check(self.path)


if __name__ == "__main__": unittest.main()
