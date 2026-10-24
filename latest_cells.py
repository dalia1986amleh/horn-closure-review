#!/usr/bin/env python3
"""Reads seeds_results.csv, keeps the LATEST run per (model, level, seed) (highest run tag number), writes seeds_latest.csv. All earlier runs stay in seeds_results.csv."""
import csv,re
rows=list(csv.DictReader(open('seeds_results.csv'))); best={}
for r in rows:
    k=(r['model'],r['level'],r['seed']); n=int(re.sub(r'\D','',r['run']) or 0)
    if k not in best or n>best[k][0]: best[k]=(n,r)
out=[v[1] for v in best.values()]
w=csv.DictWriter(open('seeds_latest.csv','w',newline=''),fieldnames=rows[0].keys()); w.writeheader(); w.writerows(out)
print(len(rows),'runs ->',len(out),'cells')
