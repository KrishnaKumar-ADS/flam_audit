# Part C Results — Provenance, Results, and Review Status

## Purpose and status

This directory contains the archived 120-case baseline/candidate comparison, automated Gemma judgments, the blinded review sheet, and the unblinding key. Preserve the original files for traceability.

**Provenance warning:** the archived run used `gemma4:31b-cloud` through Ollama Cloud for generation and the same model for automated judging. The assignment states that there is no external API budget. Unless an explicit exception was granted, this historical run is a disclosed deviation; it was not a local A100 run. Do not rerun the cloud configuration without authorization.

## Archived run

- Languages: Hindi (`hin`), Kannada (`kan`), Tamil (`tam`), Telugu (`tel`), Bengali (`ben`), Marathi (`mar`).
- Cases: 20 per language; 120 baseline/candidate pairs and 240 responses total.
- Automated judge records: 120.
- Generator and judge: `gemma4:31b-cloud` (same model; self-evaluation and position bias are possible).
- Submitter review: the submitter reports personally inspecting all 120 cases. The `review_sheet.csv` records this in `reviewer` and `verification_status`, but individual ratings and notes were not recorded. Consequently, this is not a structured human preference evaluation, and no human win rate or agreement statistic can be calculated.

## Automated preference results

| Language | Cases | A preferred | B preferred | Ties | B preference among non-ties |
|---|---:|---:|---:|---:|---:|
| Hindi | 20 | 5 | 13 | 2 | 72.2% |
| Kannada | 20 | 5 | 13 | 2 | 72.2% |
| Tamil | 20 | 5 | 15 | 0 | 75.0% |
| Telugu | 20 | 5 | 14 | 1 | 73.7% |
| Bengali | 20 | 2 | 10 | 8 | 83.3% |
| Marathi | 20 | 7 | 11 | 2 | 61.1% |
| **Overall** | **120** | **29** | **76** | **15** | **72.4%** |

`B preference = 76 / (76 + 29) = 72.4%`. This is a **presentation-slot** result, not the candidate win rate. The candidate/baseline assignment changes between A and B by case, so use `unblind_key.csv` to interpret preference after unblinding.

### After unblinding

| Language | Cases | Candidate wins | Baseline wins | Ties | Candidate preference among non-ties |
|---|---:|---:|---:|---:|---:|
| Hindi | 20 | 11 | 7 | 2 | 61.1% |
| Kannada | 20 | 7 | 11 | 2 | 38.9% |
| Tamil | 20 | 7 | 13 | 0 | 35.0% |
| Telugu | 20 | 7 | 12 | 1 | 36.8% |
| Bengali | 20 | 3 | 9 | 8 | 25.0% |
| Marathi | 20 | 10 | 8 | 2 | 55.6% |
| **Overall** | **120** | **45** | **60** | **15** | **42.9%** |

`Candidate preference = 45 / (45 + 60) = 42.9%`. These are exploratory automated judgments from small samples, not population estimates. They do not support launching the current candidate.

## Meaning and safety labels

The automated judge marked meaning preserved for A in 119/120 cases and B in 120/120, and safety preserved for both slots in 120/120. These are judge-generated labels—not independently verified correctness or safety rates. Do not describe them as proof of perfect meaning preservation or safety.

## File inventory

- `model_outputs.csv` — archived baseline/candidate response pairs. Use its header row as the source of truth.
- `model_outputs_template.csv` — template only, not measured output.
- `gemma_judge_review.csv` — structured automated judgments.
- `gemma_judge_raw.jsonl` — raw model-generated judge outputs; not verified explanations.
- `gemma_judge_by_language.csv` — automated slot-preference aggregation.
- `review_sheet.csv` — blinded review form, with submitter self-review status recorded but no individual structured ratings.
- `review_sheet.manifest.json` — metadata for the review sheet.
- `unblind_key.csv` — maps A/B to candidate/baseline. Keep separate from any fresh blinded review packet.

## What the evidence supports

1. **Execution completeness:** 120 automated judge records are present.
2. **Submitter self-review:** the submitter reports inspecting all 120 cases; individual ratings were not recorded in the sheet.
3. **Qualified linguistic validation:** not established for all six languages. The staffing plan provides native review only for Hindi and Kannada.
4. **Launch decision:** retain the baseline. Run a new local, blinded evaluation with structured ratings before considering a prompt candidate for launch.

## Human-review protocol for a new experiment

1. Run permitted local inference only; record actual model IDs, versions, timestamps, prompt/config hashes, and output paths.
2. Freeze the candidate, baseline, test set, rubric, and analysis plan before review.
3. Randomize A/B order and conceal condition labels. Keep `unblind_key.csv` separate from the reviewer packet.
4. Obtain structured per-case naturalness preference, meaning-preservation, safety, and notes from a qualified reviewer. Do not copy automated labels into human-rating columns.
5. Freeze and timestamp ratings before unblinding. Report counts, ties, and non-tie denominators by language.
6. If qualified review is unavailable, mark the launch gate pending and retain the baseline.

## Safe reporting language

> “The archived 120-case comparison used `gemma4:31b-cloud` for generation and the same model for automated judging. Slot B was preferred in 76 of 105 non-tied judgments (72.4%), but this is not candidate preference. After unblinding, the candidate won 45 cases, the baseline won 60, and 15 tied, so candidate preference among non-ties was 42.9%. The submitter reports personally inspecting all 120 cases, but structured individual human ratings were not recorded. The cloud run deviated from the zero-external-API-budget constraint unless an exception was authorized. The evidence does not support launching the current candidate.”
