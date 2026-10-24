#!/usr/bin/env python3
"""Build the released problem set: 8 base problems x 5 context conditions (C0..C4).
Writes release/problems.jsonl (one record per problem-condition), release/problems_summary.csv,
release/control_audit.csv. No API calls. Standard library only."""
import csv, json, hashlib, os, re, collections
csv.field_size_limit(10**9)
COND={'C0':('L4',0),'C1':('L4p20',20),'C2':('L4p40',40),'C3':('L4p60',60),'C4':('L4p80',80)}
def sha(x): return hashlib.sha256(x.encode()).hexdigest()[:16]
def pred(s): return s.rsplit(" is a ",1)[1].rstrip(".").strip()

def parse_rules(lines):
    rules=[]
    for ln in lines:
        if not ln.startswith("Every "): continue
        body,head=ln.rstrip(".")[6:].rsplit(" is a ",1)
        ants=tuple(a[2:] if a.startswith("a ") else a for a in (x.strip() for x in body.replace(" that is also a ","|").split("|")))
        rules.append((ants,head.strip()))
    return rules

def provable(start,rules):          # independent method: backward proof search, memoised, cycle guard
    by=collections.defaultdict(list)
    for a,h in rules: by[h].append(a)
    memo,stack={}, set()
    def prove(p):
        if p==start: return True
        if p in memo: return memo[p]
        if p in stack: return False
        stack.add(p); ok=any(all(prove(a) for a in ants) for ants in by.get(p,[])); stack.discard(p); memo[p]=ok; return ok
    return {p for p in by if prove(p)}-{start}

def forward(start,rules):           # generator-style method: forward chaining to fixpoint
    have={start}; ch=True
    while ch:
        ch=False
        for ants,h in rules:
            if h not in have and all(a in have for a in ants): have.add(h); ch=True
    return have-{start}

def structure(start,rules,gold):
    by=collections.defaultdict(list)
    for a,h in rules:
        if h in gold and all(x in gold or x==start for x in a): by[h].append(a)
    unique=all(len(v)==1 for v in by.values())
    depth={start:0}
    def d(p):
        if p in depth: return depth[p]
        depth[p]=1+max(d(a) for a in by[p][0]); return depth[p]
    for p in gold: d(p)
    children=collections.Counter()
    for h,v in by.items():
        for a in v[0]: children[a]+=1
    joins=sum(1 for h,v in by.items() if len(v[0])==2)
    return dict(max_derivation_depth=max(depth.values()), start_branches=children[start], max_out_degree=max(children.values()),
                join_facts_in_closure=joins, chain_facts_in_closure=len(gold)-joins, unique_derivation=unique)

os.makedirs('release',exist_ok=True)
recs=[]; audit=[]
for s in range(1,9):
    base=None
    for c,(lv,pad) in COND.items():
        d=f'seed_{lv}_s{s}'
        inst=list(csv.DictReader(open(f'{d}/formal_logic_dataset_v4_instances.csv',encoding='utf-8')))[0]
        items=list(csv.DictReader(open(f'{d}/formal_logic_dataset_v4_items.csv',encoding='utf-8')))
        gold=sorted(x['statement'] for x in items if x['label']=='ENTAILED')
        prompt=open(f'prompts_v2/PROMPT_SEED_{lv}_s{s}_A.txt',encoding='utf-8').read()
        plines=prompt.split('\n')
        i0=plines.index('Premises:')+1; i1=plines.index('',i0) if '' in plines[i0:] else None
        i1=next(i for i in range(i0,len(plines)) if plines[i]=='')
        prem=plines[i0:i1]; frame=plines[:i0]+plines[i1:]
        assert prem==inst['premises'].split('\n'), (d,'premises differ from prompt')
        start=pred(inst['start_fact']); rules=parse_rules(prem)
        ind=provable(start,rules); fwd=forward(start,rules); key={pred(g) for g in gold}
        st=structure(start,rules,key)
        rule_lines=[l for l in prem if l.startswith('Every ')]; fact_lines=[l for l in prem if not l.startswith('Every ')]
        rec=dict(problem_id=f'P{s}',condition=c,instance_id=f'P{s}-{c}',generator_instance=inst['instance_id'],generator_seed=int(inst['seed']),
                 target=inst['entity'],third_individual_present=pad>0,pad_tokens_target=pad*1000,
                 start_fact=inst['start_fact'],prompt_file=f'prompts/PROMPT_SEED_{lv}_s{s}_A.txt',
                 n_premise_lines=len(prem),n_rules=len(rule_lines),n_fact_lines=len(fact_lines),
                 rules=rule_lines,facts=fact_lines,
                 gold_closure=gold,closure_size=len(gold),
                 structure=dict(generator_depth=int(inst['depth']),generator_fan=int(inst['fan']),generator_joins=int(inst['joins']),**st),
                 verification=dict(method_generator='forward chaining (generator)',method_independent='backward proof search with memoisation (backward_check.py logic, re-implemented here)',
                                   independent_count=len(ind),forward_count=len(fwd),generator_count=len(key),
                                   independent_equals_gold=ind==key,forward_equals_gold=fwd==key,count_matches_instance_file=len(gold)==int(inst['num_entailed_facts']),
                                   unique_derivation=st['unique_derivation'],closure_sha256_16=sha('\n'.join(gold)),premises_sha256_16=sha('\n'.join(prem))),
                 frame_sha256_16=sha('\n'.join(frame)))
        if c=='C0': base=dict(prem=prem,frame=frame,gold=gold,start=inst['start_fact'],rules=set(rule_lines))
        # control audit vs C0
        bset=set(base['prem']); idx=[i for i,l in enumerate(prem) if l in bset]
        kept=[l for l in prem if l in bset]
        pos=[i for i,l in enumerate(prem) if l==base['start']]
        pads=[l for l in prem if l not in bset]
        a=dict(problem_id=f'P{s}',condition=c,frame_identical_to_C0=frame==base['frame'],start_fact_identical=inst['start_fact']==base['start'],
               all_C0_premises_present=bset<=set(prem),C0_order_preserved=kept==base['prem'],gold_identical_to_C0=gold==base['gold'],
               n_padding_lines=len(pads),padding_lines_use_new_predicates=all(pred(l) not in {pred(g) for g in base['gold']} and l.startswith('Every') or not l.startswith('Every') for l in pads) if pads else True,
               start_fact_position=(pos[0]+1 if pos else None),n_premise_lines=len(prem),
               start_fact_relative_position=round(pos[0]/len(prem),3) if pos else None)
        # predicates used by padding that occur in the base problem
        basepreds=set()
        for ants,h in parse_rules(base['prem']): basepreds.update(ants); basepreds.add(h)
        pp=set()
        for ants,h in parse_rules(pads): pp.update(ants); pp.add(h)
        a['padding_shares_predicate_with_base']=bool(pp&basepreds)
        del a['padding_lines_use_new_predicates']
        audit.append(a); recs.append(rec)
# nesting of padding sets across conditions
by=collections.defaultdict(dict)
for r in recs:
    base=next(x for x in recs if x['problem_id']==r['problem_id'] and x['condition']=='C0')
    b=set(base['rules']+base['facts']); by[r['problem_id']][r['condition']]={*r['rules'],*r['facts']}-b
for a in audit:
    P=by[a['problem_id']]; k=int(a['condition'][1])
    a['padding_contains_previous_condition_padding']=True if k<2 else (P[f'C{k-1}']<=P[a['condition']])
with open('release/problems.jsonl','w') as f:
    for r in recs: f.write(json.dumps(r)+'\n')
cols=['instance_id','target','start_fact','condition','pad_tokens_target','n_premise_lines','n_rules','closure_size']
with open('release/problems_summary.csv','w',newline='') as f:
    w=csv.writer(f); w.writerow(cols+['max_derivation_depth','start_branches','join_facts','chain_facts','independent_equals_gold','forward_equals_gold','unique_derivation','closure_sha256_16'])
    for r in recs:
        s=r['structure'];v=r['verification']
        w.writerow([r[c] for c in cols]+[s['max_derivation_depth'],s['start_branches'],s['join_facts_in_closure'],s['chain_facts_in_closure'],v['independent_equals_gold'],v['forward_equals_gold'],v['unique_derivation'],v['closure_sha256_16']])
with open('release/control_audit.csv','w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(audit[0])); w.writeheader(); w.writerows(audit)
print(len(recs),'records')
