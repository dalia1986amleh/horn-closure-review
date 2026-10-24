#!/usr/bin/env python3
"""Tables 4d to 4f: the DeepSeek-V4-Pro repeat study. Scores every stored answer with the primary rule (article optional), uses the
original run (tag d1, in runs/) and the two repeats of each unpadded (L4) and 80k (L4p80) cell, and writes repeat_stats.json.
Repeats: repeat_study/runs/ (tags rep1, rep2); for problems 2 and 7 at 80k, repeat 1 is the earlier run tagged n1 in noise_check_deepseek/.
Runs tagged x1 (one extra run, problem 2 at 80k) are reported but never enter a mean. Run from the package root."""
import re, glob, os, json, random, statistics as st
from math import comb
import score_responses as S
cache = {}
def score(path):
    m = re.search(r"PROMPT_SEED_(L4(?:p\d+)?)_s(\d+)_A__(\w+)\.txt$", path)
    lt, s = m.group(1), int(m.group(2))
    d = cache.setdefault(lt + str(s), S.Data(f"seed_{lt}_s{s}")); iid = f"SEED{lt}s{s}"; inst = d.inst[iid]
    text = open(path, encoding="utf-8").read(); start = S.pred_of(inst["start_fact"]).lower()
    pat = re.compile(rf"\b{re.escape(inst['entity'])}\s+is\s+(?:an?\s+)?([A-Za-z]+)", re.I)
    found = {x.group(1).lower() for x in pat.finditer(text)} - {start}
    gold = {S.pred_of(it["statement"]).lower() for it in d.items[iid] if it["item_type"] == "derived_fact"}
    return len(found & gold) / len(gold), len(found - gold)
def one(pattern):
    f = [p for p in glob.glob(pattern) if not p.endswith("__reasoning.txt")]; assert len(f) == 1, pattern; return score(f[0])
cells = {}; extras = {}
for lv in ("L4", "L4p80"):
    for p in range(1, 9):
        o = one(f"runs/*PROMPT_SEED_{lv}_s{p}_A__d1.txt")[0]
        if lv == "L4p80" and p in (2, 7): r1 = one(f"noise_check_deepseek/*PROMPT_SEED_{lv}_s{p}_A__n1.txt")[0]
        else: r1 = one(f"repeat_study/runs/*PROMPT_SEED_{lv}_s{p}_A__rep1.txt")[0]
        r2 = one(f"repeat_study/runs/*PROMPT_SEED_{lv}_s{p}_A__rep2.txt")[0]
        cells[f"{lv}_{p}"] = [o, r1, r2]
for f in glob.glob("repeat_study/runs/*__x1.txt"): extras[os.path.basename(f)] = score(f)[0]
wrong = {os.path.basename(f): score(f)[1] for f in glob.glob("repeat_study/runs/*__rep[12].txt")}
def analyse(get):
    d = [get("L4p80", p) - get("L4", p) for p in range(1, 9)]
    random.seed(1); bs = sorted(sum(random.choice(d) for _ in d) / 8 for _ in range(20000))
    lo = sum(x < 0 for x in d); hi = sum(x > 0 for x in d); n = lo + hi; k = min(lo, hi)
    return dict(un=sum(get("L4", p) for p in range(1, 9)) / 8, p80=sum(get("L4p80", p) for p in range(1, 9)) / 8, change=sum(d) / 8,
                ci=[bs[500], bs[19499]], lower=lo, higher=hi, sign_p=min(1, 2 * sum(comb(n, i) for i in range(k + 1)) / 2 ** n))
res = {"all3_mean": analyse(lambda l, p: sum(cells[f"{l}_{p}"]) / 3), "original_only": analyse(lambda l, p: cells[f"{l}_{p}"][0]),
       "first_repeat_only": analyse(lambda l, p: cells[f"{l}_{p}"][1]), "second_repeat_only": analyse(lambda l, p: cells[f"{l}_{p}"][2])}
for k, v in res.items(): print(k, {a: (round(b, 3) if not isinstance(b, list) else [round(x, 3) for x in b]) for a, b in v.items()})
print("cell: runs mean range sd")
for k, v in sorted(cells.items()): print(k, [round(x, 3) for x in v], round(sum(v) / 3, 3), round(max(v) - min(v), 3), round(st.stdev(v), 3))
print("extra runs (not in any mean):", {k: round(v, 3) for k, v in extras.items()})
print("repeat runs with unsupported statements:", {k: v for k, v in wrong.items() if v})
json.dump({"cells": cells, "analysis": res, "extras": extras}, open("repeat_stats.json", "w"), indent=1)
