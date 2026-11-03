import collections
from tests.test_accuracy import load_cases, GOLDEN_FILE

def test_ids_unique_and_golden_set_not_shrunk():
    ids = [c["id"] for c in load_cases(GOLDEN_FILE)]
    assert len(ids) == len(set(ids)), "duplicate case ids"
    assert len(ids) >= 20, f"golden set shrank to {len(ids)} cases"

def test_every_requirement_has_cases():
    reqs = collections.Counter(c["req"] for c in load_cases(GOLDEN_FILE))
    for r in ("REQ-001", "REQ-002", "REQ-003", "REQ-004"):
        assert reqs[r] > 0, f"no cases for {r}"