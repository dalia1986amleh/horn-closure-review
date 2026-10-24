#!/usr/bin/env python3
"""Mechanical spot check of human_audit_sheet.md against release/problems.jsonl: every rule in a derivation appears word for word in the premises,
every step follows from the steps before it, and the non-entailed join conclusions are absent from the key. Prints 'x of 14 items correct'."""
import re, json
P = {}
for l in open('release/problems.jsonl'):
    j = json.loads(l)
    if j['condition'] == 'C0': P[j['problem_id']] = j
ev = lambda x: x if isinstance(x, list) else eval(x)
txt = open('human_audit_sheet.md').read(); ok = 0; n_items = 0
for blk in re.split(r'\n\*\*Item ', txt)[1:]:
    m = re.match(r'(\d+)\*\* \(problem (P\d)\)', blk); n, pid = int(m.group(1)), m.group(2)
    p = P[pid]; rules = set(ev(p['rules']))
    if n <= 10:
        have = {re.search(r'Start: \*\w+ is an? (\w+)\.\*', blk).group(1)}; good = True
        for r, y in re.findall(r'^- (Every .*?\.)  → \w+ is an? (\w+)\.', blk, re.M):
            if r not in rules: good = False; break
            j = re.match(r'Every (\w+) that is also an? (\w+) is an? (\w+)\.', r)
            if j: a, b, c = j.groups(); good &= (a in have and b in have and c == y)
            else: a, c = re.match(r'Every (\w+) is an? (\w+)\.', r).groups(); good &= (a in have and c == y)
            have.add(y)
        good &= re.search(r'\*\*\w+ is an? (\w+)\*\* is entailed', blk).group(1) in have
    else:
        r = re.search(r'Rule: \*(Every .*?\.)\*', blk).group(1); good = r in rules
        a, b, c = re.match(r'Every (\w+) that is also an? (\w+) is an? (\w+)\.', r).groups()
        gold = {re.match(r'.* is an? (\w+)\.', g).group(1) for g in ev(p['gold_closure'])}
        good &= (c not in gold) and ((a in gold) != (b in gold))
    ok += good; n_items += 1
print(f"{ok} of {n_items} items correct")
