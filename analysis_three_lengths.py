#!/usr/bin/env python3
"""Three-length analysis (unpadded 9k, 40k, 80k) for three models. Unit = problem (seed). Where a cell has more than one run,
ONE run is chosen at random (cell_pick.py; fixed draw per cell; all other cells have one run); from seeds_results_normalised.csv (GPT-5.5 outputs lacking the word 'a' scored after inserting it).
Writes three_lengths_stats.json."""
import csv, json, random, re, statistics as st
from cell_pick import pick
from math import comb, sqrt
from scipy import stats
rng = random.Random(1)
M = {"deepseek": "DeepSeek-V4-Pro", "gpt-5.5": "GPT-5.5", "gemini-3.1-pro-preview": "Gemini 3.1 Pro"}
L = {"L4": "9k", "L4p40": "40k", "L4p80": "80k"}
runs = {}
for r in csv.DictReader(open("seeds_results_normalised.csv")):
    if r["model"] not in M or r["level"] not in L or not r["completeness"]: continue
    runs.setdefault((r["model"], r["level"], int(r["seed"])), []).append(r)
FIELDS = ["completeness", "soundness", "wrong", "chain_recall", "join_recall"]
best = {}
for k, rs in runs.items():
    chosen = pick(k[0], k[1], k[2], [r["run"] for r in rs]); r = [x for x in rs if x["run"] == chosen][0]
    best[k] = (len(rs), {f: ("" if r[f] == "" else float(r[f])) for f in FIELDS})
def vals(m, l, f="completeness"):
    out = []
    for s in range(1, 9):
        v = best[(m, l, s)][1][f]; out.append(None if v == "" else float(v))
    return out
def sign(x):
    lo = sum(v < -1e-9 for v in x); hi = sum(v > 1e-9 for v in x); n = lo + hi
    p = min(1., 2 * sum(comb(n, i) for i in range(min(lo, hi) + 1)) / 2 ** n) if n else 1.
    return lo, hi, 8 - n, p
def boot(x, n=20000):
    bs = sorted(sum(rng.choice(x) for _ in x) / len(x) for _ in range(n)); return bs[int(.025 * n)], bs[int(.975 * n) - 1]
out = {}
for m, name in M.items():
    d = {"completeness": {}, "soundness": {}, "chain": {}, "join": {}, "wrong": {}, "paired": {}}
    for l, lab in L.items():
        c = vals(m, l); d["completeness"][lab] = c
        s = vals(m, l, "soundness"); d["soundness"][lab] = s
        d["chain"][lab] = vals(m, l, "chain_recall"); d["join"][lab] = [x for x in vals(m, l, "join_recall") if x is not None]
        d["wrong"][lab] = [float(best[(m, l, s_)][1]["wrong"]) for s_ in range(1, 9)]
    for a, b in [("9k", "40k"), ("40k", "80k"), ("9k", "80k")]:
        x = [d["completeness"][b][i] - d["completeness"][a][i] for i in range(8)]
        lo, hi, tie, p = sign(x); bl, bh = boot(x)
        tt = stats.ttest_1samp(x, 0).pvalue if any(abs(v) > 1e-12 for v in x) else 1.
        try: w = stats.wilcoxon(x).pvalue
        except Exception: w = 1.
        d["paired"][a + "->" + b] = dict(mean=sum(x) / 8, boot=[bl, bh], lower=lo, higher=hi, tie=tie, sign_p=p, t_p=float(tt), wilcoxon_p=float(w), diffs=x)
    out[name] = d
json.dump(out, open("three_lengths_stats.json", "w"), indent=1)
mean = lambda v: sum(v) / len(v)
for name, d in out.items():
    print(name)
    for lab in L.values():
        sd = [x for x in d["soundness"][lab] if x is not None]
        print(f"  {lab}: comp {mean(d['completeness'][lab]):.3f} sd {st.stdev(d['completeness'][lab]):.3f} min {min(d['completeness'][lab]):.2f} | sound {mean(sd):.3f} min {min(sd):.3f} runs-with-wrong {sum(w>0 for w in d['wrong'][lab])} max wrong {max(d['wrong'][lab])} | chain {mean(d['chain'][lab]):.2f} join {mean(d['join'][lab]):.2f} join<chain {sum(j<c for j,c in zip(d['join'][lab],d['chain'][lab])) if len(d['join'][lab])==8 else 'n/a'}")
    for k, p in d["paired"].items():
        print(f"  {k}: {p['mean']:+.3f} [{p['boot'][0]:+.3f},{p['boot'][1]:+.3f}] lower {p['lower']} higher {p['higher']} tie {p['tie']} sign {p['sign_p']:.3f} t {p['t_p']:.3f} W {p['wilcoxon_p']:.3f}")
