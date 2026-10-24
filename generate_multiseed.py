#!/usr/bin/env python3
"""
Multi-seed ladder instances (Experiment 7).  Same fragment, prompt and checks as generate_ladder.py, but many seeds and optional context padding.

  python3 generate_multiseed.py                 -> L3 and L4 x 8 seeds, L5 x 4 seeds, plus padded L3 and L4 (20k and 60k tokens) x 3 seeds
  python3 generate_multiseed.py L4 1-8          -> one level tag and a seed range, e.g. L4, L4p20, L4p60

Level tags:  L3 | L4 | L5            plain ladder instance (seed n -> seed 31000 + 100*level + n)
             L3p20, L4p60 ...        the SAME instance (same seed) plus irrelevant padding up to about 20k / 60k prompt tokens
Writes seed_<tag>_s<n>/ (v4 CSVs) and prompts_v2/PROMPT_SEED_<tag>_s<n>_A.txt ; instance id SEED<tag>s<n>.

Padding = extra rules and facts about a THIRD individual, built from fresh invented words, spliced into the premise list at random
positions (the original lines keep their relative order).  Nothing in it is reachable from the target's or the mirror individual's start
fact; the script recomputes the closure of the full premise set and stops if the answer key changes.
"""
import csv, os, random, re, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import generate_ladder as GL
from generate_dataset_v4 import NameFactory, closure_pred, rule_text, parse_rule, ENTITIES

TOK_PER_LINE = 12.4      # calibrated on API-reported input tokens of the nesting prompts: 5,985 tokens for 470 premise lines (incl. header and task)
OVERHEAD = 150
PLAN = [("L3", range(1, 9)), ("L4", range(1, 9)), ("L5", range(1, 5)),
        ("L3p20", range(1, 4)), ("L3p60", range(1, 4)), ("L4p20", range(1, 4)), ("L4p60", range(1, 4))]


def parse_tag(tag):
    m = re.fullmatch(r"(L\d)(?:p(\d+))?", tag)
    assert m, tag
    return m[1], (int(m[2]) * 1000 if m[2] else 0)


def make_padding(rng, words, entity, other, n_lines):
    """Return (fact lines, rule lines) about a third individual; about n_lines in total."""
    nf = NameFactory(rng)
    nf.used = [w for w in words if len(w) == 8]; nf.seen = set(words)
    third = rng.choice([e for e in ENTITIES if e not in (entity, other)])
    facts, rules, made = [], [], 0
    while made < n_lines:
        chains = []
        for _ in range(3):                                   # three chains of 8 per group
            ch = [nf.new() for _ in range(8)]
            facts.append(f"{third} is a {ch[0]}.") if rng.random() < 0.5 else None
            rules += [("s", a, b) for a, b in zip(ch, ch[1:])]; chains.append(ch)
        for _ in range(4):                                   # four joins per group, each with a 2-step tail
            c1, c2 = rng.sample(chains, 2); t = [nf.new() for _ in range(3)]
            rules.append(("c", rng.choice(c1[2:]), rng.choice(c2[2:]), t[0])); rules += [("s", a, b) for a, b in zip(t, t[1:])]
        made = len(facts) + len(rules)
    return facts, [rule_text(r) for r in rules]


def build(tag, sidx):
    lvl, pad_tokens = parse_tag(tag)
    seed = 31000 + 100 * int(lvl[1]) + sidx
    m = GL.build(lvl, seed); lines = list(m["lines"])
    if pad_tokens:
        words = set(re.findall(r"[a-z]{6,}", " ".join(lines).lower()))
        base_tokens = len(lines) * TOK_PER_LINE + OVERHEAD
        n_pad = int((pad_tokens - base_tokens) / TOK_PER_LINE)
        assert n_pad > 0, "target smaller than the base prompt"
        rng = random.Random(seed + 4242)
        facts, rules = make_padding(rng, words, m["entity"], m["other"], n_pad)
        extra = facts + rules; rng.shuffle(extra)
        slots = sorted(rng.randrange(len(lines) + 1) for _ in extra)          # insert at random positions, base order untouched
        out, j = [], 0
        for i, ln in enumerate(lines + [None]):
            while j < len(extra) and slots[j] == i: out.append(extra[j]); j += 1
            if ln is not None: out.append(ln)
        lines = out
    # verification: the answer key is unchanged by padding
    rules = [parse_rule(l) for l in lines if l.startswith("Every")]
    M0 = [p for p, role, _ in m["catalog"] if role == "mirror_start"][0]
    cl = closure_pred({m["S"]}, rules) - {m["S"]}; clm = closure_pred({M0}, rules) - {M0}
    assert cl == set(m["gold"]), "answer key changed"
    assert len(clm) == len(cl) and not (cl & clm), "mirror closure changed"
    m["lines"], m["seed"], m["pad_tokens"] = lines, seed, pad_tokens
    return m


def write(tag, sidx):
    m = build(tag, sidx); IID = f"SEED{tag}s{sidx}"; pdir = f"seed_{tag}_s{sidx}"
    prem = "\n".join(m["lines"]); os.makedirs(os.path.join(HERE, pdir), exist_ok=True); os.makedirs(os.path.join(HERE, "prompts_v2"), exist_ok=True)
    inst = dict(instance_id=IID, experiment=pdir, condition=tag, seed=m["seed"], entity=m["entity"], other_entity=m["other"], depth=m["depth"],
                fan=str(m["nb"]), leaves=m["nb"], joins=m["n_joins"], blocked_pairs=m["n_blocked"], extra_rules=f"pad_tokens={m['pad_tokens']}", n_premise_lines=len(m["lines"]),
                premise_chars=len(prem), premises=prem, start_fact=f"{m['entity']} is a {m['S']}.", num_entailed_facts=len(m["gold"]),
                n_label_items=0, n_label_entailed=0, n_label_non_entailed=0)
    w = lambda n: open(os.path.join(HERE, pdir, f"formal_logic_dataset_v4_{n}.csv"), "w", newline="")
    with w("instances") as f: x = csv.DictWriter(f, fieldnames=list(inst)); x.writeheader(); x.writerow(inst)
    items = [dict(instance_id=IID, item_id=f"{IID}_I{n:03d}", statement=f"{m['entity']} is a {p}.", label="ENTAILED", item_type="derived_fact",
                  top_branch=br, depth=dp, is_leaf="TRUE" if lf else "FALSE", in_label_set="FALSE", label_order="") for n, (p, (br, dp, lf)) in enumerate(sorted(m["gold"].items()), 1)]
    with w("items") as f: x = csv.DictWriter(f, fieldnames=list(items[0])); x.writeheader(); x.writerows(items)
    with w("predicates") as f:
        x = csv.DictWriter(f, fieldnames=["instance_id", "predicate", "role", "entailed_for_target"]); x.writeheader()
        for p, role, e in m["catalog"]: x.writerow(dict(instance_id=IID, predicate=p, role=role, entailed_for_target="TRUE" if e else "FALSE"))
    header = ('Use only the premises below. All words are invented; do not use outside knowledge.\n'
              'Do NOT use code, tools, calculators or web search. Work it out yourself.\n'
              '"Every A is a B" means anything that is an A is also a B.\n'
              '"Every A that is also a B is a C" applies only to something that is both an A and a B.\n')
    task = (f'\nTask: list every statement of the form "{m["entity"]} is a ___" that follows from the premises.\n'
            f'- Do not repeat the given fact about {m["entity"]}.\n'
            f'- Write one statement per line, exactly as "{m["entity"]} is a word". No numbering, no explanations.\n'
            '- Include every statement that follows and no statement that does not follow.\n')
    text = header + "\nPremises:\n" + prem + "\n" + task
    open(os.path.join(HERE, "prompts_v2", f"PROMPT_SEED_{tag}_s{sidx}_A.txt"), "w").write(text)
    print(f"{tag:6s} s{sidx}: {IID:14s} | premise lines={len(m['lines']):5d} | est. prompt tokens={int(len(m['lines'])*TOK_PER_LINE+OVERHEAD):6d} | answer key={len(m['gold'])} | verified")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        a, b = (sys.argv[2].split("-") + [sys.argv[2]])[:2] if len(sys.argv) > 2 else ("1", "8")
        for i in range(int(a), int(b) + 1): write(sys.argv[1], i)
    else:
        for tag, rg in PLAN:
            for i in rg: write(tag, i)
