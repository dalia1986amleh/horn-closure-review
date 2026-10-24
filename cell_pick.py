"""One scored run per cell. Where a cell (model, level, problem) has more than one run, one run is chosen at random.
The draw is fixed by the cell identity, so it is reproducible and does not depend on order or on the scores."""
import random
def pick(model, level, seed, runs):
    """runs: list of run tags/items (any order). Returns one item; deterministic for a given cell."""
    runs = sorted(runs, key=lambda x: str(x))
    if len(runs) == 1: return runs[0]
    return random.Random(f"1|{model}|{level}|{seed}").choice(runs)
