import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
fig,ax=plt.subplots(figsize=(10,6)); ax.set_xlim(0,100); ax.set_ylim(-9,52); ax.axis("off")
def box(x,y,w,h,t,fc="#f3f4f6",ec="#9ca3af",fs=9,bold=False):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle="round,pad=0.3,rounding_size=1.2",fc=fc,ec=ec,lw=1.1))
    ax.text(x+w/2,y+h/2,t,ha="center",va="center",fontsize=fs,fontweight="bold" if bold else "normal",color="#111827")
def arrow(x1,y1,x2,y2):
    ax.annotate("",xy=(x2,y2),xytext=(x1,y1),arrowprops=dict(arrowstyle="->",color="#6b7280",lw=1.1))
box(1,18,20,10,"Rules as stated\nin the English prompt\n(two rule forms +\nstart fact)",fc="#e8eef8",ec="#3b6ab5")
box(29,43,24,8,"Generator:\nforward chaining\n→ stored key K",fc="#e8eef8",ec="#3b6ab5")
arrow(21,26,29,46)
rows=[("1  Backward proof search\n(own parser, memoised)","59 instances",32),
      ("2  Z3: theory ∧ ¬p unsatisfiable?\n(propositional Horn encoding)","59 instances",21),
      ("3  Unique-derivation check\n(each fact has one rule)","90 instances",10),]
for t,u,y in rows:
    box(29,y-3,31,8,t,fs=8.5); box(62,y-3,13,8,u,fs=8.5,fc="#ffffff"); arrow(21,22,29,y+1)
box(29,-5,31,8,"4  Re-derivation from the prompt\ntext (regular expressions only)",fs=8.5); box(62,-5,13,8,"24 prompts",fs=8.5,fc="#ffffff"); arrow(21,20,29,-1)
box(82,12,17,18,"Result\n\nChecks 1, 2, 4:\nsame set as K\n(59, 59, 24 agree)\nCheck 3: 0 facts\nwith >1 derivation",fc="#e6f4ea",ec="#2f855a",fs=8.5)
for y in (32,21,10,-3): arrow(75,y+1,82,21)
ax.text(50,-8.2,"All four checks read the rules as stated in the prompt; none is an audit of those semantics by a human reader.",ha="center",fontsize=8.5,color="#4b5563",style="italic")
plt.savefig("fig_key_checks.png",dpi=200,bbox_inches="tight"); print("ok")
