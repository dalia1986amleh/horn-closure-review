#!/usr/bin/env bash
# Recomputes every number behind Tables 2 to 5 (including 3b, 4b and 4c), Appendix A and the answer-key checks from the stored
# raw answers and prints PASS/FAIL against expected_outputs/. Run from this directory. No API calls, no keys, a few minutes.
set -e
python3 summarise_seeds.py > reproduced_summarise_seeds.txt       # rescoring of every stored answer -> seeds_results.csv (Table 2 and per-run scores)
python3 analysis_three_lengths.py > reproduced_table3_4.txt       # Tables 3 and 4, three_lengths_stats.json
python3 sensitivity_table.py > reproduced_table4b.txt             # Table 4b
python3 gpt55_scoring_sensitivity.py > reproduced_table3b_4c.txt  # Tables 3b and 4c (strict vs article optional)
python3 depth_analysis.py > reproduced_table5.txt                 # Table 5 and the fact-level counts
python3 appendix_deepseek.py > reproduced_appendixA.txt           # Appendix A
python3 repeat_analysis.py > reproduced_table4d_4f.txt            # Tables 4d to 4f (DeepSeek-V4-Pro repeat study), repeat_stats.json
python3 repeat_sensitivity.py > reproduced_repeat_sensitivity.txt   # post hoc checks of Section 4 and Appendix B (replace 0.987 run; same-session runs)
python3 audit_check.py                                              # spot check of the 14-item audit sheet
python3 article_optional_check.py > reproduced_scorer_check.txt   # strict vs article-optional scorer: differs on exactly 3 runs
python3 backward_check.py | tail -1                               # key check 1 (backward proof search, 59 instances)
python3 prompt_text_check.py | tail -1                            # key check 4 (key re-derived from the prompt text, 24 prompts)
python3 check_reproduction.py
# Key check 2 needs the Z3 solver:  pip install z3-solver && python3 z3_check.py
