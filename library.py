"""Offline proposed public artifact contract. No network, model, or publish authority."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parent
UUID = r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
ANCHOR = r"^rule\.[a-z0-9]+(?:\.[a-z0-9]+)*$"


def obj(fields):
    return {"type": "object", "properties": fields, "required": list(fields),
            "additionalProperties": False}


def integer(low, high):
    return {"type": "integer", "minimum": low, "maximum": high}


def enum(*values):
    return {"type": "string", "enum": list(values)}


TEXT = {"type": "string", "minLength": 1, "maxLength": 2000}
BOOL = {"type": "boolean"}
SHA = {"type": "string", "pattern": "^[a-f0-9]{64}$"}
PASSAGE = {"type": "string", "pattern": ANCHOR}

# PROPOSED portable semantics, not GSS's accepted runtime wire format.
MECHANICS = obj({
    "schema_version": {"const": 1},
    "players": obj({"per_side": integer(1, 30), "minimum_official": integer(1, 30),
                    "short_team_policy": enum("both_teams_short_only", "either_team_short", "forfeit")}),
    "clock": obj({"period_count": integer(1, 8), "period_seconds": integer(60, 7200),
        "mode": enum("running", "stopped"), "halftime_seconds": integer(0, 3600),
        "play_clock_seconds": integer(5, 120),
        "play_clock_start": enum("ready_for_play", "previous_play_over_and_ball_spotted"),
        "timeouts_per_team_per_period": integer(0, 10), "timeout_seconds": integer(0, 600),
        "final_two_minutes": enum("none", "stopped_final_period_unless_mercy"),
        "schedule_running_clock_option": BOOL}),
    "possession": obj({"drive_start_yards": integer(0, 50), "downs_to_midfield": integer(1, 10),
        "downs_to_score": integer(1, 10), "declared_punt": BOOL}),
    "snap": obj({"quarterback_minimum_depth_yards": integer(0, 20), "starts_on_ground": BOOL,
                 "sideways_allowed": BOOL}),
    "passing": obj({"quarterback_release_seconds": integer(1, 30),
                    "transfer_ends_release_count": BOOL, "forward_passes_max": integer(0, 3)}),
    "transfers": obj({"beyond_scrimmage_allowed": BOOL,
        "dropped_backward_pass": enum("dead_at_ground_spot_no_forward_gain", "live_fumble"),
        "quarterback_run_after_return_transfer": BOOL}),
    "rush": obj({"immediate_rushers_max": integer(0, 30), "line_yards": integer(0, 20),
        "raised_hand_required": BOOL, "delayed_blitz_allowed": BOOL,
        "defenders_released_after": enum("first_legal_transfer", "count_expires")}),
    "scoring": obj({"touchdown": integer(1, 20), "try_one": integer(0, 10),
        "try_two": integer(0, 10), "safety": integer(0, 10), "conversion_interception": integer(0, 10)}),
    "overtime": obj({"mode": enum("ties_stand", "timed", "shootout")}),
    "mercy": obj({"margin_points": integer(0, 100),
        "behavior": enum("none", "trailing_advantage", "end_game", "freeze_score_continue"),
        "trailing_start": enum("normal", "midfield"), "trailing_downs_to_score": integer(1, 10),
        "leading_downs_to_score": integer(1, 10), "leading_run_only": BOOL,
        "leading_blitz_allowed": BOOL, "run_only_overrides_no_run_zones": BOOL,
        "interception_start": enum("return_spot", "midfield"),
        "leading_conversion": enum("normal", "one_point_run_only")}),
    "no_run": obj({"enabled": BOOL, "before_midfield_yards": integer(0, 25),
                  "before_goal_yards": integer(0, 25)}),
    "field_policy": obj({"target_playing_length_yards": integer(20, 200),
        "target_width_yards": integer(10, 100), "target_end_zone_yards": integer(0, 30),
        "allow_safe_venue_variation": BOOL}),
    "contact": obj({"stationary_noncontact_screens_allowed": BOOL}),
    "equipment": obj({"mouthguard_required": BOOL}),
    "penalties": obj({"delayed_blitz": obj({"warnings_per_team_per_game": integer(0, 3),
        "first_replay_down": BOOL, "subsequent_yards": integer(0, 15),
        "subsequent_replay_down": BOOL, "automatic_first_down": BOOL, "offense_may_keep_play": BOOL}),
        "delay_of_game": obj({"warnings_per_team_per_game": integer(0, 3),
        "subsequent_yards": integer(0, 15), "subsequent_loss_of_down": BOOL,
        "referee_discretion": BOOL})}),
})

MANIFEST = obj({
    "schema_version": {"const": 1}, "ruleset_id": {"type": "string", "pattern": UUID},
    "revision": integer(1, 2147483647), "alias": {"type": "string", "pattern": "^[a-z0-9-]+$"},
    "name": TEXT, "edition": TEXT, "sport": {"const": "flag_football"},
    "organization": TEXT, "language": {"const": "en"},
    "effective_from": {"type": "string", "format": "date"},
    "parent": {"anyOf": [{"type": "null"}, obj({"ruleset_id": {"type": "string", "pattern": UUID},
        "revision": integer(1, 2147483647), "release_sha256": SHA})]},
    "provenance": {"type": "array", "minItems": 1, "items": obj({
        "title": TEXT, "url": {"type": "string", "pattern": "^https://", "format": "uri"},
        "version": TEXT, "retrieved_on": {"type": "string", "format": "date"},
        "attribution": TEXT, "redistribution": enum("original_work", "permission", "licensed"),
        "rights_statement": TEXT})},
    "files": obj({name: SHA for name in ("rules.md", "mechanics.json", "validation.json", "examples.json")}),
    "schema_sha256": SHA, "release_sha256": SHA,
})

VALIDATION = obj({"schema_version": {"const": 1},
    "coverage": {"type": "array", "minItems": 1, "items": obj({
        "mechanic_path": TEXT, "passage_id": PASSAGE, "quote": TEXT})},
    "unresolved": {"type": "array", "maxItems": 0, "items": TEXT},
    "limitations": {"type": "array", "items": TEXT}})
EXAMPLES = obj({"schema_version": {"const": 1}, "cases": {"type": "array", "minItems": 1,
    "items": obj({"id": {"type": "string", "pattern": "^[a-z0-9-]+$"},
        "situation": TEXT, "expected": TEXT,
        "passage_ids": {"type": "array", "minItems": 1, "uniqueItems": True, "items": PASSAGE}})}})
SCHEMAS = {"mechanics": MECHANICS, "manifest": MANIFEST, "validation": VALIDATION, "examples": EXAMPLES}


def canonical(value):
    def check(v):
        if v is None or isinstance(v, (str, bool)):
            return
        if type(v) is int and abs(v) <= 9007199254740991:
            return
        if isinstance(v, list):
            for item in v: check(item)
            return
        if isinstance(v, dict) and all(isinstance(k, str) for k in v):
            for item in v.values(): check(item)
            return
        raise ValueError("JSON permits only safe integers, strings, booleans, null, arrays and objects")
    check(value)
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def load_json(path):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result: raise ValueError("Duplicate JSON key")
            result[key] = value
        return result
    raw = Path(path).read_bytes()
    if len(raw) > 262144: raise ValueError("JSON file too large")
    value = json.loads(raw, object_pairs_hook=pairs)
    canonical(value)
    return value


def leaves(value, prefix=""):
    result = {}
    for key, item in value.items():
        path = f"{prefix}.{key}" if prefix else key
        if isinstance(item, dict): result.update(leaves(item, path))
        else: result[path] = item
    return result


def passages(raw):
    if not 1 <= len(raw) <= 49152: raise ValueError("Markdown size out of bounds")
    text = raw.decode("utf-8")
    if not text.startswith("# ") or not text.endswith("\n") or "\r" in text or "\0" in text:
        raise ValueError("Markdown must start with H1 and be LF-normalized with final newline")
    if len(re.findall(r"^# ", text, re.M)) != 1: raise ValueError("Exactly one H1 required")
    if re.search(r"[\u200b-\u200f\u202a-\u202e\u2066-\u2069]", text):
        raise ValueError("Hidden directional/control text is not permitted")
    matches = list(re.finditer(r"^<!-- (rule\.[a-z0-9]+(?:\.[a-z0-9]+)*) -->$", text, re.M))
    if not matches or len({m[1] for m in matches}) != len(matches):
        raise ValueError("Missing or duplicate passage IDs")
    result = {}
    for i, match in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        result[match[1]] = text[match.end():end]
    # Permit only anchor comments as raw HTML; browsers must still disable HTML rendering.
    without_anchors = re.sub(r"^<!-- rule\.[a-z0-9.]+ -->$", "", text, flags=re.M)
    if re.search(r"<\s*[!/a-zA-Z]", without_anchors): raise ValueError("Raw HTML is not permitted")
    if re.search(r"\]\(\s*(?:javascript|data|file):", text, re.I): raise ValueError("Unsafe link scheme")
    return result


def validate_schema(name, value):
    validator = Draft202012Validator(SCHEMAS[name], format_checker=FormatChecker())
    errors = sorted(validator.iter_errors(value), key=lambda e: str(e.path))
    if errors:
        error = errors[0]
        raise ValueError(f"{name}: {'.'.join(map(str, error.path))}: {error.validator} failed")
    # jsonschema regards 25.0 as an integer; canonical() rejects all floats.
    canonical(value)


def check(directory):
    directory = Path(directory)
    expected = {"rules.md", "mechanics.json", "manifest.json", "validation.json", "examples.json"}
    if {p.name for p in directory.iterdir()} != expected: raise ValueError("Unexpected or missing release files")
    if any(p.is_symlink() or not p.is_file() for p in directory.iterdir()): raise ValueError("No symlinks/directories in release")
    data = {name: load_json(directory / f"{name}.json") for name in SCHEMAS}
    for name, value in data.items(): validate_schema(name, value)
    sections = passages((directory / "rules.md").read_bytes())
    mechanics = data["mechanics"]
    if mechanics["players"]["minimum_official"] > mechanics["players"]["per_side"]:
        raise ValueError("Minimum players exceeds team size")
    if mechanics["rush"]["immediate_rushers_max"] > mechanics["players"]["per_side"]:
        raise ValueError("Rushers exceeds team size")
    fields = set(leaves(mechanics)) - {"schema_version"}
    covered = set()
    for row in data["validation"]["coverage"]:
        if row["mechanic_path"] not in fields: raise ValueError("Unknown mechanic reference")
        if row["passage_id"] not in sections or row["quote"] not in sections[row["passage_id"]]:
            raise ValueError("Evidence quote not found in cited passage")
        covered.add(row["mechanic_path"])
    if covered != fields: raise ValueError("Every mechanic requires source evidence")
    cases = data["examples"]["cases"]
    if len({c["id"] for c in cases}) != len(cases): raise ValueError("Duplicate example ID")
    for case in cases:
        if not set(case["passage_ids"]) <= sections.keys(): raise ValueError("Unknown example passage")
    manifest = data["manifest"]
    actual = {"rules.md": sha((directory / "rules.md").read_bytes())}
    actual.update({f"{name}.json": sha(canonical(data[name])) for name in ("mechanics", "validation", "examples")})
    if manifest["files"] != actual: raise ValueError("Content hash mismatch")
    if manifest["schema_sha256"] != sha(canonical(SCHEMAS)): raise ValueError("Schema hash mismatch")
    unsigned = {k: v for k, v in manifest.items() if k != "release_sha256"}
    if manifest["release_sha256"] != sha(canonical(unsigned)): raise ValueError("Release hash mismatch")
    return manifest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("schemas", "check", "check-all"))
    parser.add_argument("directory", nargs="?")
    args = parser.parse_args()
    if args.command == "schemas":
        dest = ROOT / "schemas" / "1"
        dest.mkdir(parents=True, exist_ok=True)
        for name, schema in SCHEMAS.items():
            (dest / f"{name}.schema.json").write_bytes(canonical(schema) + b"\n")
        return
    if args.command == "check":
        if not args.directory: parser.error("directory required")
        check(args.directory)
        print("Structurally verified; human semantic/rights approval still required")
        return
    count = 0
    for path in sorted((ROOT / "rulesets").glob("*/revisions/*")):
        manifest = check(path)
        if path.name != str(manifest["revision"]) or path.parent.parent.name != manifest["ruleset_id"]:
            raise ValueError("Release directory identity mismatch")
        count += 1
    print(f"Verified {count} release directories (not a publication approval)")


if __name__ == "__main__":
    main()
