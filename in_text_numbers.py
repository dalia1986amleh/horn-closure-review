#!/usr/bin/env python3
"""Recomputes the numbers quoted in the paper's text that are not in a table. No API calls.
Reads seeds_results_normalised.csv, seeds_results.csv (strict scorer), per_run_report.csv and root_miss_report.csv
(regenerate the last two with: python3 per_run_report.py runs_scored; python3 root_miss_analysis.py runs_scored).
One run per cell is chosen with cell_pick.py, as in every table.

Prints:
  1. leave-one-problem-out ranges of the mean paired change (Section 4, Appendix B)
  2. Gemini 3.1 Pro 40k alternatives: mean of its two runs, second runs only (Appendix B, Table 4b, Section 6)
  3. DeepSeek-V4-Pro 60k alternatives: mean of each problem's runs, all runs pooled (Appendix A)
  4. conditional join recovery, pooled over the eight chosen runs (Section 4, Appendices A and B)
  5. root and downstream misses for DeepSeek-V4-Pro, chosen runs (Section 4, Appendices A and B)
"""
import csv, random, statistics as st
from math import comb
from scipy import stats
from cell_pick import pick

def load(path):
    out = {}
    for r in csv.DictReader(open(path)):
        if r["completeness"]: out.setdefault((r["model"], r["level"], int(r["seed"])), {})[r["run"]] = float(r["completeness"])
    return out
NORM, STRICT = load("seeds_results_normalised.csv"), load("seeds_results.csv")
def chosen(table, m, l, s):
    runs = table[(m, l, s)]; return runs[pick(m, l, s, list(runs))]
def diffs(table, m, a, b):
    return [chosen(table, m, b, s) - chosen(table, m, a, s) for s in range(1, 9)]
def sign(x):
    lo = sum(v < -1e-9 for v in x); hi = sum(v > 1e-9 for v in x); n = lo + hi
    p = min(1., 2 * sum(comb(n, i) for i in range(min(lo, hi) + 1)) / 2 ** n) if n else 1.
    return lo, hi, 8 - n, p
def boot(x, n=20000, seed=1):
    rng = random.Random(seed)
    bs = sorted(sum(rng.choice(x) for _ in x) / len(x) for _ in range(n)); return bs[int(.025 * n)], bs[int(.975 * n) - 1]
def loo(x):
    m = [(sum(x) - v) / (len(x) - 1) for v in x]; return min(m), max(m)

print("1. Leave-one-problem-out range of the mean paired change")
for lab, table, m, a, b in [("DeepSeek-V4-Pro unpadded->80k", NORM, "deepseek", "L4", "L4p80"),
                            ("DeepSeek-V4-Pro unpadded->40k", NORM, "deepseek", "L4", "L4p40"),
                            ("Gemini 3.1 Pro unpadded->80k", NORM, "gemini-3.1-pro-preview", "L4", "L4p80"),
                            ("GPT-5.5 unpadded->80k, article optional", NORM, "gpt-5.5", "L4", "L4p80"),
                            ("GPT-5.5 unpadded->80k, strict", STRICT, "gpt-5.5", "L4", "L4p80")]:
    lo, hi = loo(diffs(table, m, a, b)); print(f"   {lab}: {lo:+.3f} to {hi:+.3f}")

print("2. Gemini 3.1 Pro at 40k: alternatives to the drawn run (problems 6 and 7 have two runs)")
G = "gemini-3.1-pro-preview"
for lab, how in [("mean of the two runs", "mean"), ("second runs only", "second")]:
    v40 = []
    for s in range(1, 9):
        runs = NORM[(G, "L4p40", s)]
        if len(runs) == 1: v40.append(list(runs.values())[0])
        elif how == "mean": v40.append(st.mean(runs.values())); print(f"   problem {s} mean of runs {st.mean(runs.values()):.3f}")
        else: v40.append(runs[sorted(runs)[-1]])
    v9 = [chosen(NORM, G, "L4", s) for s in range(1, 9)]; v80 = [chosen(NORM, G, "L4p80", s) for s in range(1, 9)]
    print(f"   {lab}: 40k mean {st.mean(v40):.3f}")
    for name, a, b in [("unpadded->40k", v9, v40), ("40k->80k", v40, v80)]:
        d = [y - x for x, y in zip(a, b)]; bl, bh = boot(d); lo, hi, tie, p = sign(d)
        print(f"      {name}: {st.mean(d):+.3f} bootstrap [{bl:+.3f}, {bh:+.3f}] lower/higher/unchanged {lo}/{hi}/{tie} sign p {p:.2f}")

print("3. DeepSeek-V4-Pro at 60k: alternatives to the drawn run")
D = "deepseek"
m60 = [st.mean(NORM[(D, "L4p60", s)].values()) for s in range(1, 9)]
d = [x - chosen(NORM, D, "L4", s) for s, x in zip(range(1, 9), m60)]
h = stats.t.ppf(.975, 7) * st.stdev(d) / 8 ** .5
allruns = [v for s in range(1, 9) for v in NORM[(D, "L4p60", s)].values()]
print(f"   mean of each problem's runs: 60k mean {st.mean(m60):.3f}; paired change {st.mean(d):+.3f} [{st.mean(d)-h:+.3f}, {st.mean(d)+h:+.3f}] (95% t)")
print(f"   all {len(allruns)} runs pooled: mean {st.mean(allruns):.3f}")
for s in range(1, 9):
    runs = NORM[(D, "L4p60", s)]
    if len(runs) > 1: print(f"   problem {s}: " + ", ".join(f"{k} {v:.2f}" for k, v in sorted(runs.items())) + f" (range {max(runs.values()) - min(runs.values()):.2f})")

MODEL = {"deepseek-v4-pro": "deepseek", "gpt-5.5": "gpt-5.5", "gemini-3.1-pro-preview": "gemini-3.1-pro-preview"}
def chosen_rows(path, m, l):
    rows = [r for r in csv.DictReader(open(path)) if r["model"] in MODEL and MODEL[r["model"]] == m and r["level"] == l]
    out = []
    for s in range(1, 9):
        rs = [r for r in rows if int(r["seed"]) == s]
        tag = pick(m, l, s, [r["tag"] for r in rs]); out.append([r for r in rs if r["tag"] == tag][0])
    return out

print("4. Conditional join recovery: two-condition facts listed among those whose two parents were listed (pooled, chosen runs)")
for m, levels in [("deepseek", ["L4p20", "L4p40", "L4p60", "L4p80"]), ("gpt-5.5", ["L4p40", "L4p80"]), (G, ["L4p40", "L4p80"])]:
    for l in levels:
        rs = chosen_rows("per_run_report.csv", m, l)
        found = sum(int(r["join_found_given_parents"]) for r in rs); listed = sum(int(r["joins_parents_listed"]) for r in rs)
        lost = sum(int(r["join_facts"]) - int(r["join_found"]) for r in rs)
        print(f"   {m} {l}: {found} of {listed}; joins lost {lost}, of which {listed - found} had both parents listed")

print("5. DeepSeek-V4-Pro root and downstream misses (chosen runs)")
for l in ["L4p20", "L4p40", "L4p60", "L4p80"]:
    rows = [r for r in csv.DictReader(open("root_miss_report.csv")) if r["model"] == "deepseek-v4-pro" and r["level"] == l]
    missed = root = 0
    for s in range(1, 9):
        rs = [r for r in rows if int(r["seed"]) == s]
        if not rs: continue                      # a run with no missed fact has no row
        tag = pick("deepseek", l, s, [r["tag"] for r in rs] if len(NORM[("deepseek", l, s)]) == len(rs) else list(NORM[("deepseek", l, s)]))
        r = [r for r in rs if r["tag"] == tag]
        if r: missed += int(r[0]["missed"]); root += int(r[0]["root"])
    print(f"   {l}: root misses {root} of {missed} missed facts; downstream {1 - root / missed:.0%}")
