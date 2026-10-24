#!/usr/bin/env python3
"""
Send one prompt file to the Gemini API, save answer + metadata (same layout as run_openai.py), optionally score it.
  pip install google-genai        export GEMINI_API_KEY=...   (your own terminal only)
  python3 run_gemini.py --prompt prompts_v2/PROMPT_SEED_L4p80_s1_A.txt --model MODEL_ID --effort high \
          --instance SEEDL4p80s1 --data-dir seed_L4p80_s1 --tag m1
Temperature is NOT set (Google recommends the default 1.0 for Gemini 3 reasoning; lower values can loop). Seed is not set.
--effort  high | low | none   -> thinking_level for Gemini 3 models; for 2.5 models: high = dynamic budget, low = 1024 tokens;
          none = send no thinking setting (model default).
"""
import argparse, json, os, subprocess, sys, time
ap = argparse.ArgumentParser()
ap.add_argument("--prompt", required=True); ap.add_argument("--model", required=True)
ap.add_argument("--effort", default="high", choices=["none", "low", "medium", "high"])
ap.add_argument("--max-output-tokens", type=int, default=64000)
ap.add_argument("--instance", default=""); ap.add_argument("--data-dir", default=".")
ap.add_argument("--entity-format", default="A"); ap.add_argument("--out", default="runs"); ap.add_argument("--tag", default="")
ap.add_argument("--retries", type=int, default=3, help="retries on rate-limit/overload errors (each retry is logged in the metadata)")
a = ap.parse_args()
from google import genai
from google.genai import types
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY"))
prompt = open(a.prompt, encoding="utf-8").read()
cfg = dict(max_output_tokens=a.max_output_tokens)
effort_applied = "model default (no thinking setting sent)"
if a.effort != "none":
    fields = getattr(types.ThinkingConfig, "model_fields", {})
    if "2.5" in a.model and "thinking_budget" in fields:
        cfg["thinking_config"] = types.ThinkingConfig(thinking_budget=(-1 if a.effort == "high" else 1024)); effort_applied = a.effort
    elif "thinking_level" in fields:
        cfg["thinking_config"] = types.ThinkingConfig(thinking_level=a.effort); effort_applied = a.effort
    else:
        print("WARNING: installed google-genai is too old for thinking_level; sending no thinking setting (Gemini 3 default is high per Google's launch guide). Upgrade: python3 -m pip install -U google-genai")
base = os.path.join(a.out, f"{a.model.replace('/', '_')}__{a.effort}__{os.path.basename(a.prompt)[:-4]}{('__' + a.tag) if a.tag else ''}")
os.makedirs(a.out, exist_ok=True)
t0 = time.time(); err = ""; r = None; attempts = 0; errs = []
while attempts <= a.retries:
    attempts += 1
    try:
        r = client.models.generate_content(model=a.model, contents=prompt, config=types.GenerateContentConfig(**cfg)); err = ""; break
    except Exception as e:
        err = f"{type(e).__name__}: {e}"; errs.append(err)
        if any(k in err for k in ("429", "503", "500", "UNAVAILABLE", "RESOURCE_EXHAUSTED")) and attempts <= a.retries: time.sleep(60 * attempts); continue
        break
secs = round(time.time() - t0, 1)
if r is None:
    json.dump(dict(model=a.model, effort=a.effort, prompt_file=a.prompt, tag=a.tag, seconds=secs, api_error=err, attempts=attempts,
                   sent_utc=time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())), open(base + ".error.json", "w"), indent=1)
    print("API ERROR:", err); sys.exit(1)
try: text = r.text or ""
except Exception: text = ""
u = r.usage_metadata; cand = r.candidates[0] if r.candidates else None
fin = str(getattr(cand, "finish_reason", "")) if cand else "NO_CANDIDATE"
meta = dict(model=a.model, model_returned_by_api=getattr(r, "model_version", ""), response_id=getattr(r, "response_id", ""), provider="google",
            effort=a.effort, effort_applied=effort_applied, temperature="not set (provider default)", max_output_tokens=a.max_output_tokens, seed="not set",
            finish_reason=fin, truncated=("MAX_TOKENS" in fin), empty_output=(not text.strip()),
            blocked=str(getattr(r, "prompt_feedback", "") or ""), prompt_file=a.prompt, tag=a.tag, seconds=secs, attempts=attempts, earlier_errors=errs,
            status=("incomplete" if "MAX_TOKENS" in fin else "completed" if text.strip() else "empty"),
            input_tokens=getattr(u, "prompt_token_count", None), output_tokens=getattr(u, "candidates_token_count", None),
            reasoning_tokens=getattr(u, "thoughts_token_count", None), sent_utc=time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()))
open(base + ".txt", "w", encoding="utf-8").write(text)
json.dump(meta, open(base + ".json", "w"), indent=1)
print(json.dumps(meta, indent=1)); print("answer saved:", base + ".txt")
if a.instance:
    subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), "score_responses.py"),
                    "--one", "--model", f"{a.model}_{a.effort}", "--instance", a.instance, "--format", a.entity_format,
                    "--file", base + ".txt", "--data-dir", a.data_dir])
