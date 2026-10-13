# Part C — Decision Memo: Conversational Multilingual Responses

## Decision

**Do not launch the current candidate prompt. Keep the production baseline. Select Path (c), prompt engineering, only as the next reversible experiment—not as an approved launch.** The archived automated comparison does not support the candidate: after unblinding, the candidate won 45 non-tied cases and the baseline won 60; 15 cases were ties. Candidate preference was therefore **42.9% of non-tied judgments**. This was an exploratory, same-model automated evaluation, so it is directional evidence rather than a definitive quality estimate.

A new prompt candidate may be evaluated in Hindi and Kannada first, because the assignment provides one native reviewer for those two languages only. Do not launch in any language until the required qualified human review meets predeclared acceptance criteria. Tamil, Telugu, Bengali, and Marathi remain blocked until qualified native review is available.

## 1. Constraints and evidence status

- **Compute allocation in the assignment:** one NVIDIA A100 80 GB GPU for two weeks (336 GPU-hours).
- **Human review:** one native reviewer for Hindi and Kannada only, up to 10 hours/week for three weeks (30 hours total). There is no qualified reviewer coverage for Tamil, Telugu, Bengali, or Marathi in the stated plan.
- **Decision deadline:** end of Week 3 (Day 21).
- **External API budget:** zero. A strict interpretation requires new generation and evaluation to run locally. The archived Part C run used `gemma4:31b-cloud` through Ollama Cloud for both generation and judging. That run is a **disclosed deviation** from the no-external-API constraint unless an explicit exception was granted; it must not be described as local or policy-compliant.
- **Current evidence:** 120 cases, 20 per language across Hindi, Kannada, Tamil, Telugu, Bengali, and Marathi; 120 baseline/candidate pairs (240 responses); 120 automated judge records. The same model was used for generation and judging, creating a risk of self-evaluation and position bias.
- **Submitter self-review:** the submitter reports personally inspecting all 120 cases. The review sheet records this workflow, but individual naturalness preferences, 1–5 ratings, meaning/safety labels, and notes were not recorded as structured human judgments. Therefore, no human preference rate, human meaning/safety rate, inter-rater agreement, or qualified native-speaker validation rate can be calculated from the supplied sheet.

## 2. Archived automated results

The judge selected presentation slot A 29 times, slot B 76 times, and tied 15 times. The 72.4% slot-B preference (`76 / (76 + 29)`) is **not** the candidate win rate because candidate/baseline assignment to A/B varied by case. After applying `results/unblind_key.csv`:

| Language | Cases | Candidate wins | Baseline wins | Ties | Candidate preference among non-ties |
|---|---:|---:|---:|---:|---:|
| Hindi | 20 | 11 | 7 | 2 | 61.1% |
| Kannada | 20 | 7 | 11 | 2 | 38.9% |
| Tamil | 20 | 7 | 13 | 0 | 35.0% |
| Telugu | 20 | 7 | 12 | 1 | 36.8% |
| Bengali | 20 | 3 | 9 | 8 | 25.0% |
| Marathi | 20 | 10 | 8 | 2 | 55.6% |
| **Overall** | **120** | **45** | **60** | **15** | **42.9%** |

Overall candidate preference is `45 / (45 + 60) = 42.9%`. The small per-language samples and same-model judging mean these figures should be treated as exploratory signals, not population estimates. They nevertheless do **not** justify launching this candidate. The weakest results are in Bengali, Tamil, and Telugu; Kannada also favors the baseline. Hindi and Marathi results do not establish a launch-ready improvement.

The automated judge marked meaning preserved for A in 119/120 cases and B in 120/120, and safety preserved for both slots in 120/120. These are **automated labels only**, not independently established correctness or safety rates. Do not report them as proof of perfect meaning preservation or safety.

## 3. Compare the three paths

### (a) Supervised fine-tuning (SFT)

Do not choose SFT for the immediate three-week decision. It introduces training-data construction, quality control, model regression, and rollback work before the team has demonstrated that the target conversational behavior is valuable. There is no evidence in this assignment package that a particular number of examples per language is a universal minimum; any dataset-size estimate should be treated as a planning assumption and validated with a learning curve. With native review available for only two languages, a six-language SFT dataset would have a substantial quality-control gap.

### (b) Separate inference-time rewriter

Do not choose a separate rewriter for the immediate decision. It adds a second model stage and another failure point, and requires its own evaluation for semantic drift, safety, latency, and serving cost. No supplied experiment demonstrates that a rewriter beats the baseline under the current constraints.

### (c) Prompt engineering

Choose prompt engineering as the **lowest-commitment next experiment**, not as a launch approval. It requires no model fine-tuning and can be rolled back by reverting a configuration. The present candidate failed the archived exploratory comparison, so revise or discard it and run a new, properly controlled local experiment before reconsidering launch.

## 4. Resource and reviewer-capacity arithmetic

The assignment allocates 30 reviewer-hours over three weeks. If approximately 2 hours are reserved each week for calibration, rubric alignment, and fatigue breaks, the remaining 24 hours equal 1,440 minutes. At an estimated 2 minutes per blinded pair, that is a **planning capacity** of 720 comparisons. This estimate is not measured reviewer throughput and should be adjusted during calibration.

The first qualified evaluation should prioritize Hindi and Kannada. A minimum of 30 valid comparisons per language means 60 comparisons total, approximately 2 reviewer-hours at the planning rate. Preserve additional time for calibration and adjudication. The four other languages have no qualified reviewer coverage under the stated staffing plan and must remain out of scope for launch.

The A100 allocation is available for a future local experiment. It does not change the provenance of the archived cloud run. No claim is made here that the historical run was executed on the A100.

## 5. Proposed acceptance and kill criteria for the next experiment

Before collecting new ratings, freeze the candidate prompt, baseline, test cases, rubric, randomization procedure, and analysis plan. Use the qualified reviewer and keep condition labels hidden until ratings are frozen.

**Proposed acceptance gate** (decision rule, not a result already achieved):
1. Candidate naturalness preference is at least 70% of non-tied comparisons in **each** of Hindi and Kannada, with at least 30 valid comparisons per language.
2. At least 95% of candidate responses preserve meaning under the agreed review rubric.
3. No safety regression is observed in the reviewed set.

**Kill / rollback rule:** stop the candidate experiment and revert to baseline if preference is below 60% in either language after the planned minimum sample, if meaning preservation falls below 90%, or if any material safety violation is identified. Results between 60% and 70% do not pass the acceptance gate; revise and retest rather than launch.

These thresholds are proposed operational criteria. They are not met or failed by the archived automated results because those results do not satisfy the qualified human-review requirement.

## 6. First experiment plan

1. **Day 1 — local setup:** confirm that all model artifacts and dependencies are available locally and that scripts are configured to reject cloud model IDs. Record model IDs, versions, prompt hashes, configuration, timestamps, and output paths.
2. **Day 1 — candidate design:** create up to three prompt variants aimed at concise, natural conversational responses without adding unsupported facts, changing intent, or weakening safety behavior. Treat language-specific cues as hypotheses to be reviewed, not as assumptions about all speakers.
3. **Day 1–2 — diagnostic run:** compare baseline and prompt variants on a small local diagnostic set in Hindi and Kannada. Inspect latency and token deltas, but do not choose a winner from latency alone.
4. **Day 2 — freeze and blind:** select at most one candidate for formal evaluation, freeze the prompts and test set, randomize A/B order, and generate a blinded review sheet. Keep the unblinding key separate from the reviewer packet.
5. **Days 2–7 — qualified review:** obtain structured per-case naturalness preference, meaning-preservation, and safety ratings from the qualified reviewer. Record reviewer identity/qualification at the appropriate level, dates, notes, and any adjudication. Do not fill missing human ratings with automated labels.
6. **Day 7 gate:** apply the predeclared kill/acceptance criteria. Continue only if there is no kill condition; otherwise revert to baseline.
7. **By Day 21:** launch only in languages that passed the human-review gate. If Hindi and/or Kannada fail or review is incomplete, keep the baseline. Do not launch the other four languages without qualified review.

## 7. Limitations and reporting language

The archived experiment is useful for demonstrating an evaluation pitfall: slot preference can be misleading when A/B presentation order is not the same as candidate/baseline identity. After unblinding, the candidate did not win overall. The archived judge was the same model as the generator, and the run used cloud inference despite the stated zero external API budget. The submitter's reported personal inspection of all 120 cases is acknowledged, but it was not recorded as structured per-case ratings and is not a substitute for qualified native-speaker review in all six languages.

Recommended concise statement:

> “We ran an exploratory 120-case comparison across six languages using `gemma4:31b-cloud` for generation and the same model for automated judging. The apparent 72.4% preference for slot B was not the candidate win rate. After unblinding, the candidate won 45 cases, the baseline won 60, and 15 tied, giving the candidate 42.9% preference among non-ties. The submitter reports personally inspecting all 120 cases, but structured human ratings were not recorded in the review sheet. The historical cloud run deviated from the assignment's zero-external-API-budget constraint unless an exception was authorized. We therefore retain the baseline and propose a new local, blinded, qualified review before any launch.”
