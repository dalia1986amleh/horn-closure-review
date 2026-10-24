#!/usr/bin/env python3
"""Makes human_audit_sheet.md: 10 randomly chosen entailed facts with full derivations and 4 non-entailed join conclusions from the unpadded problems (random.seed(2026)). Run from the package root."""
import json,re,random
random.seed(2026)
P=[json.loads(l) for l in open('release/problems.jsonl')]
P=[p for p in P if p['condition']=='C0']
def ev(x): return x if isinstance(x,list) else eval(x)
out=[];n=0
chain_re=re.compile(r'^Every (\w+) is an? (\w+)\.$');join_re=re.compile(r'^Every (\w+) that is also an? (\w+) is an? (\w+)\.$')
items=[]
for p in P:
    rules=ev(p['rules']);facts=ev(p['facts']);tgt=p['target']
    start=re.match(r'.* is an? (\w+)\.',p['start_fact']).group(1)
    ch=[];jn=[]
    for r in rules:
        m=join_re.match(r)
        if m: jn.append(m.groups())
        else:
            m=chain_re.match(r)
            if m: ch.append(m.groups())
    have={start:None}
    changed=True
    while changed:
        changed=False
        for a,b in ch:
            if a in have and b not in have: have[b]=('chain',a,r:=f"Every {a} is a {b}.");changed=True
        for a,b,c in jn:
            if a in have and b in have and c not in have: have[c]=('join',(a,b),f"Every {a} that is also a {b} is a {c}.");changed=True
    gold=set(re.match(r'.* is an? (\w+)\.',g).group(1) for g in ev(p['gold_closure']))
    assert gold==set(have)-{start},(p['problem_id'],len(gold),len(have))
    def path(x):
        if have[x] is None: return []
        k,a,r=have[x]
        ants=[a] if k=='chain' else list(a)
        s=[]
        for y in ants: s+=path(y)
        return s+[(x,r)]
    for x in have:
        if have[x] is not None: items.append((p['problem_id'],tgt,start,x,have[x][0],path(x)))
    # decoys: join where exactly one antecedent derived
    dec=[(a,b,c) for a,b,c in jn if c not in have and ((a in have)!=(b in have))]
    p['_dec']=(tgt,start,dec,have)
sel=[]
random.shuffle(items)
chains=[i for i in items if i[4]=='chain' and len(i[5])>=3][:6];joins=[i for i in items if i[4]=='join' and len(i[5])>=3][:4]
L=["# Human audit sheet: rules and answer keys\n","Please read each item and tick one box. About 20 minutes. All rules are in English; the words are invented, so only the logic matters.\n",
"The two rule forms mean:\n\n- *Every A is a B*: anything that is an A is also a B.\n- *Every A that is also a B is a C*: anything that is both an A and a B is also a C.\n"]
L.append("## Part 1. Is the fact entailed?\n\nThe key says the last line of each derivation is entailed. Check that every step follows from the line before and the rules shown.\n")
for k,i in enumerate(chains+joins,1):
    pid,t,s,x,kind,pth=i
    L.append(f"**Item {k}** (problem {pid}). Start: *{t} is a {s}.*\n")
    for y,r in pth: L.append(f"- {r}  → {t} is a {y}.")
    L.append(f"\nKey says: **{t} is a {x}** is entailed.   ☐ correct   ☐ wrong   ☐ unclear\n")
L.append("## Part 2. Is the fact NOT entailed?\n\nIn each item a join rule has only one of its two conditions true for the target. The key says the conclusion is not entailed.\n")
ds=[]
for p in P:
    t,s,dec,have=p['_dec']
    for a,b,c in dec:
        ds.append((p['problem_id'],t,s,a,b,c,have)); 
random.shuffle(ds)
for k,(pid,t,s,a,b,c,have) in enumerate(ds[:4],1):
    true,false=(a,b) if a in have else (b,a)
    L.append(f"**Item {k+10}** (problem {pid}). Rule: *Every {a} that is also a {b} is a {c}.* The target {t} is a {true} (derived), but nothing makes {t} a {false}.\n\nKey says: **{t} is a {c}** is NOT entailed.   ☐ correct   ☐ wrong   ☐ unclear\n")
L.append("## Result\n\nItems correct: ____ / 14.   Anything wrong or unclear (item numbers and why): ______________________\n")
open('human_audit_sheet.md','w').write('\n'.join(L))
print(len(chains),len(joins),len(ds))
