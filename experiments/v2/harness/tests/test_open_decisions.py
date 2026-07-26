"""Cross-check the open-decisions registry.

Every ``TD-*`` reference anywhere in the v2 protocol must resolve to a row in
docs/v2/OPEN_DECISIONS.csv, every entry must have an owner and a valid blocking
flag, none may be resolved yet, and the counts must be exactly 22 blocking +
6 non-blocking (TD-B16..TD-B21 were added by the pre-execution design-review
reconciliation; TD-B22 by the independent public review of the pilot task
package). Pure file inspection; no model is invoked.
"""
import csv
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
REGISTRY = REPO / "docs" / "v2" / "OPEN_DECISIONS.csv"
SCAN_DIRS = [REPO / "docs" / "v2", REPO / "experiments" / "v2"]
TEXT_EXT = {".md", ".csv", ".json", ".yml", ".yaml", ".py"}
TD_RE = re.compile(r"TD-[BN][0-9]+")


def _referenced_ids():
    found = set()
    for base in SCAN_DIRS:
        for p in base.rglob("*"):
            if p.is_file() and p.suffix in TEXT_EXT and "__pycache__" not in p.parts:
                found.update(TD_RE.findall(p.read_text(encoding="utf-8", errors="ignore")))
    return found


def _registry_rows():
    with open(REGISTRY, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def test_registry_columns_and_integrity():
    rows = _registry_rows()
    assert rows, "empty registry"
    ids = [r["decision_id"] for r in rows]
    assert len(ids) == len(set(ids)), "duplicate decision ids"
    for r in rows:
        assert r["blocking"] in {"yes", "no"}, r
        assert r["owner"].strip(), f"{r['decision_id']} has no owner"
        assert r["decision"].strip(), f"{r['decision_id']} has no decision text"
        assert r["status"].strip().lower() == "open", (
            f"{r['decision_id']} must be open in a protocol-freeze package"
        )


def test_counts_are_22_blocking_6_nonblocking():
    rows = _registry_rows()
    blocking = [r["decision_id"] for r in rows if r["blocking"] == "yes"]
    nonblocking = [r["decision_id"] for r in rows if r["blocking"] == "no"]
    assert sorted(blocking) == [f"TD-B{i:02d}" for i in range(1, 23)], blocking
    assert sorted(nonblocking) == [f"TD-N{i:02d}" for i in range(1, 7)], nonblocking
    assert len(blocking) == 22 and len(nonblocking) == 6


def test_every_referenced_todo_is_registered():
    registry_ids = {r["decision_id"] for r in _registry_rows()}
    referenced = _referenced_ids()
    missing = referenced - registry_ids
    assert not missing, f"referenced TODOs with no registry row: {sorted(missing)}"
    # and every registered id is actually referenced somewhere (no dead rows)
    dead = registry_ids - referenced
    assert not dead, f"registry rows never referenced: {sorted(dead)}"
