#!/usr/bin/env python3
"""Pre-declared repeat plan for DeepSeek-V4-Pro (written BEFORE any repeat run). Cells: problems 1-8 x {unpadded L4, 80k L4p80}.
Target: 3 runs per cell = the original run + 2 repeats. The two earlier noise-check runs at 80k (problems 2 and 7, tag n1) count as repeat 1 for those cells,
so those two cells need only one new run (tag rep2). Run order is shuffled once with a fixed seed string so no cell is chosen by hand.
Writes repeat_runs_plan.csv and repeat_commands.sh. Output goes to runs_repeat/ (not runs/)."""
import csv, random
cells = []
for lv in ("L4", "L4p80"):
    for s in range(1, 9):
        for tag in ("rep1", "rep2"):
            if lv == "L4p80" and s in (2, 7) and tag == "rep1": continue   # already have n1 for these two cells
            cells.append((lv, s, tag))
random.Random("repeat-plan-v1|deepseek").shuffle(cells)
with open("repeat_runs_plan.csv", "w", newline="") as fh:
    w = csv.writer(fh); w.writerow(["order", "level", "seed", "tag"])
    for i, c in enumerate(cells, 1): w.writerow([i, *c])
L = ["#!/usr/bin/env bash",
     "# DeepSeek-V4-Pro repeat study: 30 runs, one at a time, in the pre-shuffled order of repeat_runs_plan.csv. Safe to re-run (finished runs are skipped).",
     "# Start in OFF-PEAK hours (UK time: peak is 02:00-05:00 and 07:00-11:00 Mon-Fri in BST when UTC+1; check the DeepSeek pricing page).",
     "# Key stays in your terminal:  export DEEPSEEK_API_KEY=...   Answers go to runs_repeat/.",
     "mkdir -p runs_repeat", "set -u"]
for i, (lv, s, tag) in enumerate(cells, 1):
    P = f"prompts_v2/PROMPT_SEED_{lv}_s{s}_A.txt"; I = f"SEED{lv}s{s}"; D = f"seed_{lv}_s{s}"
    L.append(f'ls runs_repeat/*PROMPT_SEED_{lv}_s{s}_A__{tag}.txt >/dev/null 2>&1 && echo "skip {i} {lv} s{s} {tag}" || \\')
    L.append(f'  python3 run_deepseek.py --prompt {P} --model deepseek-v4-pro --base-url https://api.deepseek.com --key-env DEEPSEEK_API_KEY --instance {I} --data-dir {D} --max-output-tokens 128000 --tag {tag} --out runs_repeat')
L.append('echo "done: send me the runs_repeat folder (no keys are stored in it)."')
open("repeat_commands.sh", "w").write("\n".join(L) + "\n")
print(len(cells), "runs")
