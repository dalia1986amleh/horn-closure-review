import json, matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
D = json.load(open("three_lengths_stats.json"))
C = {"DeepSeek-V4-Pro": "#1f5aa6", "GPT-5.5": "#d95f02", "Gemini 3.1 Pro": "#1b9e77"}
MK = {"DeepSeek-V4-Pro": "s", "GPT-5.5": "D", "Gemini 3.1 Pro": "o"}
X = ["Unpadded\n(~9k)", "40k", "80k"]; K = ["9k", "40k", "80k"]
plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False})
# Fig 1: per problem, one panel per model
fig, ax = plt.subplots(1, 3, figsize=(10.5, 3.8), dpi=200, sharey=True)
for a, (m, d) in zip(ax, D.items()):
    for i in range(8):
        a.plot(range(3), [d["completeness"][k][i] for k in K], color="#b0b0b0", lw=1, marker="o", ms=3, zorder=1)
    mu = [sum(d["completeness"][k]) / 8 for k in K]
    a.plot(range(3), mu, color=C[m], lw=2.6, marker=MK[m], ms=7, zorder=3)
    for i, v in enumerate(mu): a.annotate(f"{v:.2f}", (i, v), xytext=(0, -14), textcoords="offset points", ha="center", fontsize=8, color=C[m])
    if m == "GPT-5.5":
        G = json.load(open("gpt55_scoring_sensitivity.json"))["means"]["strict"]; ms = [G[k] for k in K]
        a.plot(range(3), ms, color="#7a1f00", lw=1.8, ls="--", marker="x", ms=7, zorder=4)
        for i, v in enumerate(ms):
            if abs(v - mu[i]) > .01: a.annotate(f"strict {v:.2f}", (i, v), xytext=(8, -13), textcoords="offset points", ha="left", fontsize=7.5, color="#7a1f00")
    a.set_title(m, fontsize=10); a.set_xticks(range(3)); a.set_xticklabels(X); a.set_xlim(-.3, 2.3); a.grid(axis="y", alpha=.25)
ax[0].set_ylabel("Completeness"); ax[0].set_ylim(0, 1.04)
fig.text(.5, .01, "Grey: each of the 8 problems. Coloured: mean over problems. GPT-5.5 panel: dashed line = mean under strict scoring (article required).", ha="center", fontsize=8, color="#555")
plt.tight_layout(rect=(0, .04, 1, 1)); plt.savefig("fig1_completeness_by_problem.png")
# Fig 2: completeness vs soundness, every run at 40k and 80k
fig, ax = plt.subplots(figsize=(6.2, 4.2), dpi=200)
for m, d in D.items():
    for k, fill in (("40k", True), ("80k", False)):
        xs = d["completeness"][k]; ys = [1.0 if s is None else s for s in d["soundness"][k]]
        ax.scatter(xs, ys, s=34, marker=MK[m], facecolors=C[m] if fill else "none", edgecolors=C[m], linewidths=1.4, label=f"{m}, {k}")
ax.set_ylim(.9, 1.005); ax.set_xlim(0, 1.03); ax.set_xlabel("Completeness"); ax.set_ylabel("Soundness (axis starts at 0.90)")
ax.grid(alpha=.25); ax.legend(fontsize=7, ncol=2, loc="lower left"); plt.tight_layout(); plt.savefig("fig2_completeness_vs_soundness.png")
# Fig 3: chain vs join recall at the three lengths
fig, ax = plt.subplots(1, 3, figsize=(10.5, 3.6), dpi=200, sharey=True)
for a, (m, d) in zip(ax, D.items()):
    ch = [sum(d["chain"][k]) / 8 for k in K]; jn = [sum(d["join"][k]) / len(d["join"][k]) for k in K]
    a.plot(range(3), ch, color=C[m], lw=2.2, marker="o", ms=6, label="chain facts")
    a.plot(range(3), jn, color=C[m], lw=2.2, marker="s", ms=6, ls="--", mfc="white", label="join facts")
    for i in range(3):
        a.annotate(f"{ch[i]:.2f}", (i, ch[i]), xytext=(0, 7), textcoords="offset points", ha="center", fontsize=8)
        a.annotate(f"{jn[i]:.2f}", (i, jn[i]), xytext=(0, -14), textcoords="offset points", ha="center", fontsize=8)
    a.set_title(m, fontsize=10); a.set_xticks(range(3)); a.set_xticklabels(X); a.set_xlim(-.3, 2.3); a.grid(axis="y", alpha=.25); a.legend(fontsize=8, loc="lower left")
ax[0].set_ylabel("Mean recall over 8 problems"); ax[0].set_ylim(.3, 1.08)
plt.tight_layout(); plt.savefig("fig3_chain_vs_join.png")
# Fig 4: recall by derivation depth bin at 40k and 80k (from depth_stats.json)
S = json.load(open("depth_stats.json")); B = ["1 to 5", "6 to 10", "11 to 15", "16 +"]; LO = [1, 6, 11, 16]
fig, ax = plt.subplots(1, 2, figsize=(9.2, 3.6), dpi=200, sharey=True)
for a, lab in zip(ax, ("40k", "80k")):
    for m in C:
        v = [S[f"{m}|{lab}"][f"d|{lo}"]["mean"] for lo in LO]
        a.plot(range(4), v, color=C[m], lw=2.2, marker=MK[m], ms=6, label=m)
    a.set_xticks(range(4)); a.set_xticklabels(B); a.set_xlabel("Derivation depth of the fact"); a.set_title(f"{lab} padding", fontsize=10); a.grid(axis="y", alpha=.25)
ax[0].set_ylabel("Share of facts listed (mean over 8 problems)"); ax[0].set_ylim(.5, 1.03); ax[1].legend(fontsize=8, loc="lower left")
plt.tight_layout(); plt.savefig("fig4_recall_by_depth.png")
