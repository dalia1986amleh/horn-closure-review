#!/usr/bin/env python3
"""
Build copy-paste prompts from formal_logic_dataset_v4.

  python3 build_prompts.py --hard-pack                       # the three hardest instances -> prompts/
  python3 build_prompts.py --instances J_j6_x6_01 --format A # any instance, format A or B or both
"""
import argparse, csv, os

HERE = os.path.dirname(os.path.abspath(__file__))

HEADER = """Use only the premises below. All words are invented; do not use outside knowledge.
Do NOT use code, tools, calculators or web search. Work it out yourself.
"Every A is a B" means anything that is an A is also a B.
"Every A that is also a B is a C" applies only to something that is both an A and a B.

Premises:
{premises}
"""

TASK_A = """
Task: list every statement of the form "{entity} is a ___" that follows from the premises.
- Do not repeat the given fact about {entity}.
- Write one statement per line, exactly as "{entity} is a word". No numbering, no explanations.
- Include every statement that follows and no statement that does not follow.
"""

TASK_B = """
Task: label each statement below ENTAILED or NOT ENTAILED (does it follow from the premises?).
Answer only as one line per statement, in the form "1: ENTAILED" or "2: NOT ENTAILED".

Statements:
{statements}
"""


def read_csv(name):
    with open(os.path.join(HERE, name), newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def build(inst, items, fmt):
    body = HEADER.format(premises=inst["premises"])
    if fmt == "A":
        return body + TASK_A.format(entity=inst["entity"])
    lab = sorted([i for i in items if i["in_label_set"] == "TRUE"], key=lambda r: int(r["label_order"]))
    stm = "\n".join(f"{i['label_order']}. {i['statement']}" for i in lab)
    return body + TASK_B.format(statements=stm)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--instances", default="")
    ap.add_argument("--format", default="A", choices=["A", "B", "both"])
    ap.add_argument("--hard-pack", action="store_true")
    ap.add_argument("--out", default=os.path.join(HERE, "prompts_v2"))
    a = ap.parse_args()
    inst = {r["instance_id"]: r for r in read_csv("formal_logic_dataset_v4_instances.csv")}
    items = {}
    for r in read_csv("formal_logic_dataset_v4_items.csv"):
        items.setdefault(r["instance_id"], []).append(r)
    jobs = []
    if a.hard_pack:
        jobs = [("J_j6_x6_01", "A"), ("J_j6_x6_01", "B"), ("F_fork2x2x2_01", "A"), ("A_d24_b16_01", "A")]
    else:
        for iid in filter(None, a.instances.split(",")):
            for f in (["A", "B"] if a.format == "both" else [a.format]):
                jobs.append((iid.strip(), f))
    os.makedirs(a.out, exist_ok=True)
    for iid, f in jobs:
        text = build(inst[iid], items[iid], f)
        path = os.path.join(a.out, f"PROMPT_{iid}_{f}.txt")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)
        gold = int(inst[iid]["num_entailed_facts"]) if f == "A" else int(inst[iid]["n_label_items"])
        print(f"{path}  | lines in prompt: {text.count(chr(10))} | answer size: {gold}")


if __name__ == "__main__":
    main()
