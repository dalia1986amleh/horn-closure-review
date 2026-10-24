#!/usr/bin/env python3
"""Per-run report, ground-truth audit, join recovery and error analysis.  No API calls.

  python3 per_run_report.py                 # uses runs/  (plus any dir given as extra arguments)
  python3 per_run_report.py runs other_dir  # several answer folders

Writes:  per_run_report.csv  (one row per run)   and prints four sections:
  1. per-run results (model, level, seed, tag, soundness, completeness, repeat counts)
  2. variation per model and level (n runs, n problems, mean, SD, min, median, max)
  3. ground-truth audit (independent closure; same closure for every padding condition)
  4. join recovery vs comparable chain facts, conditional on the antecedents being listed
  5. errors: missing entailed facts vs unsupported extra statements, by type
Findings are reported as observed output patterns. Nothing here tests a mechanism.
"""
import csv, glob, os, re, statistics as st, sys
from collections import defaultdict, Counter

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import score_responses as S
import derivation_graph as G
csv.field_size_limit(10**9)


# ---------------------------------------------------------------- independent solver (backward proof search)
def parse_rules(prem):
    rules = []
    for ln in prem.splitlines():
        ln = ln.strip().rstrip(".")
        if not ln.startswith("Every ") or " that is not a " in ln: continue
        body, head = ln[6:].rsplit(" is a ", 1)
        ants = tuple(x.strip() for x in body.replace(" that is also a ", "|").split("|"))
        rules.append((ants, head.strip()))
    return rules

def provable(start, rules):
    by_head = defaultdict(list)
    for ants, h in rules: by_head[h].append(ants)
    memo, stack = {}, set()
    def prove(p):
        if p == start: return True
        if p in memo: return memo[p]
        if p in stack: return False
        stack.add(p); ok = any(all(prove(a) for a in ants) for ants in by_head.get(p, [])); stack.discard(p); memo[p] = ok
        return ok
    return {p for p in list(by_head) if prove(p)} - {start}

def edit1(a, b):
    if a == b: return True
    if abs(len(a) - len(b)) > 1: return False
    if len(a) == len(b): return sum(x != y for x, y in zip(a, b)) == 1
    s, l = (a, b) if len(a) < len(b) else (b, a)
    return any(l[:i] + l[i + 1:] == s for i in range(len(l)))


# ---------------------------------------------------------------- run discovery
PAT = re.compile(r"^(?:[0-9a-f]{8}-)?(?P<model>.+?)__(?:PROMPT_SEED_)(?P<lvl>L\d(?:p\d+)?)_s(?P<seed>\d+)_A__(?P<tag>[A-Za-z0-9]+)$")

def find_runs(dirs):
    out = {}
    for d in dirs:
        for f in sorted(glob.glob(os.path.join(d, "*.txt"))):
            b = os.path.basename(f)[:-4]
            if b.endswith("__reasoning"): continue
            m = PAT.match(b)
            if not m or not open(f, encoding="utf-8").read().strip(): continue
            model = m["model"].replace("__high", "")
            out[(model, m["lvl"], int(m["seed"]), m["tag"])] = f
    return out

def read_json(f):
    p = f[:-4] + ".json"
    try:
        import json; return json.load(open(p, encoding="utf-8"))
    except Exception: return {}


# ---------------------------------------------------------------- scoring one run
cache = {}
def score_run(key, f):
    model, lvl, seed, tag = key
    d = os.path.join(HERE, f"seed_{lvl}_s{seed}"); iid = f"SEED{lvl}s{seed}"
    if not os.path.isdir(d): return None
    data = cache.setdefault(d, S.Data(d)); inst = data.inst[iid]
    text = open(f, encoding="utf-8").read()
    start = S.pred_of(inst["start_fact"]).lower()
    pat = re.compile(rf"\b{re.escape(inst['entity'])}\s+is\s+an?\s+([A-Za-z]+)", re.I)
    found = {m.group(1).lower() for m in pat.finditer(text)} - {start}
    gold = {S.pred_of(it["statement"]).lower(): it for it in data.items[iid] if it["item_type"] == "derived_fact"}
    _, rr, heads, _neg = G.graph(inst, set(gold))
    missing = set(gold) - found
    extras = found - set(gold)
    prem_words = set(re.findall(r"[a-z]+", inst["premises"].lower()))
    kinds = Counter()
    for p in extras:
        role = data.cat[iid].get(p, ("unknown", False))[0]
        if role in ("mirror_tree", "mirror_join", "mirror_start"): kinds["wrong_individual"] += 1
        elif role == "blocked_conjunction": kinds["blocked_conjunction"] += 1
        elif role.startswith("decoy"): kinds["decoy"] += 1
        elif role == "target_start": kinds["start_repeated_as_fact"] += 1
        elif any(edit1(p, g) for g in missing): kinds["typo_of_missing_fact"] += 1
        elif p in prem_words: kinds["padding_or_other_premise_word"] += 1
        else: kinds["word_not_in_premises"] += 1
    ok = lambda ants: all(a in found or a == start for a in ants)
    # derived-by-join (2 antecedents) vs derived-by-chain (1 antecedent) facts
    jf = {c: ants for ants, c in rr if len(ants) == 2}
    cf = {c: ants for ants, c in rr if len(ants) == 1}
    def rec(group): return (sum(c in found for c in group), len(group))
    jr, cr = rec(jf), rec(cf)
    jg = [c for c, a in jf.items() if ok(a)]; cg = [c for c, a in cf.items() if ok(a)]
    j = read_json(f)
    n_correct = len(found & set(gold))
    return dict(model=model, level=lvl, seed=seed, tag=tag, entity=inst["entity"], listed=len(found), correct=n_correct,
                key_size=len(gold), missing=len(missing), extras=len(extras),
                soundness=round(n_correct / len(found), 4) if found else "", completeness=round(n_correct / len(gold), 4),
                join_facts=jr[1], join_found=jr[0], chain_facts=cr[1], chain_found=cr[0],
                join_recall=round(jr[0] / jr[1], 3) if jr[1] else "", chain_recall=round(cr[0] / cr[1], 3) if cr[1] else "",
                joins_parents_listed=len(jg), join_found_given_parents=sum(c in found for c in jg),
                join_given_parents=round(sum(c in found for c in jg) / len(jg), 3) if jg else "",
                chains_parent_listed=len(cg), chain_found_given_parent=sum(c in found for c in cg),
                chain_given_parent=round(sum(c in found for c in cg) / len(cg), 3) if cg else "",
                **{f"extra_{k}": v for k, v in kinds.items()},
                reasoning_tokens=j.get("reasoning_tokens", ""), output_tokens=j.get("output_tokens", ""),
                finish=j.get("finish_reason", j.get("status", "")))


# ---------------------------------------------------------------- ground-truth audit
def audit():
    print("\n=== 3. GROUND-TRUTH AUDIT ===")
    bad = tot = 0; closures = {}
    for d in sorted(glob.glob(os.path.join(HERE, "seed_*"))):
        ip = os.path.join(d, "formal_logic_dataset_v4_instances.csv")
        if not os.path.exists(ip): continue
        data = S.Data(d)
        for iid, r in data.inst.items():
            tot += 1
            start = S.pred_of(r["start_fact"]).lower()
            ind = provable(start, parse_rules(r["premises"]))
            key = {S.pred_of(it["statement"]).lower() for it in data.items[iid] if it["item_type"] == "derived_fact"}
            closures[os.path.basename(d)] = (ind, r["entity"], set(r["premises"].splitlines()))
            if ind != key or len(key) != int(r["num_entailed_facts"]):
                bad += 1; print("  KEY MISMATCH", iid, len(ind), len(key), r["num_entailed_facts"])
    print(f"  independent backward-search solver vs stored key: {tot - bad}/{tot} agree")
    # same closure for each padding condition
    groups = defaultdict(dict)
    for name in closures:
        m = re.match(r"seed_(L\d)(p\d+)?_s(\d+)$", name)
        if m: groups[(m[1], int(m[3]))][m[2] or "p0"] = name
    same = diff = checked = 0
    for (lv, s), conds in sorted(groups.items()):
        if "p0" not in conds or len(conds) < 2: continue
        base = closures[conds["p0"]]
        for c, name in conds.items():
            if c == "p0": continue
            checked += 1
            ind, ent, lines = closures[name]
            same_closure = ind == base[0] and ent == base[1]
            subset = base[2] <= lines
            if same_closure and subset: same += 1
            else:
                diff += 1; print(f"  DIFFERENT: {name} vs {conds['p0']}: closure equal={same_closure}, unpadded premise lines all present={subset}")
    print(f"  padding conditions compared with their unpadded base (same level and seed): {same}/{checked} have an identical closure, "
          f"same target and all original premise lines present" + (f"; {diff} differ" if diff else ""))
    missing_base = [f"{lv}_s{s}" for (lv, s), c in groups.items() if "p0" not in c and len(c) >= 1]
    if missing_base: print("  padded problems without an unpadded base to compare:", ", ".join(sorted(missing_base)))
    return bad, diff


# ---------------------------------------------------------------- main
def main():
    dirs = sys.argv[1:] or [os.path.join(HERE, "runs")]
    runs = find_runs(dirs); rows = []
    for key, f in sorted(runs.items(), key=lambda kv: (kv[0][0], kv[0][1], kv[0][2], kv[0][3])):
        r = score_run(key, f)
        if r: rows.append(r)
    if not rows: print("no runs found"); return
    fields = []
    for r in rows:
        for k in r:
            if k not in fields: fields.append(k)
    cnt = Counter((r["model"], r["level"], r["seed"]) for r in rows)
    for r in rows: r["repeats_of_this_problem"] = cnt[(r["model"], r["level"], r["seed"])]
    fields.append("repeats_of_this_problem")
    with open(os.path.join(HERE, "per_run_report.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields); w.writeheader(); w.writerows(rows)

    print(f"=== 1. PER-RUN RESULTS ({len(rows)} runs; file per_run_report.csv) ===")
    print(f"{'model':<16}{'level':<7}{'seed':>4} {'tag':<4}{'listed':>6}{'key':>5}{'miss':>5}{'extra':>6}{'sound':>7}{'compl':>7}{'join':>6}{'chain':>6}{'rep':>4}")
    for r in rows:
        print(f"{r['model']:<16}{r['level']:<7}{r['seed']:>4} {r['tag']:<4}{r['listed']:>6}{r['key_size']:>5}{r['missing']:>5}{r['extras']:>6}"
              f"{r['soundness']!s:>7}{r['completeness']:>7}{r['join_recall']!s:>6}{r['chain_recall']!s:>6}{r['repeats_of_this_problem']:>4}")

    print("\n=== 2. VARIATION PER MODEL AND LEVEL (individual runs, not only means) ===")
    g = defaultdict(list)
    for r in rows: g[(r["model"], r["level"])].append(r)
    print(f"{'model':<16}{'level':<7}{'runs':>5}{'problems':>9}  {'completeness: mean  sd   min  med  max':<40}{'soundness: mean  min':<24}")
    for (m, l), rs in sorted(g.items()):
        c = [r["completeness"] for r in rs]; s = [r["soundness"] for r in rs if r["soundness"] != ""]
        sd = st.pstdev(c) if len(c) > 1 else 0
        print(f"{m:<16}{l:<7}{len(rs):>5}{len({r['seed'] for r in rs}):>9}  {st.mean(c):>6.3f} {sd:>5.3f} {min(c):>5.3f} {st.median(c):>5.3f} {max(c):>5.3f}      {st.mean(s):>6.3f} {min(s):>6.3f}")

    audit()

    print("\n=== 4. JOIN RECOVERY vs COMPARABLE CHAIN FACTS ===")
    print("join fact = derived by a two-condition rule; chain fact = derived by a one-condition rule.")
    print("'given parents' = only facts whose required antecedent(s) the model itself listed (or the start fact), so upstream loss is excluded.")
    print(f"{'model':<16}{'level':<7}{'runs':>5} {'join found/all':>16} {'chain found/all':>16} {'join | parents listed':>24} {'chain | parent listed':>24}")
    for (m, l), rs in sorted(g.items()):
        jf, ja = sum(r["join_found"] for r in rs), sum(r["join_facts"] for r in rs)
        cf, ca = sum(r["chain_found"] for r in rs), sum(r["chain_facts"] for r in rs)
        jg, jga = sum(r["join_found_given_parents"] for r in rs), sum(r["joins_parents_listed"] for r in rs)
        cg, cga = sum(r["chain_found_given_parent"] for r in rs), sum(r["chains_parent_listed"] for r in rs)
        pc = lambda a, b: f"{a}/{b} = {a / b:.2f}" if b else "n/a"
        print(f"{m:<16}{l:<7}{len(rs):>5} {pc(jf, ja):>16} {pc(cf, ca):>16} {pc(jg, jga):>24} {pc(cg, cga):>24}")

    print("\n=== 5. ERRORS: MISSING ENTAILED FACTS vs UNSUPPORTED EXTRA STATEMENTS ===")
    kinds = ["wrong_individual", "blocked_conjunction", "decoy", "typo_of_missing_fact", "padding_or_other_premise_word", "word_not_in_premises", "start_repeated_as_fact"]
    print(f"{'model':<16}{'level':<7}{'seed':>4} {'tag':<4}{'missing':>8}{'extras':>7}  " + " ".join(f"{k[:14]:>14}" for k in kinds))
    for r in rows:
        if r["missing"] == 0 and r["extras"] == 0: continue
        print(f"{r['model']:<16}{r['level']:<7}{r['seed']:>4} {r['tag']:<4}{r['missing']:>8}{r['extras']:>7}  " + " ".join(f"{r.get('extra_' + k, 0):>14}" for k in kinds))
    n0 = sum(1 for r in rows if r["missing"] == 0 and r["extras"] == 0)
    print(f"({n0} runs with no missing facts and no extra statements are not listed)")

if __name__ == "__main__":
    main()
