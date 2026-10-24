import json, statistics as st, math
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
A=json.load(open("appendix_deepseek_stats.json"))
L=["9k","20k","40k","60k","80k"]; X=[9,20,40,60,80]
sm={}
for l in ["9k","20k","40k","60k","80k"]:
    for i,v in enumerate(A[f"completeness|{l}"]["vals"],1): sm[(l,i)]=v   # one run per cell (cell_pick.py)
T={2:12.706,3:4.303,4:3.182,5:2.776,6:2.571,7:2.447,8:2.365}
def ci(v):
    n=len(v); m=st.mean(v)
    if n<2: return m,m
    h=T[n]*st.stdev(v)/math.sqrt(n); return m-h,m+h
gpt={1:1.0,2:0.8783,4:0.9233,6:0.9933,8:0.7649}
fig,ax=plt.subplots(1,2,figsize=(10.5,4.2),dpi=200)
a=ax[0]
for s in range(1,9):
    pts=[(x,sm[(l,s)]) for x,l in zip(X,L) if (l,s) in sm]
    a.plot(*zip(*pts),color="#9a9a9a",lw=1,marker="o",ms=3,alpha=.9,zorder=1)
    a.annotate(str(s),pts[-1],xytext=(4,0),textcoords="offset points",fontsize=7,color="#666")
mx=[];lo=[];hi=[]
for l in L:
    v=[sm[(l,s)] for s in range(1,9) if (l,s) in sm]; m=st.mean(v); c=ci(v); mx.append(m); lo.append(max(0,m-c[0]) if False else m-c[0]); hi.append(min(1,c[1])-m)
a.errorbar([x+0.8 for x in X],mx,yerr=[lo,[min(h,1-m) for h,m in zip(hi,mx)]],color="#1f5aa6",lw=2,marker="s",capsize=3,zorder=3,label="Mean over problems (95% t-CI)")
a.plot([],[],color="#9a9a9a",marker="o",ms=3,label="Each DeepSeek problem (seed no.)")
a.set_ylim(0,1.04);a.set_xlim(5,88);a.set_xlabel("Prompt length (thousand tokens)");a.set_ylabel("Completeness")
a.set_title("(a) Completeness per problem",fontsize=10);a.legend(fontsize=7,loc="lower left");a.grid(alpha=.25)
b=ax[1]
import random
for i,l in enumerate(L[1:]):
    d=[(s,sm[(l,s)]-sm[("9k",s)]) for s in range(1,9) if (l,s) in sm]
    xs=[X[i+1]+(j-len(d)/2)*0.9 for j in range(len(d))]
    b.scatter(xs,[v for _,v in d],color="#9a9a9a",s=14,zorder=2)
    v=[x for _,x in d]; m=st.mean(v); c=ci(v)
    b.errorbar([X[i+1]+0.0],[m],yerr=[[m-c[0]],[c[1]-m]],color="#1f5aa6",marker="s",capsize=4,lw=2,zorder=3)
    b.annotate(f"n={len(v)}",(X[i+1],-0.72),ha="center",fontsize=7)
b.axhline(0,color="#444",lw=.8);b.set_ylim(-1.05,0.15);b.set_xlim(10,88)
b.set_xlabel("Prompt length (thousand tokens)");b.set_ylabel("Change in completeness vs 9k (same problem)")
b.set_title("(b) Paired change from 9k",fontsize=10);b.grid(alpha=.25)
for q in ax:
    for sp in ("top","right"): q.spines[sp].set_visible(False)
plt.tight_layout();plt.savefig("fig_deepseek_extra_lengths.png")
