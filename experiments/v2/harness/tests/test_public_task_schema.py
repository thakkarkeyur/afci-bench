"""Validate every public v2 task's front-matter against public_task.schema.json.

The public task schema (experiments/v2/schemas/public_task.schema.json) admits
functional metadata only and forbids any field that could carry a hidden answer
(additionalProperties: false). This test loads each authored public task body
under experiments/v2/tasks/public/, extracts its YAML front-matter, and validates
it against the schema using the repository's own subset validator
(context_audit.validate_against_schema). Pure file inspection; no model invoked.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

import context_audit as ca

REPO = Path(__file__).resolve().parents[4]
SCHEMA_PATH = REPO / "experiments" / "v2" / "schemas" / "public_task.schema.json"
PUBLIC_TASKS_DIR = REPO / "experiments" / "v2" / "tasks" / "public"


def _front_matter(text: str) -> dict:
    lines = text.splitlines(keepends=True)
    assert lines and lines[0].strip() == "---", "public task must start with YAML front-matter"
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            fm = "".join(lines[1:i])
            data = yaml.safe_load(fm)
            assert isinstance(data, dict), "front-matter must be a mapping"
            return data
    raise AssertionError("unterminated front-matter block")


def _public_task_files():
    if not PUBLIC_TASKS_DIR.is_dir():
        return []
    out = []
    for p in sorted(PUBLIC_TASKS_DIR.glob("*.md")):
        if p.name.lower() == "readme.md":
            continue
        # only actual task bodies carry front-matter; skip the human-facing report
        if p.name.upper().startswith(("PT", "PR", "T")) and p.stem[2:3].isdigit():
            out.append(p)
    return out


def test_public_task_schema_exists_and_is_closed():
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    assert schema.get("additionalProperties") is False, "schema must forbid unknown fields"
    assert set(schema["required"]) == {
        "id", "title", "category", "kind", "status", "visible_validation"
    }


def test_at_least_the_pilot_suite_is_present():
    names = {p.name for p in _public_task_files()}
    expected = {f"PT0{i}.md" for i in range(1, 7)} | {"PR01.md", "PR02.md"}
    assert expected <= names, f"missing authored public task bodies: {expected - names}"


@pytest.mark.parametrize("path", _public_task_files(), ids=lambda p: p.name)
def test_public_task_front_matter_matches_schema(path):
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    fm = _front_matter(path.read_text(encoding="utf-8"))
    errors = ca.validate_against_schema(fm, schema)
    assert errors == [], f"{path.name} front-matter schema errors: {errors}"
    # id in front-matter matches the filename stem
    assert fm["id"] == path.stem
    assert fm["visible_validation"] == "npm run ci:agent"
    assert fm["status"] == "candidate"
