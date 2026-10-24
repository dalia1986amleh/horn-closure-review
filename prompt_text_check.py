#!/usr/bin/env python3
"""Independent re-derivation of the answer key straight from the English prompt text the models saw.
Does not use the generator, its rule objects or the Z3 encoding: it parses only the sentences
'Every X is a Y.', 'Every X that is also a Y is a Z.' and '<Name> is a X.' with regular expressions."""
import re, json, sys
R1=re.compile(r"^Every (\w+) is a (\w+)\.$"); R2=re.compile(r"^Every (\w+) that is also a (\w+) is a (\w+)\.$"); F=re.compile(r"^([A-Z]\w*) is a (\w+)\.$")
def closure(path):
    one,two,facts=[],[],set()
    for line in open(path,encoding='utf-8'):
        line=line.strip()
        if m:=R2.match(line): two.append(m.groups())
        elif m:=R1.match(line): one.append(m.groups())
        elif m:=F.match(line): facts.add(m.groups())
    given=set(facts); ch=True
    while ch:
        ch=False
        for a,b in one:
            for n,c in list(facts):
                if c==a and (n,b) not in facts: facts.add((n,b)); ch=True
        for a,b,c in two:
            for n in {n for n,_ in facts}:
                if (n,a) in facts and (n,b) in facts and (n,c) not in facts: facts.add((n,c)); ch=True
    return given, facts-given, len(one), len(two)
if __name__=="__main__":
    rec=[json.loads(l) for l in open('release/problems.jsonl')]
    ok=bad=0
    for x in rec:
        if x['pad_tokens_target'] not in (0,40000,80000): continue
        p='prompts_v2/'+x['prompt_file'].split('/')[-1]
        given,derived,n1,n2=closure(p)
        gold={tuple(re.match(r"^(\w+) is a (\w+)\.$",g).groups()) for g in x['gold_closure']}
        tgt=x['target'] if isinstance(x['target'],str) else None
        # the key lists the consequences of the target's start fact; the other individuals (mirror, padding) are excluded
        who=x['start_fact'].split(' is a ')[0]
        derived={d for d in derived if d[0]==who}
        extra=len(derived-gold); miss=len(gold-derived)
        print(x['generator_seed'],x['pad_tokens_target'],'rules',n1,n2,'key',len(gold),'mine',len(derived),'missing_from_mine',miss,'extra_in_mine',extra)
        ok+= (miss==0 and extra==0); bad+=not(miss==0 and extra==0)
    print('exact match',ok,'differ',bad)
