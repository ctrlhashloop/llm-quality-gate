import json
import os
import pathlib
import time
import re

from app.bot import ask

GOLDEN_FILE = "data/golden.jsonl"
REPORT_FILE = "reports/accuracy.json"
DELAY = float(os.getenv("CALL_DELAY", "4"))   # seconds between calls, for free-tier limits

REFUSAL = [
    "don't know", "do not know", "don't have", "do not have",
    "no information", "not able to", "unable to", "can't help", "cannot help",
    "can't provide", "cannot provide", "not available", "isn't available",
    "not mentioned", "not covered", "doesn't mention", "does not mention",
]


def load_cases(path):
    """Read a .jsonl file; skips blank lines and anything that isn't a JSON object."""
    cases = []
    text = pathlib.Path(path).read_text(encoding="utf-8-sig")   # strips a BOM if present
    for n, line in enumerate(text.splitlines(), start=1):
        line = line.strip()
        if not line or not line.startswith("{"):
            continue
        try:
            cases.append(json.loads(line))
        except json.JSONDecodeError as e:
            raise ValueError(f"{path} line {n} is not valid JSON: {e}\n{line[:120]}")
    return cases


def passed(case, output):
    o = output.lower()
    if any(s.lower() in o for s in case.get("must_not_include", [])):
        return False
    if any(re.search(p, output) for p in case.get("must_not_match", [])):
        return False
    if case["expect"] == "refuse":
        return any(p in o for p in REFUSAL)
    return all(m.lower() in o for m in case["must_include"])

def test_golden_set():
    cases = load_cases(GOLDEN_FILE)
    limit = int(os.getenv("CASE_LIMIT", len(cases)))
    cases = cases[:limit]
    assert cases, f"no cases found in {GOLDEN_FILE}"

    results = []
    for c in cases:
        print("asking", c["id"], flush=True)
        try:
            out = ask(c["question"])
            ok = passed(c, out)
            status = "PASS" if ok else "FAIL"
        except Exception as e:                      # infrastructure problem, not a product failure
            out, ok, status = f"ERROR: {e}", False, "ERROR"
        results.append({
            "id": c["id"],
            "req": c["req"],
            "question": c["question"],
            "expect": c["expect"],
            "status": status,
            "pass": ok,
            "output": out,
        })
        print(f"{status} {c['id']} - {c['question']}", flush=True)
        time.sleep(DELAY)

    scored = [r for r in results if r["status"] != "ERROR"]
    errored = len(results) - len(scored)
    rate = (sum(r["pass"] for r in scored) / len(scored)) if scored else 0.0
    print(f"\nPass rate: {rate:.0%} on {len(scored)} cases ({errored} errored)")

    pathlib.Path("reports").mkdir(exist_ok=True)
    pathlib.Path(REPORT_FILE).write_text(
        json.dumps({"pass_rate": rate, "scored": len(scored), "errored": errored,
                    "results": results}, indent=2),
        encoding="utf-8",
    )

    assert scored, "every call errored, so no cases could be scored"