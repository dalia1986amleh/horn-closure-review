# Repeat study protocol (DeepSeek-V4-Pro) - frozen before any repeat run

**Question.** How stable is DeepSeek-V4-Pro's completeness on the same 8 problems when the same prompt is run again, and does the decline from unpadded to 80k persist when each cell has three runs?

**Design.** Cells: problems 1-8 x {unpadded (L4), 80k (L4p80)}. Target: 3 runs per cell = the original run plus 2 repeats. The two earlier noise-check runs at 80k (problems 2 and 7, tag n1) count as repeat 1 for those cells. 30 new runs in total, in the shuffled order of repeat_runs_plan.csv (fixed seed string "repeat-plan-v1|deepseek"). Same prompts, model name, endpoint, output cap (128,000) and scorer as the original runs. Runs are made one at a time inside one short collection window, and the order interleaves unpadded and 80k.

**Counting rule (fixed now).**
1. Every valid model response counts as a run, whatever its score. No response is dropped because of its score or because it looks odd.
2. A *valid response* is any returned answer, including one that is incomplete or ends at the output cap (finish reason "length"). It is scored as returned and flagged.
3. A *technical failure* is a run with no usable response (provider error, timeout, empty output). It is retried once with the same prompt. Both attempts stay in the log. If the retry also fails, that run is reported as missing.
4. A retry is never used to replace a valid response.
5. No extra runs are added after seeing results, for any cell.

**Primary analysis.** For each problem, completeness per cell = mean of its runs. The change from unpadded to 80k is the paired difference of these per-problem means over the 8 problems: mean change, percentile bootstrap interval (20,000 resamples of problems), problems lower / higher, exact sign test. The unit of analysis is the problem (n = 8). The runs are repeated calls on the same eight problems, not independent problems, so the intervals describe variation across these eight problems only.

**Secondary (always reported).** Per-cell minimum, maximum and SD across runs; the same analysis using only the original run (the current main analysis); the same analysis using the first repeat only; the largest within-cell range and which cell it is.

**Metadata logged for every run.** Model identifier as called, returned identifier (none), timestamps (UTC), input/output/reasoning tokens, finish reason, seconds, attempt number.

**Not claimed.** Nothing here shows the effect for other models, other tasks or new problems, or that the served model was unchanged. A short window reduces version-drift risk but does not prove it.

**What is reported regardless of the outcome.** All runs, all retries, all missing runs.
