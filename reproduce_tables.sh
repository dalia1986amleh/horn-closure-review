#!/usr/bin/env bash
# Recomputes every number behind Tables 2 to 5 (including 3b, 4b to 4g), Appendix A, the in-text numbers and the answer-key checks
# from the stored raw answers and prints PASS/FAIL against the shipped results. Run from this directory. No API calls, no keys, a few minutes.
set -e
# primary (article-optional) per-run scores: rescore runs_scored/ and compare with the shipped seeds_results_normalised.csv
RUNS_DIR=runs_scored python3 summarise_seeds.py > reproduced_summarise_seeds_normalised.txt && mv seeds_results.csv reproduced_seeds_results_normalised.csv
cmp -s reproduced_seeds_results_normalised.csv seeds_results_normalised.csv && echo "PASS seeds_results_normalised.csv" || { echo "FAIL seeds_results_normalised.csv"; exit 1; }
python3 summarise_seeds.py > reproduced_summarise_seeds.txt       # strict rescoring of every stored answer -> seeds_results.csv (Table 2 and per-run scores)
python3 analysis_three_lengths.py > reproduced_table3_4.txt       # Tables 3, 4 and 4g, three_lengths_stats.json
python3 sensitivity_table.py > reproduced_table4b.txt             # Table 4b
python3 gpt55_scoring_sensitivity.py > reproduced_table3b_4c.txt  # Tables 3b and 4c (strict vs article optional)
python3 depth_analysis.py > reproduced_table5.txt                 # Table 5 and the fact-level counts
python3 appendix_deepseek.py > reproduced_appendixA.txt           # Appendix A
python3 repeat_analysis.py > reproduced_table4d_4f.txt            # Tables 4d to 4f (DeepSeek-V4-Pro repeat study), repeat_stats.json
python3 repeat_sensitivity.py > reproduced_repeat_sensitivity.txt   # post hoc checks of Section 4 and Appendix B (replace 0.987 run; same-session runs)
python3 per_run_report.py runs_scored > reproduced_per_run_report.txt        # per_run_report.csv (conditional join recovery)
python3 root_miss_analysis.py runs_scored > reproduced_root_misses.txt       # root_miss_report.csv (root and downstream misses)
python3 in_text_numbers.py > reproduced_in_text_numbers.txt       # numbers quoted in the text without a table
python3 audit_check.py                                              # spot check of the 14-item audit sheet
python3 article_optional_check.py > reproduced_scorer_check.txt   # strict vs article-optional scorer: differs on exactly 3 runs
python3 backward_check.py | tail -1                               # key check 1 (backward proof search, 59 instances)
python3 derivation_graph.py check | tail -1                       # key check 3 (unique support, the 59 instances in this package)
python3 prompt_text_check.py | tail -1                            # key check 4 (key re-derived from the prompt text, 24 prompts)
python3 check_reproduction.py
# Key check 2 needs the Z3 solver:  pip install z3-solver && python3 z3_check.py
