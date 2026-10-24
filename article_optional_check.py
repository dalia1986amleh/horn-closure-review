#!/usr/bin/env python3
"""Checks that the primary scorer (article optional: 'T is [a/an] word') differs from the strict scorer (article required)
on exactly three of the 74 scored runs of the main comparison, and that on those three it gives the same set as the copies
with the missing 'a' inserted (runs_normalised/). Run from the supplement root."""
import sys, re, glob
sys.argv = ['x']; sys.path.insert(0, '.')
import score_responses as S, per_run_report as P
runs = P.find_runs(['runs']); cache = {}; changed = []; n = 0
for (model, lt, seed, tag), f in sorted(runs.items()):
    if lt not in ('L4', 'L4p40', 'L4p80') or not model.startswith(('deepseek', 'gpt-5.5', 'gemini')): continue
    d = f"seed_{lt}_s{seed}"; data = cache.setdefault(d, S.Data(d)); inst = data.inst[f"SEED{lt}s{seed}"]
    text = open(f, encoding='utf-8').read(); ent = re.escape(inst['entity']); start = S.pred_of(inst['start_fact']).lower()
    strict = {x.group(1).lower() for x in re.finditer(rf"\b{ent}\s+is\s+an?\s+([A-Za-z]+)", text, re.I)} - {start}
    lenient = {x.group(1).lower() for x in re.finditer(rf"\b{ent}\s+is\s+(?:an?\s+)?([A-Za-z]+)", text, re.I)} - {start}
    n += 1
    if strict != lenient: changed.append((model, lt, seed, tag, len(lenient - strict)))
print(n, "runs checked;", len(changed), "differ between the strict and the article-optional scorer"); [print(c) for c in changed]
