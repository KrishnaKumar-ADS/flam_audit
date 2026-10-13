# AI Usage and Reproducibility Disclosure

## 1. Why this document exists

This file discloses where AI assistance was used, which artifacts are model-generated, what was actually executed, where AI suggestions were misleading or corrected, and which quality checks remain pending. It is intended to make the submission fully auditable and demonstrate deep understanding of every claim and formula.

## 2. AI assistance used

AI assistance was used to:
- Inspect the assignment specification and starter kit materials;
- Design controlled micro-tests for tokenizer bugs in `partA/scripts/audit_fertility.py`;
- Help structure KV-cache memory formulas and serving throughput derivations;
- Draft and refine markdown tables and LaTeX formatting;
- Generate initial diagnostic parallel translations for the Part A probe;
- Implement the blinded evaluation harness scripts in Part C.

The submitter remains personally responsible for understanding, independently verifying, and defending every equation, metric, table, and conclusion during the live defense.

## 3. Where AI misled us and how we caught it

1. **Part C Position Bias Conflation (Critical Catch):** When analyzing the automated judge output, the AI assistant initially reported: *"Candidate B won 72.4% of matchups."* Upon auditing `unblind_key.csv` and inspecting `evaluation_harness.py`, we discovered that "B" was merely the presentation slot, not the candidate! The automated LLM judge had an acute **position bias** towards slot B (76 B wins vs 29 A wins). When properly unblinded, the candidate prompt actually won only 45 cases vs baseline 60 cases (42.9% win rate). The AI had confidently treated an evaluation artifact as a project success.
2. **Part A Harmless Code Flagging:** AI initially suggested flagging `random.seed(1337)` in `fertility.py` as a bug that "falsely implies stochasticity." We verified by code inspection and controlled test that removing the line produces identical results, recognizing that penalizing harmless code without measured distortion violates the evidence rule and loses points.
3. **Goodput vs Throughput in Part B:** AI initially described long prompts as having higher throughput based on `reported_tok_s`. We caught that the column sums prompt prefill and decode tokens, and re-derived the true decode goodput (200.9 tok/s for long vs 294.5 tok/s for short).

## 4. Part A corpus provenance & limitations

The Part A probe contains 20 aligned general-domain sentence IDs across seven languages: English (`eng`), Hindi (`hin`), Kannada (`kan`), Tamil (`tam`), Telugu (`tel`), Bengali (`ben`), and Marathi (`mar`), totaling 140 sentences. AI-generated translations were used to construct this diagnostic probe. They have **not** been independently validated by native speakers.

Therefore:
- The probe is a diagnostic instrument, not a gold-standard parallel corpus or FLORES benchmark.
- Tokenizer measurements reflect behavior on this specific sample and denominator.
- Synthetic translation artifacts limit statistical generalization to production traffic.

## 5. Part A execution status

Actual tokenizer comparisons were executed using GPT-2 (`tiktoken`) and XLM-R (`xlm-roberta-base`). Pooled tokens-per-whitespace-word results:

| Language | GPT-2 | XLM-R |
|---|---:|---:|
| English | 1.1837 | 1.2517 |
| Hindi | 7.2667 | 1.2970 |
| Kannada | 21.4434 | 2.1321 |
| Tamil | 24.9907 | 2.2222 |
| Telugu | 19.9561 | 2.1667 |
| Bengali | 11.7787 | 1.8770 |
| Marathi | 9.4252 | 1.7323 |

Output files are `partA/results/tokenizer_metrics.csv` and `partA/results/tokenizer_summary.csv`. Controlled synthetic micro-tests in `partA/scripts/audit_fertility.py` test code mechanics and are kept distinct from corpus runs.

## 6. Part B evidence status

Part B reconciles the supplied model specification and benchmark log. It is an analytical audit of recorded data, not a new GPU run. KV-cache byte arithmetic and concurrency limits are derived from first principles. Aggregate throughput is separated from output goodput.

## 7. Part C cloud generation and position bias disclosure

On 2026-10-13, Part C generated 120 baseline/candidate pairs (240 responses total) across 6 languages using `gemma4:31b-cloud` through Ollama Cloud, and judged them with the same model.

- **Slot-level results:** Slot B preferred in 76 cases, Slot A in 29 cases, 15 ties. Slot B preference among non-ties = 72.4%.
- **Unblinded candidate results:** Candidate preferred in 45 cases, Baseline in 60 cases, 15 ties. True candidate preference among non-ties = **42.9%**.
- **Judge-marked meaning preservation:** A 119/120; B 120/120.
- **Judge-marked safety preservation:** A 120/120; B 120/120.

These are automated model labels, not verified facts. The human review sheet (`review_sheet.csv`) has intentionally blank reviewer fields. **No human evaluation result is claimed.**

## 8. Constraint deviation: cloud inference

The assignment specifies no external API budget. The archived exploratory run used Ollama Cloud and is disclosed as a historical deviation. No further cloud calls will be made. Local reproduction requires local Ollama models or local GPU execution.

## 9. Live defense readiness

The submitter is prepared to:
1. Re-derive KV-cache equations and throughput formulas live.
2. Run `partA/scripts/audit_fertility.py` on arbitrary input strings.
3. Modify tokenizer denominators live.
4. Explain the unblinding mechanics and position bias in Part C.
5. Defend the prompt engineering recommendation against SFT and rewriter alternatives.

## 10. Submitter's personal verification of Part C samples

The submitter reports that, after the automated Gemma evaluation, they personally reviewed and verified all 120 Part C sample cases. The `partC/results/review_sheet.csv` now records the reviewer as **“Submitter (self-review)”** and the verification status as **“Manually verified by submitter; individual ratings not recorded in this sheet”** for each case.

This records the submitter's stated review process; it does not invent per-sample preference scores, meaning-preservation labels, safety labels, naturalness ratings, or reviewer comments. Those individual fields remain blank unless the submitter's actual judgments are entered. Consequently, no human-versus-Gemma agreement rate or human preference percentage is calculated from this sheet.

The personal review is distinct from qualified native-speaker evaluation. The reviewer’s language proficiency and the exact rubric used for the manual verification should be stated accurately if known. The assignment’s designated native-reviewer coverage is Hindi and Kannada; this document does not claim that the submitter is a qualified native reviewer for every language.

The automated evaluation used `gemma4:31b-cloud` through Ollama Cloud and the same model served as generator and judge. This remains a cloud-use deviation from the stated no-external-API-budget constraint unless an explicit exception was granted. The submitter's subsequent personal verification does not remove that provenance or constraint issue.
