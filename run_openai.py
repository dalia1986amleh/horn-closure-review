#!/usr/bin/env python3
"""
Send one prompt file to the OpenAI API, save the answer + metadata, optionally score it.

Setup (once):   pip install openai          and         export OPENAI_API_KEY=sk-...        (Windows: set OPENAI_API_KEY=sk-...)

Example:
  python3 run_openai.py --prompt prompts_v2/PROMPT_A_d8_b4_01_A.txt --model YOUR_MODEL_NAME --effort high \
          --instance A_d8_b4_01 --data-dir . --out runs/

--model   the exact model name from your OpenAI account (I cannot verify current names, so check your dashboard)
--effort  reasoning effort: minimal | low | medium | high   ('minimal' = least reasoning; 'none' only OMITS the setting, so the model uses its default and may still reason)
Each call is billed: input is small (2k-23k characters), most of the cost is the model's hidden reasoning + answer.
Use --max-output-tokens as a cost cap (a truncated answer is flagged in the metadata).
"""
import argparse, json, os, subprocess, sys, time

ap = argparse.ArgumentParser()
ap.add_argument("--prompt", required=True)
ap.add_argument("--model", required=True)
ap.add_argument("--effort", default="high", choices=["none", "minimal", "low", "medium", "high"])
ap.add_argument("--max-output-tokens", type=int, default=60000)
ap.add_argument("--instance", default="", help="instance id; if given, the answer is scored right after")
ap.add_argument("--data-dir", default=".")
ap.add_argument("--entity-format", default="A")
ap.add_argument("--out", default="runs")
ap.add_argument("--tag", default="", help="free label, e.g. run number")
a = ap.parse_args()

from openai import OpenAI
client = OpenAI()                                   # reads OPENAI_API_KEY
prompt = open(a.prompt, encoding="utf-8").read()
kw = dict(model=a.model, input=prompt, max_output_tokens=a.max_output_tokens)
if a.effort != "none":
    kw["reasoning"] = {"effort": a.effort}

t0 = time.time()
err = ""
try:
    r = client.responses.create(**kw)
except Exception as e:                               # log API errors instead of losing them
    r = None; err = f"{type(e).__name__}: {e}"
secs = round(time.time() - t0, 1)
if r is None:
    os.makedirs(a.out, exist_ok=True)
    base = os.path.join(a.out, f"{a.model.replace('/', '_')}__{a.effort}__{os.path.basename(a.prompt)[:-4]}{('__' + a.tag) if a.tag else ''}")
    json.dump(dict(model=a.model, effort=a.effort, prompt_file=a.prompt, tag=a.tag, seconds=secs, api_error=err,
                   sent_utc=time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())), open(base + ".error.json", "w"), indent=1)
    print("API ERROR:", err); sys.exit(1)

text = r.output_text or ""
u = getattr(r, "usage", None)
meta = dict(model=a.model, model_returned_by_api=getattr(r, "model", ""), response_id=getattr(r, "id", ""), provider="openai",
            effort=a.effort, temperature="not set (reasoning models fix it)", max_output_tokens=a.max_output_tokens,
            seed="not supported by the Responses API", truncated=(getattr(r, "status", "") == "incomplete"),
            empty_output=(not text.strip()), refusal=any(getattr(c, "type", "") == "refusal" for o in getattr(r, "output", []) for c in (getattr(o, "content", None) or [])), prompt_file=a.prompt, tag=a.tag, seconds=secs,
            status=getattr(r, "status", ""), incomplete=str(getattr(r, "incomplete_details", "")),
            input_tokens=getattr(u, "input_tokens", None), output_tokens=getattr(u, "output_tokens", None),
            reasoning_tokens=getattr(getattr(u, "output_tokens_details", None), "reasoning_tokens", None),
            sent_utc=time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()))
os.makedirs(a.out, exist_ok=True)
base = os.path.join(a.out, f"{a.model.replace('/', '_')}__{a.effort}__{os.path.basename(a.prompt)[:-4]}{('__' + a.tag) if a.tag else ''}")
open(base + ".txt", "w", encoding="utf-8").write(text)
json.dump(meta, open(base + ".json", "w"), indent=1)
print(json.dumps(meta, indent=1)); print("answer saved:", base + ".txt")

if a.instance:                                       # score immediately with the same scorer used so far
    subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), "score_responses.py"),
                    "--one", "--model", f"{a.model}_{a.effort}", "--instance", a.instance, "--format", a.entity_format,
                    "--file", base + ".txt", "--data-dir", a.data_dir])
