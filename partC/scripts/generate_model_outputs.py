"""Generate a fresh baseline/candidate set through Ollama using the originally specified model; cloud use is explicitly gated.

Defaults to the originally used Gemma Cloud model. Cloud use requires explicit opt-in and is not compliant with the assignment budget constraint.
Existing cloud outputs are preserved in model_outputs.csv; this script writes
model_outputs_local.csv and never reuses the cloud file.
"""
import csv, hashlib, json, os, sys, time, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORPUS = os.path.join(os.path.dirname(ROOT), "partA", "corpus", "parallel_corpus.csv")
RESULTS = os.path.join(ROOT, "results")
OUTPUT = os.path.join(RESULTS, "model_outputs_local.csv")
ERRORS = os.path.join(RESULTS, "generation_errors_local.csv")
MODEL = os.environ.get("FLAM_GENERATION_MODEL", "gemma4:31b-cloud")
API = os.environ.get("OLLAMA_API", "http://localhost:11434")
LANGUAGES = {"hin":"Hindi", "kan":"Kannada", "tam":"Tamil", "tel":"Telugu", "ben":"Bengali", "mar":"Marathi"}
FIELDS = ["case_id", "language", "prompt", "baseline_output", "candidate_output", "generation_model", "evaluation_provenance"]
BASELINE_SYSTEM = ("You are a helpful assistant. Respond in the same language as the user's message. "
                   "Keep the response relevant and concise.")
CANDIDATE_SYSTEM = ("You are a helpful assistant. Respond in the same language as the user's message. "
                    "Use a natural, warm, conversational tone, as if speaking helpfully to a person. "
                    "Be clear and concise. Preserve meaning and do not invent personal details or unsupported facts.")

def local_model_check(model):
    if "cloud" in model.lower() or ":cloud" in model.lower():
        if os.environ.get("FLAM_ALLOW_CLOUD", "").lower() != "true":
            raise SystemExit(f"{model!r} uses cloud inference and violates the no-external-API-budget assumption. Set FLAM_ALLOW_CLOUD=true only if explicitly authorized and cost/data handling are accepted.")
        print("WARNING: cloud inference explicitly enabled; this run is not compliant with a strict no-external-API-budget constraint.")
    req = urllib.request.Request(API.rstrip("/") + "/api/tags")
    with urllib.request.urlopen(req, timeout=10) as response:
        tags = json.loads(response.read().decode("utf-8")).get("models", [])
    installed = {m.get("name", "") for m in tags}
    if model not in installed:
        raise SystemExit(f"Local model {model!r} is not installed in Ollama. Install it locally first; no cloud fallback is allowed. Installed: {', '.join(sorted(installed)) or '(none)'}")

def call_model(prompt, system):
    payload = {"model": MODEL, "stream": False, "messages": [
        {"role":"system", "content":system}, {"role":"user", "content":prompt}],
        "options":{"temperature":0.2}}
    req = urllib.request.Request(API.rstrip("/") + "/api/chat", data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                                 headers={"Content-Type":"application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=600) as response:
        result = json.loads(response.read().decode("utf-8"))
    text = result.get("message", {}).get("content", "").strip()
    if not text: raise RuntimeError("Model returned an empty response")
    return text

def save_csv(path, rows, fields):
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields); writer.writeheader(); writer.writerows(rows)

def main():
    if not os.path.isfile(CORPUS): raise SystemExit(f"Corpus not found: {CORPUS}")
    local_model_check(MODEL)
    os.makedirs(RESULTS, exist_ok=True)
    with open(CORPUS, newline="", encoding="utf-8-sig") as f: corpus = list(csv.DictReader(f))
    if not corpus: raise SystemExit("Corpus is empty")
    expected = len(corpus) * len(LANGUAGES)
    print(f"Local generation model: {MODEL}\nCases: {expected}; up to {expected*2} local calls\nOutput: {OUTPUT}")
    rows_by_id = {}
    if os.path.exists(OUTPUT):
        with open(OUTPUT, newline="", encoding="utf-8-sig") as f: rows_by_id = {r["case_id"]:r for r in csv.DictReader(f)}
    errors=[]
    for item in corpus:
        sid=item["sentence_id"].strip()
        for lang in LANGUAGES:
            cid=f"{sid}-{lang}"; prompt=item.get(lang, "").strip(); old=rows_by_id.get(cid)
            if old and old.get("baseline_output", "").strip() and old.get("candidate_output", "").strip(): continue
            if not prompt:
                errors.append({"case_id":cid,"language":lang,"stage":"input","error":"Empty corpus prompt"}); continue
            row={"case_id":cid,"language":lang,"prompt":prompt,"baseline_output":"","candidate_output":"",
                 "generation_model":MODEL,"evaluation_provenance":"local_ollama_no_external_api"}
            try:
                row["baseline_output"]=call_model(prompt, BASELINE_SYSTEM)
                row["candidate_output"]=call_model(prompt, CANDIDATE_SYSTEM)
                rows_by_id[cid]=row; save_csv(OUTPUT, list(rows_by_id.values()), FIELDS)
                print(f"Saved {cid} ({len(rows_by_id)}/{expected})"); time.sleep(0.1)
            except Exception as exc:
                errors.append({"case_id":cid,"language":lang,"stage":"generation","error":str(exc)})
                save_csv(OUTPUT,list(rows_by_id.values()),FIELDS)
                save_csv(ERRORS,errors,["case_id","language","stage","error"])
                raise SystemExit(f"Failed at {cid}; progress saved, rerun to resume: {exc}")
    save_csv(OUTPUT,list(rows_by_id.values()),FIELDS)
    if errors: save_csv(ERRORS,errors,["case_id","language","stage","error"])
    corpus_hash=hashlib.sha256(open(CORPUS,"rb").read()).hexdigest()
    with open(os.path.join(RESULTS,"local_generation_manifest.json"),"w",encoding="utf-8") as f:
        json.dump({"model":MODEL,"endpoint":API,"provenance":("Ollama Cloud; explicit opt-in; external service used" if "cloud" in MODEL.lower() else "local Ollama only; no external API"),
                   "corpus_path":"partA/corpus/parallel_corpus.csv","corpus_sha256":corpus_hash,
                   "expected_cases":expected,"completed_cases":len(rows_by_id),"output":"model_outputs_local.csv"},f,indent=2)
    print(f"Done: {len(rows_by_id)}/{expected}. This is generated output, not human validation.")
if __name__ == "__main__": main()
