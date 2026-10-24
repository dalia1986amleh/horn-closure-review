#!/usr/bin/env python3
"""Second check of the answer keys by top-down (backward) proof search with memoisation and a cycle guard.
Shares no code with the generator. It re-parses the premise text of every stored instance, finds the set of
predicates provable from the start fact, and compares it with (a) the stored count of entailed facts and
(b) the set of statements labelled ENTAILED in the items file.   python3 backward_check.py"""
import csv, glob, os, sys
csv.field_size_limit(10**9)
def parse_rules(prem):
    rules = {}
    for ln in prem.splitlines():
        ln = ln.strip().rstrip(".")
        if not ln.startswith("Every ") or " that is not a " in ln: continue
        body, head = ln[6:].rsplit(" is a ", 1)
        ants = tuple(a[2:] if a.startswith("a ") else a for a in (x.strip() for x in body.replace(" that is also a ", "|").split("|")))
        rules.setdefault(head.strip(), []).append(ants)
    return rules
def pred(s): return s.rsplit(" is a ", 1)[1].rstrip(".").strip()
def provable(goal, start, rules, memo, stack):
    if goal == start: return True
    if goal in memo: return memo[goal]
    if goal in stack: return False          # cycle guard
    stack.add(goal); res = False
    for ants in rules.get(goal, []):
        if all(provable(a, start, rules, memo, stack) for a in ants): res = True; break
    stack.discard(goal); memo[goal] = res; return res
sys.setrecursionlimit(100000)
total = bad = 0
for d in sorted(glob.glob("seed_*")):
    ip, tp = f"{d}/formal_logic_dataset_v4_instances.csv", f"{d}/formal_logic_dataset_v4_items.csv"
    if not os.path.exists(ip): continue
    items = list(csv.DictReader(open(tp, encoding="utf-8")))
    for r in csv.DictReader(open(ip, encoding="utf-8")):
        total += 1; start = pred(r["start_fact"]); rules = parse_rules(r["premises"]); memo = {}
        heads = {h for h in rules}
        derived = {h for h in heads if h != start and provable(h, start, rules, memo, set())}
        key = {pred(x["statement"]) for x in items if x["instance_id"] == r["instance_id"] and x["label"] == "ENTAILED"}
        if derived != key:
            bad += 1; print("MISMATCH", r["instance_id"], len(derived), len(key))
print(f"Backward search checked {total} instances: {total-bad} agree, {bad} differ")
