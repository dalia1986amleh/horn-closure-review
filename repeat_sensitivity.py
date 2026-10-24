#!/usr/bin/env python3
"""Post hoc checks on the DeepSeek-V4-Pro repeat study (paper, Section 4.1). Reads repeat_stats.json (written by repeat_analysis.py).
(1) Sensitivity: in the cell L4p80 problem 2, the run scoring 0.987 (repeat 1) is replaced by the extra run (x1); the three-run means are recomputed.
(2) Same period: only runs sent on 22 October 2026 are used (repeats 1 and 2 of every cell, except repeat 1 of 80k problems 2 and 7, which was sent on 21 October).
Bootstrap: percentile, 20,000 resamples of the 8 problems, random.seed(1). Writes repeat_sensitivity.json. Run from the package root after repeat_analysis.py."""
import json, random
D = json.load(open("repeat_stats.json")); C = D["cells"]; x1 = list(D["extras"].values())[0]
def analyse(get):
    d = [get("L4p80", p) - get("L4", p) for p in range(1, 9)]
    random.seed(1); bs = sorted(sum(random.choice(d) for _ in d) / 8 for _ in range(20000))
    return dict(un=sum(get("L4", p) for p in range(1, 9)) / 8, p80=sum(get("L4p80", p) for p in range(1, 9)) / 8, change=sum(d) / 8,
                ci=[bs[500], bs[19499]], lower=sum(x < 0 for x in d), higher=sum(x > 0 for x in d))
def sens(l, p):
    r = C[f"{l}_{p}"]
    return (r[0] + r[2] + x1) / 3 if (l, p) == ("L4p80", 2) else sum(r) / 3
def same(l, p):
    r = C[f"{l}_{p}"]; xs = [r[2]] if (l == "L4p80" and p in (2, 7)) else [r[1], r[2]]
    return sum(xs) / len(xs)
out = {"all_runs": analyse(lambda l, p: sum(C[f"{l}_{p}"]) / 3), "replace_0.987_by_extra_run": analyse(sens), "same_session_22_oct": analyse(same), "extra_run_score": x1}
for k, v in out.items(): print(k, v if not isinstance(v, dict) else {a: (round(b, 3) if not isinstance(b, list) else [round(c, 3) for c in b]) for a, b in v.items()})
json.dump(out, open("repeat_sensitivity.json", "w"), indent=1)
