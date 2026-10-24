#!/usr/bin/env python3
"""Root vs downstream misses.  No API calls.   python3 root_miss_analysis.py [runs_dir]

For every answer in runs/ (reasoning files are skipped):
  missed fact  = entailed fact the model did not list
  ROOT miss    = missed fact whose antecedent(s) the model DID list (or the start fact): the first break in a derivation
  DOWNSTREAM   = missed fact with at least one antecedent also missed: lost because something above it was lost
Also: how many top-level branches are lost entirely, the depth of the shallowest root miss, and for repeated runs of
the same problem the overlap of the missed sets.  Output patterns only; nothing here tests why a fact was missed.
Writes root_miss_report.csv
"""
import csv, glob, os, re, sys, statistics as st
from collections import defaultdict
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import score_responses as S
import derivation_graph as G
import per_run_report as P          # reuses run discovery and the answer parser
csv.field_size_limit(10**9)

def analyse(key, f, cache):
    model, lvl, seed, tag = key
    d = os.path.join(HERE, f"seed_{lvl}_s{seed}"); iid = f"SEED{lvl}s{seed}"
    if not os.path.isdir(d): return None
    data = cache.setdefault(d, S.Data(d)); inst = data.inst[iid]
    text = open(f, encoding="utf-8").read()
    start = S.pred_of(inst["start_fact"]).lower()
    pat = re.compile(rf"\b{re.escape(inst['entity'])}\s+is\s+an?\s+([A-Za-z]+)", re.I)
    found = {m.group(1).lower() for m in pat.finditer(text)} - {start}
    items = {S.pred_of(it["statement"]).lower(): it for it in data.items[iid] if it["item_type"] == "derived_fact"}
    _, rr, heads, _neg = G.graph(inst, set(items))
    ants_of = {c: ants for ants, c in rr}
    missed = {p for p in items if p not in found}
    root, down = set(), set()
    for p in missed:
        ants = ants_of.get(p, ())
        (down if any(a in missed for a in ants if a != start) else root).add(p)
    depth = lambda p: float(items[p]["depth"])
    by_branch = defaultdict(lambda: [0, 0])
    for p, it in items.items():
        b = it["top_branch"]
        by_branch[b][1] += 1; by_branch[b][0] += p in found
    tree_branches = {b: v for b, v in by_branch.items() if b not in ("join", "neg", "negcascade")}
    lost = sum(1 for a, n in tree_branches.values() if a == 0)
    partial = sum(1 for a, n in tree_branches.values() if 0 < a < n)
    full = sum(1 for a, n in tree_branches.values() if a == n)
    row = dict(model=model, level=lvl, seed=seed, tag=tag, key=len(items), missed=len(missed), root=len(root), downstream=len(down),
               root_share=round(len(root) / len(missed), 3) if missed else "",
               branches=len(tree_branches), branches_fully_listed=full, branches_partly_listed=partial, branches_not_listed=lost,
               first_root_depth=min((depth(p) for p in root), default=""), max_depth=float(inst["depth"]))
    return row, frozenset(missed)

def main():
    dirs = sys.argv[1:] or [os.path.join(HERE, "runs")]
    runs = P.find_runs(dirs); cache = {}; rows = []; missed_sets = defaultdict(list)
    for key, f in sorted(runs.items()):
        r = analyse(key, f, cache)
        if r:
            rows.append(r[0]); missed_sets[(key[0], key[1], key[2])].append((key[3], r[1]))
    with open(os.path.join(HERE, "root_miss_report.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)

    print("=== 1. MISSES PER RUN: root (first break) vs downstream (lost because a parent was lost) ===")
    print(f"{'model':<16}{'level':<7}{'seed':>4} {'tag':<4}{'missed':>7}{'root':>6}{'downstr':>8}{'root%':>7}  {'branches full/partial/none':>27}{'first root depth':>18}")
    for r in rows:
        if not r["missed"]: continue
        print(f"{r['model']:<16}{r['level']:<7}{r['seed']:>4} {r['tag']:<4}{r['missed']:>7}{r['root']:>6}{r['downstream']:>8}{str(round(100*r['root_share']))+'%':>7}  "
              f"{str(r['branches_fully_listed'])+'/'+str(r['branches_partly_listed'])+'/'+str(r['branches_not_listed']):>27}{str(r['first_root_depth'])+' of '+str(r['max_depth']):>18}")
    print("\n=== 2. BY MODEL AND LEVEL (runs with at least one miss) ===")
    g = defaultdict(list)
    for r in rows:
        if r["missed"]: g[(r["model"], r["level"])].append(r)
    for (m, l), rs in sorted(g.items()):
        tm, tr = sum(r["missed"] for r in rs), sum(r["root"] for r in rs)
        print(f"{m:<16}{l:<7} runs {len(rs):>2}  missed {tm:>5}  root {tr:>4} ({100*tr/tm:.0f}%)  downstream {tm-tr:>5}   "
              f"median root misses per run {st.median(r['root'] for r in rs):.0f} (min {min(r['root'] for r in rs)}, max {max(r['root'] for r in rs)})  "
              f"branches wholly unlisted per run: median {st.median(r['branches_not_listed'] for r in rs):.0f}")
    print("\n=== 3. REPEATED RUNS OF THE SAME PROBLEM: do they miss the same facts? ===")
    print("overlap = facts missed in both runs / facts missed in either run (1.0 = same facts, 0 = different facts)")
    any_ = False
    for k, lst in sorted(missed_sets.items()):
        for i in range(len(lst)):
            for j in range(i + 1, len(lst)):
                a, b = lst[i][1], lst[j][1]
                if a or b:
                    any_ = True
                    print(f"  {k[0]} {k[1]} seed {k[2]}  {lst[i][0]} vs {lst[j][0]}: missed {len(a)} / {len(b)}, both {len(a & b)}, overlap {len(a & b) / len(a | b):.2f}")
    if not any_: print("  no repeated runs with misses found")

if __name__ == "__main__":
    main()
