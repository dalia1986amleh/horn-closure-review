#!/usr/bin/env python3
"""Derivation graph per problem + derivation-aware scoring.  No API calls.
  python3 derivation_graph.py check            # is every derived fact derivable by exactly one rule (unique proof)?
  python3 derivation_graph.py score [runs_dir] # per-run: recovery, support, orphans, rule-application coverage, join scores
Definitions (positive Horn rules; negation rules are reported but not graphed):
  node          = a predicate derived for the target entity
  rule instance = (antecedents -> consequent); a chain rule has 1 antecedent, a join rule has 2
  fact recovery = gold facts asserted / gold facts                         (= completeness)
  supported     = an asserted gold fact whose antecedents are all asserted too
  orphan        = an asserted gold fact with a missing antecedent (produced without its derivation)
  application   = a rule instance counts as covered if antecedents AND consequent are all asserted
  join score    = join facts asserted / join facts; conditional = among joins whose BOTH antecedents are asserted
"""
import glob, os, re, sys
from collections import defaultdict
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import score_responses as S

def parse(prem):
    rules, neg = [], 0
    for ln in prem.splitlines():
        ln = ln.strip()
        if not ln.startswith("Every "): continue
        if " that is not a " in ln: neg += 1; continue
        if " that is also a " in ln:
            a, rest = ln[6:].split(" that is also a "); b, c = rest.rstrip(".").split(" is a ")
            rules.append(((a.lower(), b.lower()), c.lower()))
        else:
            a, c = ln[6:].rstrip(".").split(" is a "); rules.append(((a.lower(),), c.lower()))
    return rules, neg

def graph(inst, gold):
    rules, neg = parse(inst["premises"]); start = S.pred_of(inst["start_fact"]).lower()
    by_head = defaultdict(list)
    for ants, c in rules: by_head[c].append(ants)
    inst_rules = [(ants, c) for ants, c in rules if c in gold and all(a in gold or a == start for a in ants)]
    heads = defaultdict(list)
    for ants, c in inst_rules: heads[c].append(ants)
    return start, inst_rules, heads, neg

def datadirs():
    return sorted(d for d in glob.glob(os.path.join(HERE, "*/")) if os.path.exists(os.path.join(d, "formal_logic_dataset_v4_instances.csv")))

def check():
    tot = multi = 0
    for d in datadirs():
        data = S.Data(d)
        for iid, inst in data.inst.items():
            gold = {S.pred_of(it["statement"]).lower() for it in data.items[iid] if it["item_type"] == "derived_fact"}
            start, rr, heads, neg = graph(inst, gold)
            m = [h for h, v in heads.items() if len(v) > 1]
            tot += 1; multi += bool(m)
            if m or neg: print(f"{os.path.basename(d.rstrip('/'))}: facts with >1 rule: {len(m)}  negation rules: {neg}")
    print(f"{tot} instances checked; {multi} contain a fact derivable by more than one rule")

def locate(b):
    for pat, f in ((r"PROMPT_SEED_(L\d(?:p\d+)?)_s(\d+)_A", lambda m: (f"seed_{m[1]}_s{m[2]}", f"SEED{m[1]}s{m[2]}")),
                   (r"PROMPT_LADDER_(L\d)_A", lambda m: (f"ladder_{m[1]}", f"LAD{m[1][1:]}_joins")),
                   (r"PROMPT_NEST_NS(\d)_s(\d)_A", lambda m: (f"nesting_NS{m[1]}_s{m[2]}", f"NEST{m[1]}s{m[2]}"))):
        m = re.search(pat, b)
        if m: return f(m)
    return None, None

def score(runs):
    cache, out = {}, []
    for f in sorted(glob.glob(os.path.join(runs, "*.txt"))):
        b = re.sub(r"^[0-9a-f]{8}-", "", os.path.basename(f))[:-4]; d, iid = locate(b)
        if not d or not os.path.isdir(os.path.join(HERE, d)): continue
        text = open(f, encoding="utf-8").read()
        if not text.strip(): continue
        data = cache.setdefault(d, S.Data(os.path.join(HERE, d))); inst = data.inst[iid]
        gold = {S.pred_of(it["statement"]).lower(): it for it in data.items[iid] if it["item_type"] == "derived_fact"}
        start, rr, heads, neg = graph(inst, set(gold))
        pat = re.compile(rf"\b{re.escape(inst['entity'])}\s+is\s+an?\s+([A-Za-z]+)", re.I)
        found = {m.group(1).lower() for m in pat.finditer(text)} - {start}
        if not (found & set(gold)): continue
        A = found & set(gold)
        ok = lambda ants: all(a in found or a == start for a in ants)
        orphan = [p for p in A if any(not ok(ants) for ants in heads[p]) and not any(ok(ants) for ants in heads[p])]
        app = [(ants, c) for ants, c in rr]; cov = sum(ok(ants) and c in found for ants, c in app)
        joins = [(ants, c) for ants, c in rr if len(ants) == 2]
        cond = [c for ants, c in joins if ok(ants)]
        out.append(dict(run=b.split("PROMPT_")[1], facts=len(gold), recovery=round(len(A)/len(gold), 3), orphans=len(orphan),
                        app_cov=round(cov/len(app), 3), join_all=round(sum(c in found for _, c in joins)/len(joins), 3) if joins else "",
                        join_given_parents=round(sum(c in found for c in cond)/len(cond), 3) if cond else "", joins_with_parents=len(cond), neg_rules=neg))
    return out

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "check": check()
    else:
        import csv
        rows = score(sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "runs"))
        for r in rows: print(r)
        if rows:
            with open(os.path.join(HERE, "derivation_scores.csv"), "w", newline="") as fh:
                w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
