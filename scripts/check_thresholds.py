import json
import pathlib
import sys

import yaml


def load_json(path):
    p = pathlib.Path(path)
    if not p.exists():
        print(f"Missing {path}. Run the accuracy test and the Promptfoo eval first.")
        sys.exit(2)
    return json.loads(p.read_text(encoding="utf-8"))


t = yaml.safe_load(open("thresholds.yaml", encoding="utf-8"))
acc = load_json("reports/accuracy.json")
pf = load_json("reports/promptfoo.json")

# ---- Golden set (provider errors are already excluded from pass_rate) ----
acc_rate = acc["pass_rate"]
acc_err = acc.get("errored", 0)
acc_total = acc.get("total_cases", acc.get("scored", 0) + acc_err)
acc_failed = [r["id"] for r in acc.get("results", []) if r.get("status") == "FAIL"]

# ---- Promptfoo (failureReason 2 means provider error, not a product failure) ----
rows = pf["results"]["results"]
errored = [r for r in rows if r.get("failureReason") == 2]
scored = [r for r in rows if r.get("failureReason") != 2]
pf_pass = sum(1 for r in scored if r["success"])
pf_rate = pf_pass / len(scored) if scored else 0.0
pf_fail = [r for r in scored if not r["success"]]
distinct_tests = len({r["testCase"]["description"] for r in rows})
critical_fail = sorted({
    r["testCase"]["description"] for r in pf_fail
    if any(r["testCase"]["description"].startswith(p) for p in t["critical_prefixes"])
})

total_calls = acc_total + len(rows)
error_share = (acc_err + len(errored)) / total_calls if total_calls else 1.0

# ---- Checks ----
checks = [
    ("Golden-set size", acc_total >= t.get("min_golden_cases", 0),
     f"{acc_total} cases (min {t.get('min_golden_cases', 0)})"),
    ("Promptfoo test count", distinct_tests >= t.get("min_promptfoo_tests", 0),
     f"{distinct_tests} tests (min {t.get('min_promptfoo_tests', 0)})"),
    ("Golden-set accuracy", acc_rate >= t["accuracy_min"],
     f"{acc_rate:.0%} (min {t['accuracy_min']:.0%})"),
    ("Promptfoo pass rate", pf_rate >= t["promptfoo_pass_min"],
     f"{pf_rate:.0%} (min {t['promptfoo_pass_min']:.0%})"),
    ("Critical tests clean", not critical_fail,
     "none failed" if not critical_fail else ", ".join(critical_fail)),
    ("Infrastructure errors", error_share <= t["max_error_share"],
     f"{error_share:.0%} of calls (max {t['max_error_share']:.0%})"),
]

# ---- Summary (ASCII only so it prints on any Windows console) ----
lines = [
    "## Quality gate result",
    "",
    f"Provider: {acc.get('provider', 'unknown')} | Models: {', '.join(acc.get('models', [])) or 'unknown'} "
    f"| Weak prompt: {acc.get('weak_prompt', 'unknown')} | Run at: {acc.get('run_at', 'unknown')}",
    "",
    "| Check | Result | Detail |",
    "|---|---|---|",
]
for name, ok, detail in checks:
    lines.append(f"| {name} | {'PASS' if ok else 'FAIL'} | {detail} |")

if acc_failed:
    lines += ["", "### Failed golden-set cases", "", ", ".join(acc_failed)]
if pf_fail:
    lines += ["", "### Failed adversarial, privacy, robustness and bias tests", ""]
    for name in sorted({r["testCase"]["description"] for r in pf_fail}):
        n = sum(1 for r in pf_fail if r["testCase"]["description"] == name)
        lines.append(f"- {name}: {n} failing run(s)")

verdict = all(ok for _, ok, _ in checks)
lines += ["", f"**Gate: {'PASSED' if verdict else 'FAILED'}**"]
summary = "\n".join(lines)

pathlib.Path("reports").mkdir(exist_ok=True)
pathlib.Path("reports/gate_summary.md").write_text(summary, encoding="utf-8")
print(summary)
sys.exit(0 if verdict else 1)