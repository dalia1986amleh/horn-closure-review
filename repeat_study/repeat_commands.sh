#!/usr/bin/env bash
# DeepSeek-V4-Pro repeat study: 30 runs, one at a time, in the pre-shuffled order of repeat_runs_plan.csv. Safe to re-run (finished runs are skipped).
# Start in OFF-PEAK hours (UK time: peak is 02:00-05:00 and 07:00-11:00 Mon-Fri in BST when UTC+1; check the DeepSeek pricing page).
# Key stays in your terminal:  export DEEPSEEK_API_KEY=...   Answers go to runs_repeat/.
mkdir -p runs_repeat
set -u
ls runs_repeat/*PROMPT_SEED_L4p80_s2_A__rep2.txt >/dev/null 2>&1 && echo "skip 1 L4p80 s2 rep2" || \
  python3 run_deepseek.py --prompt prompts_v2/PROMPT_SEED_L4p80_s2_A.txt --model deepseek-v4-pro --base-url https://api.deepseek.com --key-env DEEPSEEK_API_KEY --instance SEEDL4p80s2 --data-dir seed_L4p80_s2 --max-output-tokens 128000 --tag rep2 --out runs_repeat
ls runs_repeat/*PROMPT_SEED_L4_s1_A__rep1.txt >/dev/null 2>&1 && echo "skip 2 L4 s1 rep1" || \
  python3 run_deepseek.py --prompt prompts_v2/PROMPT_SEED_L4_s1_A.txt --model deepseek-v4-pro --base-url https://api.deepseek.com --key-env DEEPSEEK_API_KEY --instance SEEDL4s1 --data-dir seed_L4_s1 --max-output-tokens 128000 --tag rep1 --out runs_repeat
ls runs_repeat/*PROMPT_SEED_L4_s6_A__rep1.txt >/dev/null 2>&1 && echo "skip 3 L4 s6 rep1" || \
  python3 run_deepseek.py --prompt prompts_v2/PROMPT_SEED_L4_s6_A.txt --model deepseek-v4-pro --base-url https://api.deepseek.com --key-env DEEPSEEK_API_KEY --instance SEEDL4s6 --data-dir seed_L4_s6 --max-output-tokens 128000 --tag rep1 --out runs_repeat
ls runs_repeat/*PROMPT_SEED_L4p80_s8_A__rep2.txt >/dev/null 2>&1 && echo "skip 4 L4p80 s8 rep2" || \
  python3 run_deepseek.py --prompt prompts_v2/PROMPT_SEED_L4p80_s8_A.txt --model deepseek-v4-pro --base-url https://api.deepseek.com --key-env DEEPSEEK_API_KEY --instance SEEDL4p80s8 --data-dir seed_L4p80_s8 --max-output-tokens 128000 --tag rep2 --out runs_repeat
ls runs_repeat/*PROMPT_SEED_L4p80_s1_A__rep1.txt >/dev/null 2>&1 && echo "skip 5 L4p80 s1 rep1" || \
  python3 run_deepseek.py --prompt prompts_v2/PROMPT_SEED_L4p80_s1_A.txt --model deepseek-v4-pro --base-url https://api.deepseek.com --key-env DEEPSEEK_API_KEY --instance SEEDL4p80s1 --data-dir seed_L4p80_s1 --max-output-tokens 128000 --tag rep1 --out runs_repeat
ls runs_repeat/*PROMPT_SEED_L4_s1_A__rep2.txt >/dev/null 2>&1 && echo "skip 6 L4 s1 rep2" || \
  python3 run_deepseek.py --prompt prompts_v2/PROMPT_SEED_L4_s1_A.txt --model deepseek-v4-pro --base-url https://api.deepseek.com --key-env DEEPSEEK_API_KEY --instance SEEDL4s1 --data-dir seed_L4_s1 --max-output-tokens 128000 --tag rep2 --out runs_repeat
ls runs_repeat/*PROMPT_SEED_L4_s3_A__rep1.txt >/dev/null 2>&1 && echo "skip 7 L4 s3 rep1" || \
  python3 run_deepseek.py --prompt prompts_v2/PROMPT_SEED_L4_s3_A.txt --model deepseek-v4-pro --base-url https://api.deepseek.com --key-env DEEPSEEK_API_KEY --instance SEEDL4s3 --data-dir seed_L4_s3 --max-output-tokens 128000 --tag rep1 --out runs_repeat
ls runs_repeat/*PROMPT_SEED_L4p80_s3_A__rep1.txt >/dev/null 2>&1 && echo "skip 8 L4p80 s3 rep1" || \
  python3 run_deepseek.py --prompt prompts_v2/PROMPT_SEED_L4p80_s3_A.txt --model deepseek-v4-pro --base-url https://api.deepseek.com --key-env DEEPSEEK_API_KEY --instance SEEDL4p80s3 --data-dir seed_L4p80_s3 --max-output-tokens 128000 --tag rep1 --out runs_repeat
ls runs_repeat/*PROMPT_SEED_L4p80_s5_A__rep2.txt >/dev/null 2>&1 && echo "skip 9 L4p80 s5 rep2" || \
  python3 run_deepseek.py --prompt prompts_v2/PROMPT_SEED_L4p80_s5_A.txt --model deepseek-v4-pro --base-url https://api.deepseek.com --key-env DEEPSEEK_API_KEY --instance SEEDL4p80s5 --data-dir seed_L4p80_s5 --max-output-tokens 128000 --tag rep2 --out runs_repeat
ls runs_repeat/*PROMPT_SEED_L4_s6_A__rep2.txt >/dev/null 2>&1 && echo "skip 10 L4 s6 rep2" || \
  python3 run_deepseek.py --prompt prompts_v2/PROMPT_SEED_L4_s6_A.txt --model deepseek-v4-pro --base-url https://api.deepseek.com --key-env DEEPSEEK_API_KEY --instance SEEDL4s6 --data-dir seed_L4_s6 --max-output-tokens 128000 --tag rep2 --out runs_repeat
ls runs_repeat/*PROMPT_SEED_L4_s3_A__rep2.txt >/dev/null 2>&1 && echo "skip 11 L4 s3 rep2" || \
  python3 run_deepseek.py --prompt prompts_v2/PROMPT_SEED_L4_s3_A.txt --model deepseek-v4-pro --base-url https://api.deepseek.com --key-env DEEPSEEK_API_KEY --instance SEEDL4s3 --data-dir seed_L4_s3 --max-output-tokens 128000 --tag rep2 --out runs_repeat
ls runs_repeat/*PROMPT_SEED_L4p80_s5_A__rep1.txt >/dev/null 2>&1 && echo "skip 12 L4p80 s5 rep1" || \
  python3 run_deepseek.py --prompt prompts_v2/PROMPT_SEED_L4p80_s5_A.txt --model deepseek-v4-pro --base-url https://api.deepseek.com --key-env DEEPSEEK_API_KEY --instance SEEDL4p80s5 --data-dir seed_L4p80_s5 --max-output-tokens 128000 --tag rep1 --out runs_repeat
ls runs_repeat/*PROMPT_SEED_L4p80_s4_A__rep1.txt >/dev/null 2>&1 && echo "skip 13 L4p80 s4 rep1" || \
  python3 run_deepseek.py --prompt prompts_v2/PROMPT_SEED_L4p80_s4_A.txt --model deepseek-v4-pro --base-url https://api.deepseek.com --key-env DEEPSEEK_API_KEY --instance SEEDL4p80s4 --data-dir seed_L4p80_s4 --max-output-tokens 128000 --tag rep1 --out runs_repeat
ls runs_repeat/*PROMPT_SEED_L4p80_s6_A__rep2.txt >/dev/null 2>&1 && echo "skip 14 L4p80 s6 rep2" || \
  python3 run_deepseek.py --prompt prompts_v2/PROMPT_SEED_L4p80_s6_A.txt --model deepseek-v4-pro --base-url https://api.deepseek.com --key-env DEEPSEEK_API_KEY --instance SEEDL4p80s6 --data-dir seed_L4p80_s6 --max-output-tokens 128000 --tag rep2 --out runs_repeat
ls runs_repeat/*PROMPT_SEED_L4p80_s7_A__rep2.txt >/dev/null 2>&1 && echo "skip 15 L4p80 s7 rep2" || \
  python3 run_deepseek.py --prompt prompts_v2/PROMPT_SEED_L4p80_s7_A.txt --model deepseek-v4-pro --base-url https://api.deepseek.com --key-env DEEPSEEK_API_KEY --instance SEEDL4p80s7 --data-dir seed_L4p80_s7 --max-output-tokens 128000 --tag rep2 --out runs_repeat
ls runs_repeat/*PROMPT_SEED_L4_s7_A__rep1.txt >/dev/null 2>&1 && echo "skip 16 L4 s7 rep1" || \
  python3 run_deepseek.py --prompt prompts_v2/PROMPT_SEED_L4_s7_A.txt --model deepseek-v4-pro --base-url https://api.deepseek.com --key-env DEEPSEEK_API_KEY --instance SEEDL4s7 --data-dir seed_L4_s7 --max-output-tokens 128000 --tag rep1 --out runs_repeat
ls runs_repeat/*PROMPT_SEED_L4_s7_A__rep2.txt >/dev/null 2>&1 && echo "skip 17 L4 s7 rep2" || \
  python3 run_deepseek.py --prompt prompts_v2/PROMPT_SEED_L4_s7_A.txt --model deepseek-v4-pro --base-url https://api.deepseek.com --key-env DEEPSEEK_API_KEY --instance SEEDL4s7 --data-dir seed_L4_s7 --max-output-tokens 128000 --tag rep2 --out runs_repeat
ls runs_repeat/*PROMPT_SEED_L4_s4_A__rep2.txt >/dev/null 2>&1 && echo "skip 18 L4 s4 rep2" || \
  python3 run_deepseek.py --prompt prompts_v2/PROMPT_SEED_L4_s4_A.txt --model deepseek-v4-pro --base-url https://api.deepseek.com --key-env DEEPSEEK_API_KEY --instance SEEDL4s4 --data-dir seed_L4_s4 --max-output-tokens 128000 --tag rep2 --out runs_repeat
ls runs_repeat/*PROMPT_SEED_L4_s2_A__rep2.txt >/dev/null 2>&1 && echo "skip 19 L4 s2 rep2" || \
  python3 run_deepseek.py --prompt prompts_v2/PROMPT_SEED_L4_s2_A.txt --model deepseek-v4-pro --base-url https://api.deepseek.com --key-env DEEPSEEK_API_KEY --instance SEEDL4s2 --data-dir seed_L4_s2 --max-output-tokens 128000 --tag rep2 --out runs_repeat
ls runs_repeat/*PROMPT_SEED_L4_s5_A__rep1.txt >/dev/null 2>&1 && echo "skip 20 L4 s5 rep1" || \
  python3 run_deepseek.py --prompt prompts_v2/PROMPT_SEED_L4_s5_A.txt --model deepseek-v4-pro --base-url https://api.deepseek.com --key-env DEEPSEEK_API_KEY --instance SEEDL4s5 --data-dir seed_L4_s5 --max-output-tokens 128000 --tag rep1 --out runs_repeat
ls runs_repeat/*PROMPT_SEED_L4_s8_A__rep1.txt >/dev/null 2>&1 && echo "skip 21 L4 s8 rep1" || \
  python3 run_deepseek.py --prompt prompts_v2/PROMPT_SEED_L4_s8_A.txt --model deepseek-v4-pro --base-url https://api.deepseek.com --key-env DEEPSEEK_API_KEY --instance SEEDL4s8 --data-dir seed_L4_s8 --max-output-tokens 128000 --tag rep1 --out runs_repeat
ls runs_repeat/*PROMPT_SEED_L4p80_s8_A__rep1.txt >/dev/null 2>&1 && echo "skip 22 L4p80 s8 rep1" || \
  python3 run_deepseek.py --prompt prompts_v2/PROMPT_SEED_L4p80_s8_A.txt --model deepseek-v4-pro --base-url https://api.deepseek.com --key-env DEEPSEEK_API_KEY --instance SEEDL4p80s8 --data-dir seed_L4p80_s8 --max-output-tokens 128000 --tag rep1 --out runs_repeat
ls runs_repeat/*PROMPT_SEED_L4p80_s4_A__rep2.txt >/dev/null 2>&1 && echo "skip 23 L4p80 s4 rep2" || \
  python3 run_deepseek.py --prompt prompts_v2/PROMPT_SEED_L4p80_s4_A.txt --model deepseek-v4-pro --base-url https://api.deepseek.com --key-env DEEPSEEK_API_KEY --instance SEEDL4p80s4 --data-dir seed_L4p80_s4 --max-output-tokens 128000 --tag rep2 --out runs_repeat
ls runs_repeat/*PROMPT_SEED_L4_s5_A__rep2.txt >/dev/null 2>&1 && echo "skip 24 L4 s5 rep2" || \
  python3 run_deepseek.py --prompt prompts_v2/PROMPT_SEED_L4_s5_A.txt --model deepseek-v4-pro --base-url https://api.deepseek.com --key-env DEEPSEEK_API_KEY --instance SEEDL4s5 --data-dir seed_L4_s5 --max-output-tokens 128000 --tag rep2 --out runs_repeat
ls runs_repeat/*PROMPT_SEED_L4p80_s3_A__rep2.txt >/dev/null 2>&1 && echo "skip 25 L4p80 s3 rep2" || \
  python3 run_deepseek.py --prompt prompts_v2/PROMPT_SEED_L4p80_s3_A.txt --model deepseek-v4-pro --base-url https://api.deepseek.com --key-env DEEPSEEK_API_KEY --instance SEEDL4p80s3 --data-dir seed_L4p80_s3 --max-output-tokens 128000 --tag rep2 --out runs_repeat
ls runs_repeat/*PROMPT_SEED_L4_s4_A__rep1.txt >/dev/null 2>&1 && echo "skip 26 L4 s4 rep1" || \
  python3 run_deepseek.py --prompt prompts_v2/PROMPT_SEED_L4_s4_A.txt --model deepseek-v4-pro --base-url https://api.deepseek.com --key-env DEEPSEEK_API_KEY --instance SEEDL4s4 --data-dir seed_L4_s4 --max-output-tokens 128000 --tag rep1 --out runs_repeat
ls runs_repeat/*PROMPT_SEED_L4p80_s6_A__rep1.txt >/dev/null 2>&1 && echo "skip 27 L4p80 s6 rep1" || \
  python3 run_deepseek.py --prompt prompts_v2/PROMPT_SEED_L4p80_s6_A.txt --model deepseek-v4-pro --base-url https://api.deepseek.com --key-env DEEPSEEK_API_KEY --instance SEEDL4p80s6 --data-dir seed_L4p80_s6 --max-output-tokens 128000 --tag rep1 --out runs_repeat
ls runs_repeat/*PROMPT_SEED_L4_s8_A__rep2.txt >/dev/null 2>&1 && echo "skip 28 L4 s8 rep2" || \
  python3 run_deepseek.py --prompt prompts_v2/PROMPT_SEED_L4_s8_A.txt --model deepseek-v4-pro --base-url https://api.deepseek.com --key-env DEEPSEEK_API_KEY --instance SEEDL4s8 --data-dir seed_L4_s8 --max-output-tokens 128000 --tag rep2 --out runs_repeat
ls runs_repeat/*PROMPT_SEED_L4_s2_A__rep1.txt >/dev/null 2>&1 && echo "skip 29 L4 s2 rep1" || \
  python3 run_deepseek.py --prompt prompts_v2/PROMPT_SEED_L4_s2_A.txt --model deepseek-v4-pro --base-url https://api.deepseek.com --key-env DEEPSEEK_API_KEY --instance SEEDL4s2 --data-dir seed_L4_s2 --max-output-tokens 128000 --tag rep1 --out runs_repeat
ls runs_repeat/*PROMPT_SEED_L4p80_s1_A__rep2.txt >/dev/null 2>&1 && echo "skip 30 L4p80 s1 rep2" || \
  python3 run_deepseek.py --prompt prompts_v2/PROMPT_SEED_L4p80_s1_A.txt --model deepseek-v4-pro --base-url https://api.deepseek.com --key-env DEEPSEEK_API_KEY --instance SEEDL4p80s1 --data-dir seed_L4p80_s1 --max-output-tokens 128000 --tag rep2 --out runs_repeat
echo "done: send me the runs_repeat folder (no keys are stored in it)."
