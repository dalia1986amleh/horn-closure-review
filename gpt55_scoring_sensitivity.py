#!/usr/bin/env python3
"""GPT-5.5 under the two scoring rules, side by side (one run per cell; unit = problem).
primary = article optional (seeds_results_normalised.csv), strict = article required (seeds_results.csv).
Also: the problems/cells NOT touched by the format slip, and leave-one-out under both rules. Writes gpt55_scoring_sensitivity.json."""
import csv, json, random, statistics as st
from math import comb
from scipy import stats
rng = random.Random(1)
LV = {"L4": "9k", "L4p40": "40k", "L4p80": "80k"}
def load(path):
    v = {}
    for r in csv.DictReader(open(path)):
        if r["model"] == "gpt-5.5" and r["level"] in LV and r["completeness"]:
            v[(LV[r["level"]], int(r["seed"]))] = float(r["completeness"])
    return v
P, S = load("seeds_results_normalised.csv"), load("seeds_results.csv")
affected = sorted(k for k in P if abs(P[k] - S[k]) > 1e-9)
def sign(d):
    lo = sum(x < -1e-9 for x in d); hi = sum(x > 1e-9 for x in d); n = lo + hi
    p = min(1., 2 * sum(comb(n, i) for i in range(min(lo, hi) + 1)) / 2 ** n) if n else 1.
    return lo, hi, len(d) - n, p
def boot(x, n=20000):
    b = sorted(sum(rng.choice(x) for _ in x) / len(x) for _ in range(n)); return b[int(.025 * n)], b[int(.975 * n) - 1]
def paired(V, a, b, seeds):
    d = [V[(b, s)] - V[(a, s)] for s in seeds]
    lo, hi, tie, p = sign(d); bl, bh = boot(d)
    try: tp = float(stats.ttest_rel([V[(b, s)] for s in seeds], [V[(a, s)] for s in seeds]).pvalue)
    except Exception: tp = None
    try: wp = float(stats.wilcoxon(d).pvalue)
    except Exception: wp = None
    return dict(mean=st.mean(d), boot=[bl, bh], lower=lo, higher=hi, tie=tie, sign_p=p, t_p=tp, wilcoxon_p=wp, n=len(d))
seeds = list(range(1, 9)); out = {"affected_cells": affected, "per_problem": {}, "means": {}, "paired": {}, "subset": {}, "leave_one_out": {}}
for name, V in (("primary", P), ("strict", S)):
    out["per_problem"][name] = {l: [V[(l, s)] for s in seeds] for l in LV.values()}
    out["means"][name] = {l: st.mean(V[(l, s)] for s in seeds) for l in LV.values()}
    out["paired"][name] = {f"{a}->{b}": paired(V, a, b, seeds) for a, b in (("9k", "40k"), ("40k", "80k"), ("9k", "80k"))}
    loo = {}
    for a, b in (("9k", "40k"), ("9k", "80k")):
        vals = [st.mean(V[(b, s)] - V[(a, s)] for s in seeds if s != d) for d in seeds]; loo[f"{a}->{b}"] = [min(vals), max(vals)]
    out["leave_one_out"][name] = loo
# problems whose scores do not depend on the rule for the comparison in question
for a, b in (("9k", "40k"), ("9k", "80k"), ("40k", "80k")):
    ok = [s for s in seeds if (a, s) not in affected and (b, s) not in affected]
    out["subset"][f"{a}->{b}"] = dict(problems=ok, **paired(P, a, b, ok))
json.dump(out, open("gpt55_scoring_sensitivity.json", "w"), indent=1)
print("cells whose score depends on the rule:", affected)
for k in ("primary", "strict"):
    print(k, {l: round(m, 3) for l, m in out["means"][k].items()})
    for c, v in out["paired"][k].items(): print("  ", c, f"{v['mean']:+.3f} [{v['boot'][0]:+.3f},{v['boot'][1]:+.3f}] lower {v['lower']} higher {v['higher']} tie {v['tie']} sign {v['sign_p']:.3f} t {v['t_p']:.3f} W {v['wilcoxon_p']:.3f}")
    print("  LOO", {c: [round(x, 3) for x in r] for c, r in out["leave_one_out"][k].items()})
for c, v in out["subset"].items(): print("unaffected subset", c, v["problems"], f"{v['mean']:+.3f} lower {v['lower']} higher {v['higher']} tie {v['tie']} sign {v['sign_p']:.3f}")
