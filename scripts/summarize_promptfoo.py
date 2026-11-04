import json, sys, collections

def load(path):
    d = json.load(open(path, encoding="utf-8"))
    rows = d["results"]["results"]
    by = collections.OrderedDict()
    for r in rows:
        name = r["testCase"]["description"]
        by.setdefault(name, []).append(r)
    return by

strong = load("reports/promptfoo_strong.json")
weak = load("reports/promptfoo_weak.json")

print(f"{'test':42} {'strong':>8} {'weak':>8}")
for name in weak:
    s = strong.get(name, [])
    w = weak[name]
    sp = sum(1 for r in s if r["success"])
    wp = sum(1 for r in w if r["success"])
    print(f"{name[:42]:42} {sp:>3}/{len(s):<4} {wp:>3}/{len(w):<4}")

print("\nWEAK-BOT FAILURES (first 160 chars of each answer)")
for name, rs in weak.items():
    for r in rs:
        if not r["success"]:
            out = (r.get("response") or {}).get("output", "").replace("\n", " ")
            print(f"- {name}: {out[:400]}")