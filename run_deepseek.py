#!/usr/bin/env python3
"""
Same job as run_openai.py, but for any OpenAI-compatible Chat Completions API (e.g. DeepSeek).

Setup (once, in a SECOND terminal window):
  pip install openai
  export DEEPSEEK_API_KEY="..."                      # Windows PowerShell:  $env:DEEPSEEK_API_KEY="..."

Example:
  python3 run_deepseek.py --prompt prompts_v2/PROMPT_LADDER_L3_A.txt --model deepseek-reasoner --instance LAD3_joins --data-dir ladder_L3 --tag ds1

Check the exact model name and the maximum output tokens on the provider's documentation page; I cannot verify them.
"""
import argparse, json, os, subprocess, sys, time
ap = argparse.ArgumentParser()
ap.add_argument("--prompt", required=True)
ap.add_argument("--model", required=True)
ap.add_argument("--base-url", default="https://api.deepseek.com")
ap.add_argument("--key-env", default="DEEPSEEK_API_KEY")
ap.add_argument("--max-output-tokens", type=int, default=32000)
ap.add_argument("--instance", default="")
ap.add_argument("--data-dir", default=".")
ap.add_argument("--entity-format", default="A")
ap.add_argument("--out", default="runs")
ap.add_argument("--tag", default="")
a = ap.parse_args()

from openai import OpenAI
client = OpenAI(api_key=os.environ[a.key_env], base_url=a.base_url)
prompt = open(a.prompt, encoding="utf-8").read()
t0 = time.time()
r = client.chat.completions.create(model=a.model, messages=[{"role": "user", "content": prompt}], max_tokens=a.max_output_tokens)
secs = round(time.time() - t0, 1)
ch = r.choices[0]; text = ch.message.content or ""
u = r.usage; det = getattr(u, "completion_tokens_details", None)
meta = dict(model=a.model, base_url=a.base_url, prompt_file=a.prompt, tag=a.tag, seconds=secs, finish_reason=ch.finish_reason,
            input_tokens=getattr(u, "prompt_tokens", None), output_tokens=getattr(u, "completion_tokens", None),
            reasoning_tokens=getattr(det, "reasoning_tokens", None), has_reasoning_text=bool(getattr(ch.message, "reasoning_content", None)),
            max_output_tokens=a.max_output_tokens, sent_utc=time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()))
os.makedirs(a.out, exist_ok=True)
base = os.path.join(a.out, f"{a.model.replace('/', '_')}__{os.path.basename(a.prompt)[:-4]}{('__' + a.tag) if a.tag else ''}")
open(base + ".txt", "w", encoding="utf-8").write(text); json.dump(meta, open(base + ".json", "w"), indent=1)
rt = getattr(ch.message, "reasoning_content", None)
if rt: open(base + "__reasoning.txt", "w", encoding="utf-8").write(rt); print("reasoning saved:", base + "__reasoning.txt")
print(json.dumps(meta, indent=1)); print("answer saved:", base + ".txt")
if meta["finish_reason"] == "length": print("WARNING: finish_reason=length -> the answer was cut off by the output cap")
if a.instance:
    subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), "score_responses.py"), "--one", "--model", a.model,
                    "--instance", a.instance, "--format", a.entity_format, "--file", base + ".txt", "--data-dir", a.data_dir])
