#!/usr/bin/env python3
"""Third, solver-based check of the answer keys with Z3 (pip install z3-solver).
Every instance is a propositional Horn theory about the start individual: one Boolean per predicate,
rules a1 & a2 -> head, plus the start fact. Predicate p is entailed iff (theory AND NOT p) is UNSAT.
Compared with the stored key (items labelled ENTAILED). Run:  python3 z3_check.py            (all seed_* folders)
      python3 z3_check.py "seed_L4_s*"  (only the 8 unpadded base problems)"""
import csv, glob, os, sys
csv.field_size_limit(10**9)
from z3 import Bool, Solver, Implies, And, Not, unsat
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
def parse_rules(prem):
    rules = []
    for ln in prem.splitlines():
        ln = ln.strip().rstrip(".")
        if not ln.startswith("Every "): continue
        if " that is not a " in ln: raise ValueError("negation rule not handled")
        body, head = ln[6:].rsplit(" is a ", 1)
        ants = tuple(x.strip() for x in body.replace(" that is also a ", "|").split("|"))
        rules.append((tuple(a[2:] if a.startswith("a ") else a for a in ants), head.strip()))
    return rules
def pred(s): return s.rsplit(" is a ", 1)[1].rstrip(".").strip()
bad = total = 0
pat = sys.argv[1] if len(sys.argv) > 1 else "seed_*"
for d in sorted(glob.glob(pat)):
    ip, tp = f"{d}/formal_logic_dataset_v4_instances.csv", f"{d}/formal_logic_dataset_v4_items.csv"
    if not os.path.exists(ip): continue
    items = list(csv.DictReader(open(tp, encoding="utf-8")))
    for r in csv.DictReader(open(ip, encoding="utf-8")):
        total += 1; print("checking", r["instance_id"], flush=True); start = pred(r["start_fact"]); rules = parse_rules(r["premises"])
        names = {start} | {a for ants, h in rules for a in ants} | {h for _, h in rules}
        B = {n: Bool(n) for n in names}; s = Solver(); s.add(B[start])
        for ants, h in rules: s.add(Implies(And([B[a] for a in ants]), B[h]))
        derived = set()
        for n in names:
            if n == start: continue
            s.push(); s.add(Not(B[n])); ent = s.check() == unsat; s.pop()
            if ent: derived.add(n)
        key = {pred(x["statement"]) for x in items if x["instance_id"] == r["instance_id"] and x["label"] == "ENTAILED"}
        if derived != key:
            bad += 1; print("MISMATCH", r["instance_id"], len(derived), len(key), "only-z3:", len(derived-key), "only-key:", len(key-derived))
print(f"Z3 checked {total} instances: {total-bad} agree, {bad} differ")
