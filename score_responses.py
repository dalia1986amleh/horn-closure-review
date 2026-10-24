#!/usr/bin/env python3
"""
Score model outputs against formal_logic_dataset_v4.   (standard library only)

Inputs (keep the three dataset CSVs in --data-dir, default: this script's folder)
  A) a CSV with columns:  model, instance_id, format, output
        optional extra columns are carried through: thinking, finish_reason, output_tokens, notes
        format = A (generate everything) or B (label list)
  B) a folder of .txt files named   MODEL__INSTANCE__FORMAT.txt      e.g. gemini__J_j6_x6_01__A.txt
  C) a single file:  --one --model gpt --instance J_j6_x6_01 --format A --file out.txt

Examples
  python3 score_responses.py --responses responses.csv --out scored.csv
  python3 score_responses.py --dir responses/
  python3 score_responses.py --one --model gemini --instance J_j6_x6_01 --format A --file out.txt
  python3 score_responses.py --selftest                      # shows what each failure pattern scores

Format A metrics (per response)
  soundness      = asserted statements that are entailed / asserted statements        (the given fact is ignored)
  completeness   = entailed statements asserted / all entailed statements (bounded deductive completeness)
  leaf coverage  = share of branch-end facts asserted (tree branches and joins separately)
  err_*          = unsound assertions by type, from formal_logic_dataset_v4_predicates.csv
                   mirror_* = wrong entity, blocked_conjunction = "and" read as "or",
                   decoy_* = affirming the consequent, unknown = word not in the problem
Format B metrics: accuracy, recall of ENTAILED, specificity (NOT ENTAILED), yes-rate, accuracy by item type.
"""
import argparse, csv, os, re, sys
from collections import defaultdict, Counter

HERE = os.path.dirname(os.path.abspath(__file__))


def read_csv(path):
    csv.field_size_limit(sys.maxsize)          # padded instances have premise fields over 131,072 characters
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def pred_of(stmt):
    return stmt[:-1].split(" is a ")[1]


class Data:
    def __init__(self, d):
        self.inst = {r["instance_id"]: r for r in read_csv(os.path.join(d, "formal_logic_dataset_v4_instances.csv"))}
        self.items = defaultdict(list)
        for r in read_csv(os.path.join(d, "formal_logic_dataset_v4_items.csv")):
            self.items[r["instance_id"]].append(r)
        self.cat = defaultdict(dict)
        for r in read_csv(os.path.join(d, "formal_logic_dataset_v4_predicates.csv")):
            self.cat[r["instance_id"]][r["predicate"]] = (r["role"], r["entailed_for_target"] == "TRUE")


def ratio(a, b):
    return round(a / b, 4) if b else ""


# ------------------------------------------------------------------ format A
def score_A(data, iid, text):
    inst = data.inst[iid]
    ent, oth = inst["entity"], inst["other_entity"]
    start = pred_of(inst["start_fact"]).lower()
    gold_items = {pred_of(it["statement"]).lower(): it for it in data.items[iid] if it["item_type"] == "derived_fact"}
    cat = data.cat[iid]
    pat = lambda e: re.compile(rf"\b{re.escape(e)}\s+is\s+an?\s+([A-Za-z]+)", re.I)
    seen, A, total = set(), [], 0
    for m in pat(ent).finditer(text):
        p = m.group(1).lower()
        total += 1
        if p not in seen:
            seen.add(p)
            if p != start:
                A.append(p)
    correct = [p for p in A if p in gold_items]
    unsound = [p for p in A if p not in gold_items]
    errs = Counter(cat.get(p, ("unknown", False))[0] for p in unsound)

    def cov(sel):
        tot = [p for p, it in gold_items.items() if sel(it)]
        return ratio(sum(p in seen for p in tot), len(tot)), len(tot)

    tree_cov, _ = cov(lambda it: it["is_leaf"] == "TRUE" and it["top_branch"] not in ("join", "neg", "negcascade"))
    neg_rec, n_neg = cov(lambda it: it["top_branch"] == "neg")
    casc_rec, n_casc = cov(lambda it: it["top_branch"] == "negcascade")
    prem_neg = sum(n for r, n in errs.items() if r.startswith("neg_"))
    join_cov, n_join_leaves = cov(lambda it: it["is_leaf"] == "TRUE" and it["top_branch"] == "join")
    by_branch = defaultdict(lambda: [0, 0])
    for p, it in gold_items.items():
        if it["top_branch"] not in ("join", "neg", "negcascade"):
            by_branch[it["top_branch"]][1] += 1
            by_branch[it["top_branch"]][0] += p in seen
    branches_complete = ratio(sum(1 for a, b in by_branch.values() if a == b), len(by_branch))
    half = float(inst["depth"]) / 2
    shallow = [p for p, it in gold_items.items() if float(it["depth"]) <= half]
    deep = [p for p, it in gold_items.items() if float(it["depth"]) > half]
    blocked_total = sum(1 for p, (role, _) in cat.items() if role == "blocked_conjunction")
    out = dict(
        n_gold=len(gold_items), n_asserted=len(A), n_correct=len(correct), n_unsound=len(unsound),
        soundness=ratio(len(correct), len(A)), completeness=ratio(len(correct), len(gold_items)),
        leaf_cov_tree=tree_cov, leaf_cov_join=join_cov if n_join_leaves else "",
        branches_complete=branches_complete,
        recall_shallow=ratio(sum(p in seen for p in shallow), len(shallow)),
        recall_deep=ratio(sum(p in seen for p in deep), len(deep)),
        blocked_asserted=errs.get("blocked_conjunction", 0), blocked_rate=ratio(errs.get("blocked_conjunction", 0), blocked_total),
        err_mirror_wrong_entity=errs.get("mirror_tree", 0) + errs.get("mirror_join", 0) + errs.get("mirror_start", 0),
        err_blocked_conjunction=errs.get("blocked_conjunction", 0),
        err_decoy=errs.get("decoy_target_side", 0) + errs.get("decoy_mirror_side", 0),
        err_unknown=errs.get("unknown", 0),
        err_premature_negation=prem_neg if (n_neg or prem_neg) else "",
        neg_recall=neg_rec if n_neg else "", cascade_recall=casc_rec if n_casc else "",
        repeated_given=int(start in seen), other_entity_statements=len(pat(oth).findall(text)),
        statements_total=total, repeat_factor=ratio(total, len(seen)) if seen else "",
        looped="TRUE" if seen and total / len(seen) >= 3 else "",
    )
    return out


# ------------------------------------------------------------------ format B
LABEL = re.compile(r"(NOT[\s_\-]*ENTAILED|ENTAILED)", re.I)
NUM = re.compile(r"^\W*(\d+)\W")


def score_B(data, iid, text):
    items = sorted([it for it in data.items[iid] if it["in_label_set"] == "TRUE"], key=lambda r: int(r["label_order"]))
    ans = {}
    for line in text.splitlines():
        m, lab = NUM.match(line + " "), LABEL.search(line)
        if m and lab and int(m.group(1)) not in ans:
            ans[int(m.group(1))] = "NOT_ENTAILED" if lab.group(1).upper().startswith("NOT") else "ENTAILED"
    tp = tn = 0
    pos = [it for it in items if it["label"] == "ENTAILED"]
    neg = [it for it in items if it["label"] == "NOT_ENTAILED"]
    by_type = defaultdict(lambda: [0, 0])
    for it in items:
        guess = ans.get(int(it["label_order"]))
        ok = guess == it["label"]
        by_type[it["item_type"]][1] += 1
        by_type[it["item_type"]][0] += ok
        if ok and it["label"] == "ENTAILED": tp += 1
        if ok and it["label"] == "NOT_ENTAILED": tn += 1
    out = dict(n_items=len(items), answered=len(ans),
               accuracy=ratio(tp + tn, len(items)), recall_entailed=ratio(tp, len(pos)),
               specificity=ratio(tn, len(neg)),
               yes_rate=ratio(sum(1 for v in ans.values() if v == "ENTAILED"), len(ans)))
    for t in ("derived_fact", "transitive_rule", "unreachable_predicate", "affirming_consequent",
              "blocked_conjunction", "reversed_rule", "reversed_skip_rule", "cross_chain_rule"):
        out[f"acc_{t}"] = ratio(*by_type[t]) if t in by_type else ""
    return out


# ------------------------------------------------------------------ driver
def score_one(data, row):
    iid, fmt = row["instance_id"], row["format"].strip().upper()
    if iid not in data.inst:
        raise SystemExit(f"unknown instance_id: {iid}")
    res = score_A(data, iid, row["output"]) if fmt == "A" else score_B(data, iid, row["output"])
    fr = (row.get("finish_reason") or "").lower()
    base = dict(model=row["model"], instance_id=iid, condition=data.inst[iid]["condition"],
                experiment=data.inst[iid]["experiment"], format=fmt,
                thinking=row.get("thinking", ""), finish_reason=row.get("finish_reason", ""),
                output_tokens=row.get("output_tokens", ""),
                possibly_truncated="TRUE" if ("length" in fr or "max" in fr) else "")
    return {**base, **res}


def num(x):
    try: return float(x)
    except (TypeError, ValueError): return None


def summarise(rows):
    groups = defaultdict(list)
    for r in rows:
        groups[(r["model"], r["format"], r["condition"])].append(r)
    cols = {"A": ["soundness", "completeness", "leaf_cov_tree", "leaf_cov_join", "blocked_rate"],
            "B": ["accuracy", "recall_entailed", "specificity", "yes_rate", "acc_blocked_conjunction"]}
    for fmt in ("A", "B"):
        sel = {k: v for k, v in groups.items() if k[1] == fmt}
        if not sel: continue
        print(f"\n=== Format {fmt} " + ("(generate everything)" if fmt == "A" else "(label list)") + " ===")
        head = ["model", "condition", "n"] + cols[fmt]
        table = []
        for (m, f, c), rs in sorted(sel.items()):
            line = [m, c, str(len(rs))]
            for col in cols[fmt]:
                vals = [num(r.get(col)) for r in rs if num(r.get(col)) is not None]
                line.append(f"{sum(vals)/len(vals):.2f}" if vals else "-")
            table.append(line)
        w = [max(len(h), *(len(r[i]) for r in table)) for i, h in enumerate(head)]
        print("  ".join(h.ljust(w[i]) for i, h in enumerate(head)))
        for r in table:
            print("  ".join(c.ljust(w[i]) for i, c in enumerate(r)))
    trunc = [r for r in rows if r.get("possibly_truncated")]
    if trunc:
        print(f"\nNOTE: {len(trunc)} response(s) may be truncated (finish_reason length/max). Check before drawing conclusions.")


def selftest(data):
    iid = "J_j6_x6_01" if "J_j6_x6_01" in data.inst else sorted(data.inst)[0]
    inst, items, cat = data.inst[iid], data.items[iid], data.cat[iid]
    ent = inst["entity"]
    gold = [pred_of(it["statement"]) for it in items if it["item_type"] == "derived_fact"]
    blocked = [p for p, (r, _) in cat.items() if r == "blocked_conjunction"]
    mirror = [p for p, (r, _) in cat.items() if r in ("mirror_tree", "mirror_join")]
    drop = {pred_of(it["statement"]) for it in items if it["item_type"] == "derived_fact" and it["top_branch"] in ("3", "4")}
    mk = lambda ps: "\n".join(f"{ent} is a {p}" for p in ps)
    cases = {
        "perfect": mk(gold),
        "reads 'and' as 'or'": mk(gold + blocked),
        "mixes up the entity": mk(gold + mirror),
        "drops branches 3 and 4": mk([p for p in gold if p not in drop]),
        "lists everything it sees": mk(gold + blocked + mirror),
    }
    print(f"SELFTEST on {iid}: {len(gold)} entailed facts, {len(blocked)} blocked-conjunction words, {len(mirror)} mirror words\n")
    hdr = ["pattern", "soundness", "completeness", "leaf_tree", "leaf_join", "blocked", "wrong_ent"]
    print("  ".join(h.ljust(24 if i == 0 else 12) for i, h in enumerate(hdr)))
    for name, txt in cases.items():
        r = score_A(data, iid, txt)
        vals = [name, r["soundness"], r["completeness"], r["leaf_cov_tree"], r["leaf_cov_join"],
                r["err_blocked_conjunction"], r["err_mirror_wrong_entity"]]
        print("  ".join(str(v).ljust(24 if i == 0 else 12) for i, v in enumerate(vals)))
    order = sorted([it for it in items if it["in_label_set"] == "TRUE"], key=lambda r: int(r["label_order"]))
    truth = [(int(it["label_order"]), it["label"], it["item_type"]) for it in order]
    mkb = lambda f: "\n".join(f"{n}: {f(l, t).replace('_', ' ')}" for n, l, t in truth)
    cases_b = {
        "label list: perfect": mkb(lambda l, t: l),
        "label list: says yes to all": mkb(lambda l, t: "ENTAILED"),
        "label list: 'and' as 'or'": mkb(lambda l, t: "ENTAILED" if t == "blocked_conjunction" else l),
    }
    print()
    hdr = ["pattern", "accuracy", "recall_ent", "specificity", "yes_rate", "acc_blocked"]
    print("  ".join(h.ljust(28 if i == 0 else 12) for i, h in enumerate(hdr)))
    for name, txt in cases_b.items():
        r = score_B(data, iid, txt)
        vals = [name, r["accuracy"], r["recall_entailed"], r["specificity"], r["yes_rate"], r["acc_blocked_conjunction"]]
        print("  ".join(str(v).ljust(28 if i == 0 else 12) for i, v in enumerate(vals)))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data-dir", default=HERE)
    ap.add_argument("--responses"); ap.add_argument("--dir"); ap.add_argument("--out", default="scored_responses.csv")
    ap.add_argument("--one", action="store_true"); ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--model", default="model"); ap.add_argument("--instance"); ap.add_argument("--format")
    ap.add_argument("--file")
    a = ap.parse_args()
    data = Data(a.data_dir)
    if a.selftest:
        return selftest(data)
    rows_in = []
    if a.responses:
        rows_in = read_csv(a.responses)
    elif a.dir:
        for fn in sorted(os.listdir(a.dir)):
            if fn.endswith(".txt") and fn.count("__") == 2:
                model, iid, fmt = fn[:-4].split("__")
                rows_in.append(dict(model=model, instance_id=iid, format=fmt,
                                    output=open(os.path.join(a.dir, fn), encoding="utf-8").read()))
    elif a.one:
        rows_in = [dict(model=a.model, instance_id=a.instance, format=a.format,
                        output=open(a.file, encoding="utf-8").read())]
    else:
        ap.error("give --responses, --dir, --one or --selftest")
    scored = [score_one(data, r) for r in rows_in]
    if a.one:
        for k, v in scored[0].items():
            print(f"{k:28s} {v}")
        return
    cols = []
    for r in scored:
        for k in r:
            if k not in cols: cols.append(k)
    with open(a.out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(scored)
    print(f"scored {len(scored)} response(s) -> {a.out}")
    summarise(scored)


if __name__ == "__main__":
    main()
