#!/usr/bin/env python3
"""
Generator for formal_logic_dataset_v4  (harder than v3).

Fragment: monadic, function-free definite Horn logic, one target entity.
  fact  : "<Entity> is a <P>."
  rule  : "Every <P> is a <Q>."                        (P(x) -> Q(x))
  rule  : "Every <P> that is also a <Q> is a <R>."     (P(x) & Q(x) -> R(x))   [conjunctive body]
All concept names are invented 8-letter words.

What is harder than v3
  * size: depth up to 24, up to 16 branches (384 gold facts)
  * conjunctive rules: a JOIN needs facts from two different branches before it fires
  * BLOCKED conjunctions: look identical to joins, but one conjunct is never derivable for the
    target entity (it belongs to the mirror entity), so the conclusion is NOT entailed
  * forks at several levels (shared prefixes), not only at the root
  * everything in the target structure has an identical-looking MIRROR for another entity
    (same shape, own joins, own blocked conjunctions), so copying consequents gives ~0.5 precision

Run:  python3 generate_dataset_v4.py [output_dir]
"""
import csv, os, random, sys
from collections import Counter, defaultdict

BASE_SEED = 20261009
OUT_DIR = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__))

ENTITIES = ["Sally", "Rex", "Mara", "Tobin", "Ines", "Orla", "Dev", "Nell"]
CONS = list("bdfgjklmnprstvzxw")
VOW = "aeiou"
CLUSTERS = ["rk", "lt", "nz", "vk", "zm", "gn", "dr", "kr", "tl", "lv", "nk",
            "rd", "sk", "zl", "mb", "rz", "xt", "jn"]
RARE = set("zxjvwk")
MIN_HAM = 3                      # names (all 8 letters) differ in >= 3 positions


def grid():
    # (experiment, condition, depth, fan, n_joins, n_blocked_pairs, n_instances)
    cells = []
    for d in (8, 16, 24):
        for b in (4, 8, 16):
            cells.append(("scale", f"A_d{d}_b{b}", d, [b], 0, 0, 12))
    for j in (0, 3, 6):
        for x in (0, 3, 6):
            cells.append(("join", f"J_j{j}_x{x}", 8, [6], j, x, 15))
    for tag, fan in (("root8", [8]), ("fork4x2", [4, 2]), ("fork2x2x2", [2, 2, 2])):
        cells.append(("fork", f"F_{tag}", 8, fan, 0, 0, 15))
    return cells


# ---------------------------------------------------------------- names
class NameFactory:
    def __init__(self, rng):
        self.rng, self.used, self.seen = rng, [], set()

    def new(self):
        r = self.rng
        for _ in range(200000):
            w = (r.choice(CONS) + r.choice(VOW) + r.choice(CLUSTERS) + r.choice(VOW)
                 + r.choice(CONS) + r.choice(VOW) + r.choice(CONS))
            if w in self.seen or not (set(w) & RARE):
                continue
            ok = True
            for u in self.used:
                d = 0
                for x, y in zip(w, u):
                    if x != y:
                        d += 1
                if d < MIN_HAM:
                    ok = False
                    break
            if ok:
                self.used.append(w); self.seen.add(w)
                return w
        raise RuntimeError("name space exhausted")


# ---------------------------------------------------------------- logic helpers
# rule = ("s", a, b)  or  ("c", a1, a2, b)
def closure_pred(start, rules):
    S, changed = set(start), True
    while changed:
        changed = False
        for r in rules:
            if r[0] == "s":
                if r[1] in S and r[2] not in S:
                    S.add(r[2]); changed = True
            else:
                if r[1] in S and r[2] in S and r[3] not in S:
                    S.add(r[3]); changed = True
    return S


def has_cycle(rules):
    adj = defaultdict(set)
    for r in rules:
        for a in r[1:-1]:
            adj[a].add(r[-1])
    color = {}

    def dfs(u):
        color[u] = 1
        for v in adj[u]:
            if color.get(v) == 1 or (v not in color and dfs(v)):
                return True
        color[u] = 2
        return False
    return any(u not in color and dfs(u) for u in list(adj))


def rule_text(r):
    if r[0] == "s":
        return f"Every {r[1]} is a {r[2]}."
    return f"Every {r[1]} that is also a {r[2]} is a {r[3]}."


def parse_rule(line):
    if " that is also a " in line:
        a1, rest = line[len("Every "):].split(" that is also a ")
        a2, b = rest[:-1].split(" is a ")
        return ("c", a1, a2, b)
    a, b = line[len("Every "):-1].split(" is a ")
    return ("s", a, b)


# ---------------------------------------------------------------- abstract structure
def make_abstract(rng, depth, fan, n_join):
    nodes = [dict(parent=-1, level=0, top=-1)]
    frontier = [0]
    for l in range(1, depth + 1):
        k = fan[l - 1] if l <= len(fan) else 1
        new = []
        for p in frontier:
            for _ in range(k):
                top = len(new) if l == 1 else nodes[p]["top"]
                nodes.append(dict(parent=p, level=l, top=top))
                new.append(len(nodes) - 1)
        frontier = new
    joins, cand = [], [i for i, n in enumerate(nodes) if 2 <= n["level"] <= depth - 1]
    tries = 0
    while len(joins) < n_join and tries < 5000:
        tries += 1
        x, y = rng.sample(cand, 2)
        if nodes[x]["top"] == nodes[y]["top"]:
            continue
        if any({x, y} == {a, b} for a, b, _ in joins):
            continue
        joins.append((x, y, rng.choice([1, 2])))
    assert len(joins) == n_join, "could not place joins"
    return dict(nodes=nodes, joins=joins, depth=depth)


def instantiate(ab, nf):
    names = [nf.new() for _ in ab["nodes"]]
    rules = [("s", names[n["parent"]], names[i]) for i, n in enumerate(ab["nodes"]) if n["parent"] >= 0]
    join_nodes = []
    for x, y, t in ab["joins"]:
        J = [nf.new() for _ in range(t + 1)]
        rules.append(("c", names[x], names[y], J[0]))
        rules += [("s", a, b) for a, b in zip(J, J[1:])]
        join_nodes.append(J)
    return dict(names=names, rules=rules, joins=join_nodes)


# ---------------------------------------------------------------- one instance
def build_instance(rng, depth, fan, n_join, n_block):
    entity = rng.choice(ENTITIES)
    other = rng.choice([e for e in ENTITIES if e != entity])
    nf = NameFactory(rng)
    ab = make_abstract(rng, depth, fan, n_join)
    real, mirror = instantiate(ab, nf), instantiate(ab, nf)
    rules = list(real["rules"]) + list(mirror["rules"])
    n_struct_rules = len(rules)
    S, M0 = real["names"][0], mirror["names"][0]
    cand = [i for i, n in enumerate(ab["nodes"]) if n["level"] >= 2]

    # blocked conjunctions: one conjunct belongs to the other entity -> never fires for either entity
    blocked_nodes = []
    for _ in range(n_block):
        for A, B in ((real["names"], mirror["names"]), (mirror["names"], real["names"])):
            x, y = A[rng.choice(cand)], B[rng.choice(cand)]
            Z = [nf.new() for _ in range(rng.choice([1, 2]) + 1)]
            rules.append(("c", x, y, Z[0]))
            rules += [("s", a, b) for a, b in zip(Z, Z[1:])]
            blocked_nodes += Z
    # near-miss decoys feeding INTO a chain (affirming-the-consequent trap), one per side
    decoy_real, decoy_mirror, decoy_all = [], [], []
    for names, store, role in ((real["names"], decoy_real, "decoy_target_side"),
                               (mirror["names"], decoy_mirror, "decoy_mirror_side")):
        z1, z2 = nf.new(), nf.new()
        rules += [("s", z1, z2), ("s", z2, names[rng.choice(cand)])]
        store += [z2]; decoy_all += [(z1, role), (z2, role)]
    never = [nf.new() for _ in range(4)]

    lines = [f"{entity} is a {S}.", f"{other} is a {M0}."] + [rule_text(r) for r in rules]
    rng.shuffle(lines)

    # ---- gold: entailed facts about `entity`
    nodes, names = ab["nodes"], real["names"]
    derived = []                                             # (predicate, top_branch, depth, is_leaf)
    for i in range(1, len(nodes)):
        derived.append((names[i], nodes[i]["top"] + 1, nodes[i]["level"], nodes[i]["level"] == depth))
    for (x, y, t), J in zip(ab["joins"], real["joins"]):
        d0 = max(nodes[x]["level"], nodes[y]["level"]) + 1
        for k, p in enumerate(J):
            derived.append((p, "join", d0 + k, k == len(J) - 1))

    # ---- rule-statement pools (single-antecedent paths in the real tree)
    parent = {i: n["parent"] for i, n in enumerate(nodes)}

    def ancestors(i):
        out, p = [], parent[i]
        while p >= 0:
            out.append(p); p = parent[p]
        return out                                           # nearest first, ends with root 0
    deep = [i for i, n in enumerate(nodes) if n["level"] >= 2]
    trans, rev_skip = [], []
    for i in rng.sample(deep, min(30, len(deep))):
        anc = ancestors(i)[1:]                               # skip the direct parent -> >= 2 hops
        if anc:
            a = rng.choice(anc)
            trans.append((f"Every {names[a]} is a {names[i]}.", nodes[i]["top"] + 1, nodes[i]["level"] - nodes[a]["level"]))
            rev_skip.append(f"Every {names[i]} is a {names[a]}.")
    rev = [f"Every {names[i]} is a {names[nodes[i]['parent']]}." for i in range(1, len(nodes))]
    allnames = [n for n in real["names"][1:]] + [n for n in mirror["names"][1:]]
    tops = [nd["top"] for nd in nodes[1:]] * 2
    cross = []
    for _ in range(40):
        i, j = rng.sample(range(len(allnames)), 2)
        if tops[i] != tops[j] or (i < len(nodes) - 1) != (j < len(nodes) - 1):
            cross.append(f"Every {allnames[i]} is a {allnames[j]}.")
    mirror_rhs = mirror["names"][1:] + [p for J in mirror["joins"] for p in J] + decoy_mirror

    fact_pools = {
        "unreachable_predicate": [f"{entity} is a {p}." for p in mirror_rhs],
        "affirming_consequent": [f"{entity} is a {p}." for p in decoy_real],
        "blocked_conjunction": [f"{entity} is a {p}." for p in blocked_nodes],
    }
    rule_pools = {"reversed_rule": rev, "reversed_skip_rule": rev_skip, "cross_chain_rule": cross}
    for pool in list(fact_pools.values()) + list(rule_pools.values()):
        rng.shuffle(pool)

    # ---- label list: entailed ~ non-entailed, matched by statement form
    leaves = [d for d in derived if d[3]]
    jleaves = [d for d in leaves if d[1] == "join"]
    tleaves = [d for d in leaves if d[1] != "join"]
    rng.shuffle(jleaves); rng.shuffle(tleaves)
    chosen = jleaves[:3] + tleaves[:max(0, 10 - len(jleaves[:3]))]
    others = [d for d in derived if not d[3]]
    rng.shuffle(others)
    sel_ent_f = [("derived_fact", f"{entity} is a {p}.", br, dp) for p, br, dp, _ in chosen + others[:2]]
    rng.shuffle(trans)
    sel_ent_r = [("transitive_rule", s, br, dp) for s, br, dp in trans[:2]]

    def draw(pools, n):
        out = []
        while len(out) < n and any(pools.values()):
            keys = list(pools); rng.shuffle(keys)
            for k in keys:
                if pools[k] and len(out) < n:
                    out.append((k, pools[k].pop(), None, None))
        return out
    non_f = draw(fact_pools, len(sel_ent_f))
    for nn in never:
        if len(non_f) < len(sel_ent_f):
            non_f.append(("never_mentioned", f"{entity} is a {nn}.", None, None))
    sel_non = non_f + draw(rule_pools, len(sel_ent_r))

    catalog = [(S, "target_start", "FALSE")]
    catalog += [(p, "target_tree", "TRUE") for p in real["names"][1:]]
    catalog += [(p, "target_join", "TRUE") for J in real["joins"] for p in J]
    catalog += [(M0, "mirror_start", "FALSE")]
    catalog += [(p, "mirror_tree", "FALSE") for p in mirror["names"][1:]]
    catalog += [(p, "mirror_join", "FALSE") for J in mirror["joins"] for p in J]
    catalog += [(p, "blocked_conjunction", "FALSE") for p in blocked_nodes]
    catalog += [(p, role, "FALSE") for p, role in decoy_all]
    return dict(entity=entity, other=other, S=S, lines=lines, derived=derived, leaves=len(leaves), catalog=catalog,
                n_extra=len(rules) - n_struct_rules,
                sel_ent=sel_ent_f + sel_ent_r, sel_non=sel_non)


# ---------------------------------------------------------------- verification
def verify(row, items):
    facts, rules = [], []
    for ln in row["premises"].split("\n"):
        if ln.startswith("Every "):
            rules.append(parse_rule(ln))
        else:
            e, p = ln[:-1].split(" is a "); facts.append((e, p))
    assert not has_cycle(rules), "cycle"
    ent, oth = row["entity"], row["other_entity"]
    start = [p for e, p in facts if e == ent]
    ostart = [p for e, p in facts if e == oth]
    assert len(start) == 1 and len(ostart) == 1
    cl = closure_pred(start, rules)
    ocl = closure_pred(ostart, rules)
    gold = {it["statement"] for it in items if it["item_type"] == "derived_fact"}
    assert gold == {f"{ent} is a {p}." for p in cl if p != start[0]}, "gold != closure"
    assert len(ocl) == len(cl), "mirror is not symmetric"
    assert not (cl - {start[0]}) & (ocl - {ostart[0]}), "entities share derived predicates"
    for it in items:
        s = it["statement"]
        if s.startswith("Every "):
            a, b = s[len("Every "):-1].split(" is a ")
            truth = b != a and b in closure_pred({a}, rules)
        else:
            e, p = s[:-1].split(" is a ")
            assert e == ent
            truth = p in cl and p != start[0]
        assert truth == (it["label"] == "ENTAILED"), f"label wrong: {s} ({it['item_type']})"
    return True


# ---------------------------------------------------------------- main
def main():
    inst_rows, item_rows, cat_rows, idx = [], [], [], 0
    for exp, cond, depth, fan, n_join, n_block, n_inst in grid():
        for k in range(1, n_inst + 1):
            idx += 1
            seed = BASE_SEED + idx
            rng = random.Random(seed)
            m = build_instance(rng, depth, fan, n_join, n_block)
            iid = f"{cond}_{k:02d}"
            label_items = [(t, s, "ENTAILED", br, dp) for t, s, br, dp in m["sel_ent"]] + \
                          [(t, s, "NOT_ENTAILED", br, dp) for t, s, br, dp in m["sel_non"]]
            rng.shuffle(label_items)
            items, n, seen = [], 0, set()
            leaf_of = {f"{m['entity']} is a {p}.": lf for p, br, dp, lf in m["derived"]}
            for pos, (t, s, lab, br, dp) in enumerate(label_items, 1):
                n += 1
                items.append(dict(instance_id=iid, item_id=f"{iid}_I{n:03d}", statement=s, label=lab,
                                  item_type=t, top_branch=br if br is not None else "",
                                  depth=dp if dp is not None else "",
                                  is_leaf=("TRUE" if leaf_of.get(s) else "FALSE") if t == "derived_fact" else "",
                                  in_label_set="TRUE", label_order=pos))
                seen.add(s)
            for p, br, dp, lf in m["derived"]:
                s = f"{m['entity']} is a {p}."
                if s in seen:
                    continue
                n += 1
                items.append(dict(instance_id=iid, item_id=f"{iid}_I{n:03d}", statement=s, label="ENTAILED",
                                  item_type="derived_fact", top_branch=br, depth=dp,
                                  is_leaf="TRUE" if lf else "FALSE", in_label_set="FALSE", label_order=""))
            premises = "\n".join(m["lines"])
            row = dict(
                instance_id=iid, experiment=exp, condition=cond, seed=seed, entity=m["entity"],
                other_entity=m["other"], depth=depth, fan="-".join(map(str, fan)),
                leaves=m["leaves"], joins=n_join, blocked_pairs=n_block, extra_rules=m["n_extra"],
                n_premise_lines=len(m["lines"]), premise_chars=len(premises), premises=premises,
                start_fact=f"{m['entity']} is a {m['S']}.",
                num_entailed_facts=len(m["derived"]), n_label_items=len(label_items),
                n_label_entailed=sum(1 for x in label_items if x[2] == "ENTAILED"),
                n_label_non_entailed=sum(1 for x in label_items if x[2] == "NOT_ENTAILED"))
            verify(row, items)
            inst_rows.append(row); item_rows.extend(items)
            cat_rows += [dict(instance_id=iid, predicate=p, role=role, entailed_for_target=e) for p, role, e in m["catalog"]]

    os.makedirs(OUT_DIR, exist_ok=True)
    with open(os.path.join(OUT_DIR, "formal_logic_dataset_v4_instances.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(inst_rows[0])); w.writeheader(); w.writerows(inst_rows)
    with open(os.path.join(OUT_DIR, "formal_logic_dataset_v4_items.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(item_rows[0])); w.writeheader(); w.writerows(item_rows)
    with open(os.path.join(OUT_DIR, "formal_logic_dataset_v4_predicates.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(cat_rows[0])); w.writeheader(); w.writerows(cat_rows)
    print("instances:", len(inst_rows), "| items:", len(item_rows), "| predicates:", len(cat_rows))
    print("by experiment:", dict(Counter(r["experiment"] for r in inst_rows)))
    print("all instances verified from premise text (incl. mirror symmetry): OK")
    print("label-set balance:", dict(Counter(r["label"] for r in item_rows if r["in_label_set"] == "TRUE")))
    print("non-entailed types:", dict(Counter(r["item_type"] for r in item_rows if r["label"] == "NOT_ENTAILED")))


if __name__ == "__main__":
    main()
