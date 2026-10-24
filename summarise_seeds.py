#!/usr/bin/env python3
"""Scores every runs/*PROMPT_SEED_* answer, prints per model x condition results with 95% bootstrap CIs over instances, and checks hypotheses H1-H5.
Usage: python3 summarise_seeds.py            (reads runs/, writes seeds_results.csv)"""
import csv, glob, json, os, random, re, sys
from collections import defaultdict
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import score_responses as S
RUNS = os.environ.get("RUNS_DIR", os.path.join(HERE, "runs"))
rng = random.Random(1)

def ci(xs, n=10000):
    xs = [x for x in xs if x is not None]
    if not xs: return ("", "", "")
    m = sum(xs) / len(xs)
    if len(xs) < 2: return (m, m, m)
    bs = sorted(sum(rng.choice(xs) for _ in xs) / len(xs) for _ in range(n))
    return (m, bs[int(.025 * n)], bs[int(.975 * n) - 1])

def fmt(t): return "   n/a          " if t[0] == "" else f"{t[0]:.2f} [{t[1]:.2f},{t[2]:.2f}]"

rows, cache = [], {}
for f in sorted(glob.glob(os.path.join(RUNS, "*PROMPT_SEED_*_A*.txt"))):
    b = os.path.basename(f)[:-4]
    if b.endswith("__reasoning"): continue  # reasoning text is not an answer
    m = re.search(r"PROMPT_SEED_(L\d(?:p\d+)?)_s(\d+)_A", b)
    if not m: continue
    lt, s = m.groups(); parts = b.split("__"); model = "deepseek" if parts[0].startswith("deepseek") else "gpt-5.5" if parts[0].startswith("gpt-5.5") else "gpt-5-mini" if parts[0].startswith("gpt-5-mini") else parts[0]
    effort = parts[1] if parts[0].startswith(("gpt", "gemini")) and len(parts) > 2 and parts[1] in ("high", "medium", "low", "minimal") else ""
    d = os.path.join(HERE, f"seed_{lt}_s{s}"); iid = f"SEED{lt}s{s}"
    data = cache.setdefault(d, S.Data(d)); text = open(f, encoding="utf-8").read()
    meta = {}
    if os.path.exists(f[:-4] + ".json"):
        try: meta = json.load(open(f[:-4] + ".json"))
        except Exception: pass
    r = dict(model=model, effort=effort, level=lt, seed=int(s), run=parts[-1], finished=bool(text.strip()),
             reasoning_tokens=meta.get("reasoning_tokens"), input_tokens=meta.get("input_tokens"), status=meta.get("status", ""))
    if r["finished"]:
        sc = S.score_A(data, iid, text); inst = data.inst[iid]; start = S.pred_of(inst["start_fact"]).lower()
        pat = re.compile(rf"\b{re.escape(inst['entity'])}\s+is\s+an?\s+([A-Za-z]+)", re.I)
        found = {x.group(1).lower() for x in pat.finditer(text)} - {start}
        gold = {S.pred_of(it["statement"]).lower(): it for it in data.items[iid] if it["item_type"] == "derived_fact"}
        ch = [p for p, it in gold.items() if it["top_branch"] != "join"]; jn = [p for p, it in gold.items() if it["top_branch"] == "join"]
        r.update(completeness=sc["completeness"], soundness=sc["soundness"], wrong=sc["n_unsound"], mirror_err=sc["err_mirror_wrong_entity"],
                 blocked_err=sc["err_blocked_conjunction"], unknown_err=sc["err_unknown"],
                 chain_recall=sum(p in found for p in ch) / len(ch), join_recall=(sum(p in found for p in jn) / len(jn)) if jn else None)
    rows.append(r)
if not rows: sys.exit("no SEED runs found in " + RUNS)
cols = ["model", "effort", "level", "seed", "run", "finished", "completeness", "soundness", "wrong", "mirror_err", "blocked_err", "unknown_err", "chain_recall", "join_recall", "reasoning_tokens", "input_tokens", "status"]
with open(os.path.join(HERE, "seeds_results.csv"), "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore"); w.writeheader(); w.writerows(rows)

g = defaultdict(list)
for r in rows: g[(r["model"], r["effort"], r["level"])].append(r)
print(f"{'model':11s} {'eff':7s} {'level':6s} {'runs':>4s} {'fin':>4s}  {'completeness [95% CI]':22s} {'soundness':10s} {'chain':6s} {'join':6s} {'join<chain':>10s} {'reason tok':>10s} {'input tok':>9s}")
agg = {}
for k in sorted(g):
    rs = g[k]; fin = [r for r in rs if r["finished"]]
    comp = ci([float(r["completeness"]) for r in fin]); snd = [float(r["soundness"]) for r in fin if r["soundness"] != ""]
    chn = [r["chain_recall"] for r in fin]; jn = [r["join_recall"] for r in fin if r["join_recall"] is not None]
    jl = sum(1 for r in fin if r["join_recall"] is not None and r["join_recall"] < r["chain_recall"])
    rt = [r["reasoning_tokens"] for r in fin if r["reasoning_tokens"]]; it = [r["input_tokens"] for r in rs if r["input_tokens"]]
    agg[k] = dict(rs=rs, fin=fin, comp=comp, snd=snd, jl=jl)
    print(f"{k[0]:11s} {k[1]:7s} {k[2]:6s} {len(rs):4d} {len(fin):4d}  {fmt(comp):22s} {(sum(snd)/len(snd) if snd else float('nan')):10.3f} {(sum(chn)/len(chn) if chn else float('nan')):6.2f} {(sum(jn)/len(jn) if jn else float('nan')):6.2f} {jl:>6d}/{len(fin):<3d} {(int(sum(rt)/len(rt)) if rt else 0):10d} {(int(sum(it)/len(it)) if it else 0):9d}")

print("\nHypothesis checks (thresholds from design_experiment7_confirmatory.md; small samples, read with the CI):")
def get(model, level): return agg.get((model, "high", level)) or agg.get((model, "", level))
a = get("gpt-5-mini", "L4"); b = get("gpt-5.5", "L4") or get("gpt-5.5", "L5")
if a and a["fin"]: m, lo, hi = a["comp"]; print(f"H1 gpt-5-mini L4 mean completeness {m:.2f} [{lo:.2f},{hi:.2f}] -> " + ("supported (<=0.70, CI excludes 1.0)" if m <= .70 and hi < 1 else "REJECTED (>=0.90)" if m >= .90 else "inconclusive"))
for model in ("gpt-5-mini", "gpt-5.5", "deepseek"):
    ok = tot = 0
    for k, v in agg.items():
        if k[0] == model and k[1] in ("high", ""): ok += sum(1 for r in v["fin"] if r["soundness"] != "" and float(r["soundness"]) >= .97); tot += len(v["fin"])
    if tot: print(f"H2 {model}: soundness >= 0.97 in {ok}/{tot} finished runs ({ok/tot:.0%}) -> " + ("supported (>=90%)" if ok / tot >= .9 else "REJECTED (<80%)" if ok / tot < .8 else "inconclusive"))
for model in ("gpt-5-mini", "deepseek"):
    for lv in ("L3", "L4"):
        x = get(model, lv)
        if x and x["fin"]: print(f"H3 {model} {lv}: join recall below chain recall in {x['jl']}/{len(x['fin'])} instances -> " + ("supported (>=7/8)" if x["jl"] >= 7 else "REJECTED (<=5)" if x["jl"] <= 5 and len(x["fin"]) >= 8 else "inconclusive / too few instances"))
for model, lv in (("gpt-5.5", "L4"), ("gpt-5-mini", "L3"), ("deepseek", "L3")):
    base = get(model, lv)
    for pad in ("p20", "p60"):
        pr = get(model, lv + pad)
        if base and pr and pr["fin"]:
            bs = {r["seed"]: float(r["completeness"]) for r in base["fin"]}; ps = {r["seed"]: float(r["completeness"]) for r in pr["fin"] if r["seed"] in bs}
            if ps:
                drop = sum(bs[s] for s in ps) / len(ps) - sum(ps.values()) / len(ps)
                print(f"H4 {model} {lv} -> {lv+pad}: paired drop {drop:+.2f} over {len(ps)} seeds, finished {len(pr['fin'])}/{len(pr['rs'])} -> " + ("context length hurts (>=0.15)" if drop >= .15 else "no context effect (<0.05)" if drop < .05 else "inconclusive"))
for lv in ("L3", "L4"):
    x = get("deepseek", lv)
    if x: print(f"H5 deepseek {lv}: finished {len(x['fin'])}/{len(x['rs'])} ({len(x['fin'])/len(x['rs']):.0%}); targets: L3 >=80%, L4 <60%")
print("\nper-run table: seeds_results.csv   (an unfinished run is counted as 'did not finish', never as completeness 0)")
