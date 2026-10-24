#!/usr/bin/env python3
"""Sensitivity of 9k/40k/80k completeness to the two post-hoc analysis choices. Writes sensitivity_stats.json."""
import pandas as pd, re, json
from cell_pick import pick as _pick
S=pd.read_csv('seeds_results.csv'); N=pd.read_csv('seeds_results_normalised.csv')
lv={'L4':'9k','L4p40':'40k','L4p80':'80k'}
def pick(df,model,mode):
    d=df[(df.model==model)&df.level.isin(lv)].copy(); d['n']=d.run.str.replace(r'\D','',regex=True).astype(int)
    g=d.groupby(['level','seed'])
    if mode=='random':
        keep=[(r.level,r.seed,_pick(r.model,r.level,r.seed,list(d[(d.level==r.level)&(d.seed==r.seed)].run))) for r in d.drop_duplicates(['level','seed']).itertuples()]
        d=pd.concat([d[(d.level==l)&(d.seed==sd)&(d.run==rn)] for l,sd,rn in keep])
    elif mode=='latest': d=d.loc[g.n.idxmax()]
    elif mode=='first': d=d.loc[g.n.idxmin()]
    elif mode=='mean': d=g.completeness.mean().reset_index()
    p=d.pivot(index='seed',columns='level',values='completeness'); p.columns=[lv[c] for c in p.columns]; return p
def summ(p):
    r={k:round(float(p[k].mean()),3) for k in ['9k','40k','80k']}
    for a,b in [('9k','40k'),('9k','80k')]:
        dd=p[b]-p[a]; r[f'{a}->{b}']=dict(mean=round(float(dd.mean()),3),lower=int((dd<-1e-9).sum()),higher=int((dd>1e-9).sum()))
    return r
out={}
out['DeepSeek: primary']=summ(pick(N,'deepseek','random'))
out['GPT-5.5: primary (normalised)']=summ(pick(N,'gpt-5.5','random'))
out['GPT-5.5: strict']=summ(pick(S,'gpt-5.5','random'))
out['Gemini: primary (one run chosen at random)']=summ(pick(N,'gemini-3.1-pro-preview','random'))
out['Gemini: mean of repeats']=summ(pick(N,'gemini-3.1-pro-preview','mean'))
out['Gemini: first runs']=summ(pick(N,'gemini-3.1-pro-preview','first'))
out['Gemini: latest runs']=summ(pick(N,'gemini-3.1-pro-preview','latest'))
json.dump(out,open('sensitivity_stats.json','w'),indent=1)
for k,v in out.items(): print(k,v)
