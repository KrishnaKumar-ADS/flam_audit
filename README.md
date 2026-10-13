# FLAM — The Audit

## 1. Purpose and status

This repository contains the take-home audit work for **The Audit** assignment. It investigates whether the supplied tokenizer-fertility analysis and serving-throughput conclusions are reliable, then proposes a constrained experiment for improving the conversational style of multilingual responses.

The package separates four kinds of evidence:

1. **Source inspection** — what the supplied code, benchmark specification, and benchmark log say.
2. **Controlled tests** — small deterministic tests used to isolate specific code/metric behaviors.
3. **Measured outputs** — outputs produced by running actual tokenizers or the documented model pipeline.
4. **Proposals and pending gates** — thresholds and experiments proposed for a future decision; these are not results unless an actual run is recorded.

Do not interpret a file being present as proof that every proposed experiment has been run. In particular, the Part C cloud run is an actual automated experiment, but it is **not** independent human validation and it does not satisfy a strict no-external-API constraint without an explicit exception.

## 2. Current evidence at a glance

### Part A — Tokenizer audit

- The probe corpus contains **20 aligned sentence IDs in each of seven languages**: English (`eng`), Hindi (`hin`), Kannada (`kan`), Tamil (`tam`), Telugu (`tel`), Bengali (`ben`), and Marathi (`mar`). This is 140 sentence strings total.
- The corpus is a small, author-created general-domain probe. Its translations have **not been independently validated by native speakers**. It is not FLORES and is not a production benchmark.
- The actual tokenizer comparison was run using GPT-2 (`tiktoken`) and XLM-R (`xlm-roberta-base`). `partA/results/tokenizer_metrics.csv` contains per-case measurements; `partA/results/tokenizer_summary.csv` contains summary values.
- Pooled tokens per whitespace-delimited word from the recorded run:

| Language | GPT-2 | XLM-R |
|---|---:|---:|
| English | 1.1837 | 1.2517 |
| Hindi | 7.2667 | 1.2970 |
| Kannada | 21.4434 | 2.1321 |
| Tamil | 24.9907 | 2.2222 |
| Telugu | 19.9561 | 2.1667 |
| Bengali | 11.7787 | 1.8770 |
| Marathi | 9.4252 | 1.7323 |

These values describe tokenizer behavior on this specific corpus and denominator. They do **not** directly establish API price, production token volume, quality, or a routing policy. Tokenizers can be compared under multiple denominators, but the denominator must be named and interpreted explicitly.

The controlled audit identifies problems in the starter metric: splitting on a literal single space can count empty fields when repeated spaces occur; Python string length counts Unicode code points rather than grapheme clusters; and an unweighted mean of per-line ratios can differ from a pooled ratio. The presence of `random.seed(1337)` is not by itself a demonstrated bug because the inspected script does not use randomness. See `partA/scripts/audit_fertility.py` for controlled tests and `partA/memo.md` for interpretation.

### Part B — Capacity and throughput

The analysis uses the supplied model specification and benchmark log. It is a **reconciliation of provided measurements**, not a new GPU benchmark.

- KV-cache bytes per token: `2 × 28 layers × 8 KV heads × 128 head_dim × 2 bytes = 114,688 bytes`, equal to 112 KiB/token.
- A 4,096-token sequence uses 469,762,048 bytes, or 448 MiB, for KV cache under the stated assumptions.
- The memory-based concurrency estimate is approximate and depends on how GPU memory, runtime overhead, and utilization are interpreted. The estimate is not a guaranteed scheduler limit.
- For the 3,584-input/512-output workload, the logged aggregate token rate includes prompt **and** generated tokens. Batch 24 reports 1,607.4 combined tokens/s, while generated-output-only goodput is approximately `24 × 512 / 61.16 = 200.8 output tokens/s`.
- Long-prompt throughput peaks at batch 24 in the supplied rows. At batches 32 and 48, throughput declines and preemptions are recorded; this is consistent with KV-cache pressure, but the log alone does not prove that cache pressure is the sole cause.

See `partB/memo.md`, `partB/Conclusion.md`, `partB/model_spec.md`, `partB/bench_log.csv`, and `partB/reconcile.py` where present. The original `REPORT_v0.md` is preserved as source evidence; its claims should not be mistaken for the corrected conclusion.

### Part C — Conversational multilingual responses

The archived run generated 120 baseline/candidate pairs (20 cases per language for Hindi, Kannada, Tamil, Telugu, Bengali, and Marathi) using `gemma4:31b-cloud` through Ollama Cloud. The **same model** then judged the pairs.

| Language | Cases | Slot A preferred | Slot B preferred | Ties | Slot B preference among non-ties | Unblinded Candidate Win Rate |
|---|---:|---:|---:|---:|---:|---:|
| Hindi | 20 | 5 | 13 | 2 | 72.2% | **61.1%** (11 vs 7) |
| Kannada | 20 | 5 | 13 | 2 | 72.2% | **38.9%** (7 vs 11) |
| Tamil | 20 | 5 | 15 | 0 | 75.0% | **35.0%** (7 vs 13) |
| Telugu | 20 | 5 | 14 | 1 | 73.7% | **36.8%** (7 vs 12) |
| Bengali | 20 | 2 | 10 | 8 | 83.3% | **25.0%** (3 vs 9) |
| Marathi | 20 | 7 | 11 | 2 | 61.1% | **55.6%** (10 vs 8) |
| **Overall** | **120** | **29** | **76** | **15** | **72.4%** | **42.9%** (45 vs 60) |

**Critical audit finding:** The 72.4% figure was entirely an artifact of **severe LLM judge position bias towards Slot B** (76 B vs 29 A). When unblinded using `unblind_key.csv`, the candidate prompt actually achieved only **42.9% non-tied preference** (45 candidate wins vs 60 baseline wins, 15 ties). Every single language failed the 70% threshold.

The judge marked meaning preservation for A in 119/120 cases and for B in 120/120; safety preservation was marked YES for both A and B in 120/120 cases. These are **the judge's automated labels**, not independently verified correctness or safety rates. The blinded `review_sheet.csv` has blank reviewer-rating fields. **Human review is pending.** No completed human-review pass is claimed.

The run used a cloud model even though the assignment states there is no external API budget. This is disclosed as a constraint deviation. Do not describe this archived run as local or as compliant with a strict local-only/no-external-API requirement.

## 3. Repository map

- `NOTEBOOK.md` — chronological record of hypotheses, tests, actual runs, revisions, dead ends, and pending work.
- `AI_USAGE.md` — disclosure of AI assistance, AI-created corpus material, cloud inference, position bias catch, and live defense readiness.
- `tests/test_all.py` — deterministic unit test suite (56 tests) verifying all Part A, B, and C formulas and counts.
- `partA/corpus/` — the seven-language probe and its manifest.
- `partA/scripts/audit_fertility.py` — controlled tests for the starter metric's behavior.
- `partA/scripts/compare_tokenizers.py` — actual GPT-2/XLM-R tokenizer comparison script.
- `partA/results/` — tokenizer measurements and summary outputs.
- `partA/memo.md` — Part A findings, caveats, and recommendation.
- `partB/` — capacity calculations, throughput reconciliation, supporting inputs, and memo.
- `partC/memo.md` — proposed experiment, back-of-envelope arithmetic, and decision gates.
- `partC/scripts/` — generation, judging, and evaluation-harness scripts.
- `partC/results/model_outputs.csv` — archived generated baseline/candidate responses.
- `partC/results/gemma_judge_review.csv` and `gemma_judge_raw.jsonl` — archived automated judgments and raw judge outputs.
- `partC/results/gemma_judge_by_language.csv` — per-language automated summary.
- `partC/results/review_sheet.csv` — blinded review template with blank reviewer fields in the archived run.
- `partC/results/unblind_key.csv` — mapping from A/B labels to conditions. Keep this separate from any new reviewer packet.

## 4. Setup

Run commands from the **submission directory** (`your-submission`):

```powershell
Set-Location "your-submission"
python --version
```

If a virtual environment has already been activated, use its `python`. Dependencies for tests are standard library only; tokenizer scripts require `tiktoken`, `transformers`, `sentencepiece`, and `regex`.

To execute the deterministic test suite:
```powershell
python tests/test_all.py
# or: python -m pytest tests/test_all.py -v
```

## 5. Reproducing Part A

From `your-submission`:

```powershell
python partA/scripts/audit_fertility.py
python partA/scripts/compare_tokenizers.py
```

Keep the actual generated `partA/results/tokenizer_metrics.csv` and `partA/results/tokenizer_summary.csv`. Record the command, date, tokenizer identifiers, corpus revision, and output paths in `NOTEBOOK.md` when rerunning. A rerun should update evidence only when it actually completes; do not edit measured values by hand to match this README.

## 6. Reproducing Part B

The Part B analysis reconciles the supplied benchmark log and model specification. It does not require a new GPU run to recompute the arithmetic. Follow the invocation documented in the relevant script or memo, and retain the exact input log and model specification alongside the output. If any input row or unit changes, recompute the result rather than reusing the values above.

## 7. Part C: current artifacts and compliant next steps

The archived cloud results are retained for transparency and exploratory diagnosis. They should not be silently overwritten or relabeled as local results.

Before a new run:

1. Read `AI_USAGE.md` and `partC/results/README.md`.
2. Check the assignment's no-external-API rule. Unless an explicit exception has been granted, do not use `gemma4:31b-cloud` or another cloud endpoint.
3. Confirm that the selected generation and judge models are installed locally and that the scripts' actual defaults match the intended configuration. Record the model IDs in a run manifest.
4. Keep each run's output in distinct files/directories so cloud-origin and local-origin artifacts cannot be confused.
5. Treat an AI judge as supplementary screening. It is not a native-speaker reviewer, and using a different judge model does not itself prove linguistic correctness.
6. If a human review is required, use a genuinely blinded review process with qualified reviewers, keep the unblinding key private until ratings are frozen, and report the human results separately. If qualified review cannot be obtained, state that the human gate remains unmet.

The Part C memo's proposed Day-7 thresholds are **proposed gates**, not achieved outcomes: at least 70% candidate preference among non-ties in each reviewed language, with meaning and safety preserved in at least 95% of reviewed answers; revert if either priority language is below 60% after at least 30 valid comparisons or a material regression appears. The existing 20-case-per-language cloud self-judging run does not satisfy the proposed 30-comparison human-review gate.

## 8. Evidence and integrity rules

- Preserve raw inputs, commands, model identifiers, logs, outputs, and dates for each actual run.
- Label synthetic micro-tests as synthetic tests of code behavior; do not present them as corpus-level tokenizer results.
- Label the Part B results as calculations against the supplied benchmark log, not as a newly executed GPU benchmark.
- Label the Part C results as cloud-generated and same-model-judged automated screening.
- Do not invent missing human scores or convert a blank review sheet into a completed evaluation.
- Do not claim a proposed threshold passed until the required experiment and valid denominator exist.
- Ensure the final ZIP includes the latest reports generated on the working machine, then inspect the ZIP contents before submitting.

## 9. Final readiness checklist

- [ ] `NOTEBOOK.md` is chronological and distinguishes actual work from proposed/pending work.
- [ ] `AI_USAGE.md` describes AI assistance, AI-generated corpus translations, and cloud inference accurately.
- [ ] Part A numbers match the checked-in CSV outputs and memo.
- [ ] Part B arithmetic and throughput denominators match the supplied benchmark rows.
- [ ] Part C cloud results are labeled exploratory automated self-evaluation.
- [ ] The human-review status is stated honestly; blank fields are not represented as reviews.
- [ ] Any local rerun is genuinely local, uses documented model IDs, and has separate artifacts.
- [ ] The no-external-API constraint and any exception are addressed explicitly.
- [ ] The final ZIP contains the updated README files and all referenced evidence files.
- [ ] You can explain the key formulas, denominators, assumptions, and limitations in the live defense.

## 10. Bottom line

This submission's strongest claim is that it audits metrics and benchmark interpretation with explicit arithmetic and controlled tests. Its Part C cloud run provides preliminary automated screening, not independent validation. Keep that distinction visible throughout the repository. A careful, reproducible limitation is stronger than a result described as more conclusive than the evidence supports.
