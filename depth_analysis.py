#!/usr/bin/env python3
"""Fact-level breakdown (descriptive). For each model x length: recall of gold derived facts by derivation depth bin and by chain/join,
computed per problem and then averaged over the 8 problems (unit = problem); pooled counts also given. ONE run per cell (cell_pick.py; cells with more than one run are Gemini 40k problems 6 and 7); GPT-5.5 normalised copies (runs_scored/)."""
import csv, glob, json, os, re, sys
from cell_pick import pick
from collections import defaultdict
sys.path.insert(0, "."); import score_responses as S
M = {"deepseek": "DeepSeek-V4-Pro", "gpt-5.5": "GPT-5.5", "gemini-3.1-pro-preview": "Gemini 3.1 Pro"}
LV = {"L4": "9k", "L4p40": "40k", "L4p80": "80k"}
BINS = [(1, 5), (6, 10), (11, 15), (16, 99)]
best = {}
for f in glob.glob("runs_scored/*PROMPT_SEED_*_A*.txt"):
    b = os.path.basename(f)[:-4]; m = re.search(r"PROMPT_SEED_(L\d(?:p\d+)?)_s(\d+)_A", b)
    if not m or m.group(1) not in LV: continue
    p = b.split("__"); model = "deepseek" if p[0].startswith("deepseek") else "gpt-5.5" if p[0].startswith("gpt-5.5") else "gemini-3.1-pro-preview" if p[0].startswith("gemini") else None
    if not model: continue
    if not re.fullmatch(r"[a-z]\d+", p[-1]): continue   # skip the separate reasoning-text files
    n = int(re.sub(r"\D", "", p[-1]) or 0); k = (model, m.group(1), int(m.group(2)))
    best.setdefault(k, []).append((n, f))
cache = {}; res = {}; ngold = {}
for (model, lt, s), fl in sorted(best.items()):
  runcells = []
  _allruns = len(fl)
  _tag = pick(model, lt, s, [n for n, _ in fl]); fl_used = [(n, f) for n, f in fl if n == _tag]
  for _, f in sorted(fl_used):
    d = os.path.join(".", f"seed_{lt}_s{s}"); iid = f"SEED{lt}s{s}"; data = cache.setdefault(d, S.Data(d)); inst = data.inst[iid]
    text = open(f, encoding="utf-8").read(); start = S.pred_of(inst["start_fact"]).lower()
    pat = re.compile(rf"\b{re.escape(inst['entity'])}\s+is\s+an?\s+([A-Za-z]+)", re.I)
    found = {x.group(1).lower() for x in pat.finditer(text)} - {start}
    gold = {S.pred_of(it["statement"]).lower(): it for it in data.items[iid] if it["item_type"] == "derived_fact"}
    ngold[(lt, s)] = len(gold)
    cells = defaultdict(lambda: [0, 0])
    for pr, it in gold.items():
        dep = float(it["depth"]); typ = "join" if it["top_branch"] == "join" else "chain"
        for lo, hi in BINS:
            if lo <= dep <= hi: cells[("d", lo)][0] += pr in found; cells[("d", lo)][1] += 1
        cells[(typ, 0)][0] += pr in found; cells[(typ, 0)][1] += 1
        for lo, hi in BINS:
            if lo <= dep <= hi: cells[(typ + "_d", lo)][0] += pr in found; cells[(typ + "_d", lo)][1] += 1
    runcells.append(dict(cells))
  agg = {}
  for key in set(k for rc in runcells for k in rc):
    agg[key] = [sum(rc.get(key, [0, 0])[0] for rc in runcells) / len(runcells), runcells[0].get(key, [0, 0])[1]]
  res[(model, LV[lt], s)] = agg
out = {}
print("distinct gold derived facts per problem (same key at every length):", [ngold[("L4", s)] for s in range(1, 9)], "total", sum(ngold[("L4", s)] for s in range(1, 9)))
runs_facts = sum(ngold[(lt, s)] for (m, lt, s), fl in best.items())
print("scored fact-level judgements (gold facts x cells):", runs_facts, "in", len(best), "cells (one run each)")
for model, name in M.items():
    for lab in ("9k", "40k", "80k"):
        row = {}
        for key in [("d", lo) for lo, _ in BINS] + [("chain", 0), ("join", 0)] + [(t + "_d", lo) for t in ("chain", "join") for lo, _ in BINS]:
            per = []; pooled = [0, 0]
            for s in range(1, 9):
                c = res[(model, lab, s)].get(key)
                if c and c[1]: per.append(c[0] / c[1]); pooled[0] += c[0]; pooled[1] += c[1]
            row["|".join(map(str, key))] = dict(mean=sum(per) / len(per) if per else None, n_problems=len(per), found=pooled[0], total=pooled[1])
        out[f"{name}|{lab}"] = row
json.dump(out, open("depth_stats.json", "w"), indent=1)
for name in M.values():
    print(name)
    for lab in ("9k", "40k", "80k"):
        r = out[f"{name}|{lab}"]
        print(" ", lab, "depth bins (mean over problems):", [round(r[f"d|{lo}"]["mean"], 2) if r[f"d|{lo}"]["mean"] is not None else None for lo, _ in BINS], "| n facts", [r[f"d|{lo}"]["total"] for lo, _ in BINS], "| chain", round(r["chain|0"]["mean"], 2), "join", round(r["join|0"]["mean"], 2))
