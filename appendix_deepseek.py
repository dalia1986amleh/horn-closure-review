#!/usr/bin/env python3
"""Appendix A (DeepSeek-V4-Pro, 9k/20k/40k/60k/80k): one run per cell (cell_pick.py), from seeds_results_normalised.csv."""
import csv, json, statistics as st
from math import comb
from cell_pick import pick
from scipy import stats
LV={'L4':'9k','L4p20':'20k','L4p40':'40k','L4p60':'60k','L4p80':'80k'}
runs={}
for r in csv.DictReader(open('seeds_results_normalised.csv')):
    if r['model']=='deepseek' and r['level'] in LV and r['completeness']: runs.setdefault((r['level'],int(r['seed'])),[]).append(r)
F=['completeness','soundness','wrong','chain_recall','join_recall']
cell={}
for (l,s),rs in runs.items():
    ch=pick('deepseek',l,s,[x['run'] for x in rs]); x=[y for y in rs if y['run']==ch][0]
    cell[(LV[l],s)]={f:(float(x[f]) if x[f]!='' else None) for f in F}; cell[(LV[l],s)]['run']=ch
lv=['9k','20k','40k','60k','80k']
T=lambda n: stats.t.ppf(.975,n-1)
def ci(v): m=st.mean(v); h=T(len(v))*st.stdev(v)/len(v)**.5; return m,m-h,m+h
out={}
for f in ['completeness','soundness','chain_recall','join_recall']:
    for l in lv:
        v=[cell[(l,s)][f] for s in range(1,9) if cell[(l,s)][f] is not None]
        m,lo,hi=ci(v); out[f"{f}|{l}"]=dict(mean=m,lo=lo,hi=hi,sd=st.stdev(v),min=min(v),max=max(v),n=len(v),vals=v)
for l in lv:
    w=[cell[(l,s)]['wrong'] for s in range(1,9)]; out[f"wrongruns|{l}"]=dict(runs_with_wrong=sum(x>0 for x in w),max=max(w))
def sign(d):
    lo=sum(x<-1e-9 for x in d); hi=sum(x>1e-9 for x in d); n=lo+hi
    return lo,hi,8-n,min(1.,2*sum(comb(n,i) for i in range(min(lo,hi)+1))/2**n) if n else 1.
for l in lv[1:]:
    d=[cell[(l,s)]['completeness']-cell[('9k',s)]['completeness'] for s in range(1,9)]
    m,lo,hi=ci(d); out[f"paired|{l}"]=dict(mean=m,lo=lo,hi=hi,sign=sign(d),min=min(d),max=max(d))
d=[cell[('80k',s)]['completeness']-cell[('60k',s)]['completeness'] for s in range(1,9)]
m,lo,hi=ci(d); out["paired|60k->80k"]=dict(mean=m,lo=lo,hi=hi,sign=sign(d))
json.dump({k:v for k,v in out.items()},open('appendix_deepseek_stats.json','w'),indent=1)
print("chosen runs at 60k:",{s:cell[('60k',s)]['run'] for s in range(1,9)})
for l in lv: print(l,[round(cell[(l,s)]['completeness'],2) for s in range(1,9)])
for l in lv:
    o=out[f'completeness|{l}']; print(l,f"mean {o['mean']:.3f} [{o['lo']:.3f},{o['hi']:.3f}] sd {o['sd']:.3f} range {o['min']:.2f}-{o['max']:.2f} | sound {out[f'soundness|{l}']['mean']:.3f} | chain {out[f'chain_recall|{l}']['mean']:.2f} join {out[f'join_recall|{l}']['mean']:.2f} | wrong runs {out[f'wrongruns|{l}']}")
for k in ['20k','40k','60k','80k','60k->80k']:
    o=out['paired|'+k]; print(k,f"{o['mean']:+.3f} [{o['lo']:+.3f},{o['hi']:+.3f}] lower/higher/tie/p {o['sign']}")
