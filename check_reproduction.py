#!/usr/bin/env python3
"""Compares recomputed JSON outputs with expected_outputs/ (numbers to 6 decimals)."""
import csv, json, math, os, sys
bad = 0
def close(a, b):
    if isinstance(a, dict): return a.keys() == b.keys() and all(close(a[k], b[k]) for k in a)
    if isinstance(a, list): return len(a) == len(b) and all(close(x, y) for x, y in zip(a, b))
    if isinstance(a, float) or isinstance(b, float): return a is not None and b is not None and math.isclose(a, b, rel_tol=1e-6, abs_tol=1e-6)
    return a == b
for f in sorted(os.listdir("expected_outputs")):
    if not f.endswith(".json"): continue
    ok = close(json.load(open(f)), json.load(open(os.path.join("expected_outputs", f)))); bad += not ok
    print(("PASS" if ok else "FAIL"), f)
print("All reproduced outputs match." if not bad else f"{bad} file(s) differ.")
sys.exit(1 if bad else 0)
