# Anonymous review artifact
Do Reasoning LLMs List All Consequences of Horn Rules as Irrelevant Padding Grows? (double-blind submission).

This package contains everything needed to audit the reported numbers without any model call: the generated problems and answer keys, the exact prompts, every stored model answer with run metadata, the scoring code, and the scripts that recompute each table and the numbers quoted in the text. It contains no author names, institution names or API keys.

## Quick start (a few minutes, Python 3.10+)
    pip install -r requirements.txt
    bash reproduce_tables.sh
The script rescores every stored answer under both scoring rules (the primary, article-optional scores are compared with the shipped `seeds_results_normalised.csv`), recomputes the tables below, regenerates the two report files and the in-text numbers, runs the backward-search, unique-support and prompt-text answer-key checks, and ends with `All reproduced outputs match.` if the recomputed JSON files equal `expected_outputs/`. The Z3 check (`z3_check.py`) is run separately because it needs `z3-solver`. Every random step (bootstrap resamples, the choice of one run for a repeated cell) is seeded.

## What produces what
| Paper item | Script | Output |
|---|---|---|
| Per-run scores, primary (article optional) | `RUNS_DIR=runs_scored python3 summarise_seeds.py` (uses `score_responses.py`) | `seeds_results_normalised.csv` |
| Per-run scores, strict scorer; Table 2 | `summarise_seeds.py` | `seeds_results.csv` |
| Tables 3, 4 and 4g (t and Wilcoxon p-values), Figures 1 to 4 | `analysis_three_lengths.py`, `make_figs_three_lengths.py` | `three_lengths_stats.json` |
| Table 4b (analysis-choice sensitivity) | `sensitivity_table.py` | `sensitivity_stats.json` |
| Tables 3b and 4c (GPT-5.5 strict vs article optional; unaffected problems) | `gpt55_scoring_sensitivity.py` | `gpt55_scoring_sensitivity.json` |
| Table 5, fact-level counts | `depth_analysis.py` | `depth_stats.json` |
| Tables 4d, 4e and 4f (DeepSeek-V4-Pro repeat study: three runs per problem at unpadded and 80k) | `repeat_analysis.py` (protocol and run plan in `repeat_study/`) | `repeat_stats.json` |
| Post hoc checks of the repeat study (0.987 run replaced; runs of one session only) | `repeat_sensitivity.py` | `repeat_sensitivity.json` |
| Conditional join recovery, per run | `python3 per_run_report.py runs_scored` | `per_run_report.csv` |
| Root versus downstream misses, per run | `python3 root_miss_analysis.py runs_scored` | `root_miss_report.csv` |
| Numbers quoted in the text without a table (leave-one-out ranges, Gemini 40k and DeepSeek 60k alternatives, pooled conditional join counts, root-miss counts) | `in_text_numbers.py` | printed |
| Spot check of 14 items (10 entailed, 4 not entailed); the sheet itself is for a human reader | `audit_sheet_make.py`, `audit_check.py`, `human_audit_sheet.md` | printed |
| Appendix A | `appendix_deepseek.py`, `make_fig_deepseek_extra_lengths.py` | `appendix_deepseek_stats.json` |
| Scorer check (strict vs article optional differ on exactly 3 runs) | `article_optional_check.py` | printed |
| Answer-key checks | `backward_check.py` (59 instances), `prompt_text_check.py` (24 prompts), `python3 derivation_graph.py check` (unique support; the 59 instances in this package, of the 90 reported in the paper), `z3_check.py` (59 instances, needs `z3-solver`); Figure C1: `make_fig_key_checks.py` | printed |

## Contents
- `release/`: `problems.jsonl`, `problems_summary.csv`, `control_audit.csv` (8 problems in 5 context conditions: premises, start fact, key, padding audit). The `prompt_file` field gives paths under `prompts/`; the files are in `prompts_v2/`.
- `seed_*/`: generator output per problem and length (instances, items, predicates), including the 19 instances at other generator levels (L3, L5, and one L4 problem padded to 120k) that no reported result uses.
- `prompts_v2/`: prompts as sent to the models. The `PROMPT_SEED_*` prompts are the study's; the other families (`A`, `F`, `J`, `LADDER`, `NEG`, `NEST`, `PROBE`) are pilot prompts that no reported result uses.
- `runs/`: every stored model answer (`.txt`) and its run metadata (`.json`): token counts, finish status and, where recorded, the model identifier returned by the API and the output cap. The metadata field `sent_utc` records when the response was received. The 8 GPT-5.5 runs sent on 15 and 16 October use an earlier metadata format without the returned identifier, output cap or decoding settings, and the two second Gemini 3.1 Pro runs at 40k (tag `m2`) have no metadata file. Runs not used in any reported result: DeepSeek-V4-Pro at levels L3 and L5, gpt-5-mini at L3 and L4, and 16 pilot runs on `PROMPT_NEST_*` prompts (gpt-5-mini and GPT-5.5, tag `r1`).
- `runs_scored/`: the answers scored for the primary analysis, i.e. `runs/` with the three GPT-5.5 answers that lack the word "a" replaced by versions with "a" inserted (article-optional reading); those three normalised answers are also in `runs_normalised/`.
- `repeat_study/`: `PROTOCOL.md` (design, run order, retry and analysis rules, written before the repeats), `repeat_plan.py`, `repeat_runs_plan.csv`, `repeat_commands.sh`, and `runs/` with the 30 repeat runs (tags rep1, rep2) and one extra run (tag x1, outside the plan, in no mean; used only in the post hoc check). `noise_check_deepseek/`: the four-cell check (tag n1); the two 80k runs are repeat 1 of problems 2 and 7. Reasoning-text files of these runs are not included.
- `MANIFEST.csv`: every file with size and SHA-256 (except `MANIFEST.csv` itself); for run files also model, length, problem (seed) and run tag.
- `expected_outputs/`: the JSON results and figures that the paper reports; `check_reproduction.py` compares recomputed files with them.
- `generate_*.py`, `build_prompts.py`, `build_release.py`: problem and prompt generation. `run_openai.py`, `run_gemini.py`, `run_deepseek.py`: the API callers (reading keys from environment variables).

## Conventions
- Unit of analysis: the problem (seed). One scored run per model, problem and length in Tables 3 to 5 (the DeepSeek-V4-Pro repeat study, Tables 4e and 4f, uses the original run plus two repeats); if a cell has more than one stored run, `cell_pick.py` draws one by a fixed seed derived from the cell, independent of the scores. Run tags: `g1` GPT-5.5, `m1`/`m2` Gemini, `d1` to `d3` DeepSeek, `r1` gpt-5-mini and pilot runs.
- Scoring: the primary scorer reads "T is [a/an] word" with the article optional; the strict scorer requires the article. They differ on exactly three GPT-5.5 outputs (unpadded problems 4 and 5, problem 1 at 40k). `seeds_results.csv` holds strict scores, `seeds_results_normalised.csv` the primary scores; the paper reports both for GPT-5.5.

## What cannot be reproduced here
- The model calls themselves (provider-served models change over time; DeepSeek-V4-Pro returns no version identifier; temperature and seed were not set; Gemini used its default thinking setting). The stored answers are the evidence; rerunning would sample new answers.
- `z3_check.py` needs the `z3-solver` package; the Z3 version is printed by `python3 -c "import z3; print(z3.get_version_string())"`.
- The unique-support check in the paper covers 90 instances; 31 of them are not in this package.
