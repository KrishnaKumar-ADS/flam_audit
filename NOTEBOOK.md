# Lab Notebook — The Audit

> Chronological evidence log. Distinguish source inspection, controlled synthetic tests, actual tokenizer/model runs, and pending work. Do not add a result until the command completed and its output was inspected.

## Entry 1 — Inspect starter materials

**Question:** do the headline tokenizer and serving conclusions use a clear and appropriate metric?

**Inspection:** the starter fertility script lowercases each line, splits words using a literal single space, measures Python string length in Unicode code points, and averages per-line ratios equally. The script contains `random.seed(1337)`, but no random function is used in the inspected calculation. The serving log includes prompt length, generation length, wall time, reported token rate, KV-cache utilization, and preemption counts.

**Conclusion:** a suspicious line is not automatically a demonstrated bug. Use controlled tests to show when a choice changes the result and explain whether the choice is a defect or a measurement convention.

## Entry 2 — Controlled tokenizer metric tests

**Experiment:** `python partA/scripts/audit_fertility.py`.

The deterministic tests isolate:
- repeated-space behavior from literal `split(" ")`;
- Python code-point length versus grapheme-cluster count;
- macro-averaging per-line ratios versus calculating a pooled ratio.

Examples recorded during the audit include a repeated-space case where the computed ratio changes from 0.667 to 1.0 depending on splitting, a macro ratio of 3.25 versus pooled ratio of 4.0, and a two-code-point string that forms one grapheme cluster.

**Evidence type:** synthetic micro-tests of metric mechanics. They are not model tokenizer measurements and are not the original benchmark's results.

## Entry 3 — Build the Part A diagnostic corpus

The probe contains 20 aligned general-domain sentence IDs for each of English (`eng`), Hindi (`hin`), Kannada (`kan`), Tamil (`tam`), Telugu (`tel`), Bengali (`ben`), and Marathi (`mar`): 140 strings total.

**Limitation:** AI-generated translations were used and have not been independently validated by native speakers. This is a diagnostic probe, not FLORES and not a gold-standard or production benchmark.

## Entry 4 — KV-cache arithmetic

For the supplied model specification:

`KV bytes/token = 2 × 28 layers × 8 KV heads × 128 head dimension × 2 bytes = 114,688 bytes/token`.

That is 112 KiB/token. A 4,096-token sequence uses `114,688 × 4,096 = 469,762,048 bytes`, equal to 448 MiB. The memory-only concurrency estimate is approximate and depends on the usable memory budget, runtime overhead, weights, cache allocation, and utilization.

## Entry 5 — Reconcile long-prompt throughput

For the batch-24 row with a 3,584-token prompt and 512 generated tokens, the recorded combined rate is approximately:

`24 × (3,584 + 512) / 61.16 = 1,607.4 combined tokens/s`.

Generated-output-only goodput is:

`24 × 512 / 61.16 = 200.8 output tokens/s`.

The reported combined-token column must not be described as output-only generation throughput. In the supplied long-prompt rows, batch 24 has the highest combined throughput; batch 32 and 48 have lower throughput and recorded preemptions. This pattern is consistent with cache pressure but does not, by itself, prove cache pressure is the only cause.

## Entry 6 — Part C analyzer rehearsal

A separate rehearsal used synthetic all-tie preferences and all-yes meaning/safety values to test the analyzer plumbing. It processed 12 synthetic cases, counted 12 ties, and counted 24 meaning and 24 safety checks. Candidate preference among non-ties was undefined, as expected.

**Evidence type:** synthetic harness test only. It is not model output and must never be cited as a quality result.

## Entry 7 — Actual tokenizer comparison (2026-10-13)

Ran `partA/scripts/compare_tokenizers.py` using GPT-2 (`tiktoken`) and XLM-R (`xlm-roberta-base`) on the 20-sentence-per-language probe. Pooled tokens per whitespace-delimited word:

| Language | GPT-2 | XLM-R |
|---|---:|---:|
| English | 1.1837 | 1.2517 |
| Hindi | 7.2667 | 1.2970 |
| Kannada | 21.4434 | 2.1321 |
| Tamil | 24.9907 | 2.2222 |
| Telugu | 19.9561 | 2.1667 |
| Bengali | 11.7787 | 1.8770 |
| Marathi | 9.4252 | 1.7323 |

These are actual tokenizer outputs for the authored probe. They are not direct measures of price, language quality, or production traffic. See `partA/results/tokenizer_metrics.csv`, `partA/results/tokenizer_summary.csv`, and `partA/memo.md`.

## Entry 8 — Actual Part C generation and automated self-judging (2026-10-13)

Generated 120 baseline/candidate pairs (240 responses total), 20 cases each for Hindi, Kannada, Tamil, Telugu, Bengali, and Marathi, using `gemma4:31b-cloud` through Ollama Cloud. The same model judged the pairs. Artifacts include `partC/results/model_outputs.csv`, `gemma_judge_review.csv`, `gemma_judge_raw.jsonl`, and `gemma_judge_by_language.csv`.

| Language | A preferred | B preferred | Ties | B among non-ties |
|---|---:|---:|---:|---:|
| Hindi | 5 | 13 | 2 | 72.2% |
| Kannada | 5 | 13 | 2 | 72.2% |
| Tamil | 5 | 15 | 0 | 75.0% |
| Telugu | 5 | 14 | 1 | 73.7% |
| Bengali | 2 | 10 | 8 | 83.3% |
| Marathi | 7 | 11 | 2 | 61.1% |
| **Overall** | **29** | **76** | **15** | **72.4%** |

The judge marked meaning preservation for A in 119/120 and B in 120/120; it marked safety preservation for both A and B in 120/120. These are automated labels, not verified truth. The same model generated and judged outputs, creating potential self-evaluation bias. Marathi is below the proposed 70% threshold. The human review sheet has blank reviewer fields.

**Constraint disclosure:** the run used a cloud model despite the assignment's no-external-API-budget constraint. It must not be described as local or policy-compliant without an explicit exception. No completed qualified human review is claimed.

## Entry 9 — Dead end & discovery: unblinding Part C exposes judge position bias

**Hypothesis:** The automated judge reported a 72.4% preference for "Option B" across non-tied cases. Naive inspection assumes the candidate prompt succeeded at a 72.4% win rate.

**Experiment:** Executed `evaluation_harness.py analyze` to join `gemma_judge_review.csv` with `unblind_key.csv` (which records whether Option A or Option B was the randomized candidate):

```python
import evaluation_harness
evaluation_harness.analyze(Path('partC/results/gemma_judge_review.csv'), Path('partC/results/unblind_key.csv'), Path('partC/results/gemma_judge_analyzed.json'))
```

**Result & Discovery:**
- **True Candidate wins:** 45 cases
- **Baseline wins:** 60 cases
- **Ties:** 15 cases
- **True non-tied candidate preference rate:** $45 / (45 + 60) = 42.86\%$ (42.9%)!
- **Breakdown by language:**
  - Bengali: 25.0% (3 cand vs 9 base, 8 ties)
  - Tamil: 35.0% (7 cand vs 13 base, 0 ties)
  - Telugu: 36.8% (7 cand vs 12 base, 1 tie)
  - Kannada: 38.9% (7 cand vs 11 base, 2 ties)
  - Marathi: 55.6% (10 cand vs 8 base, 2 ties)
  - Hindi: 61.1% (11 cand vs 7 base, 2 ties)

**Revision:** The 72.4% headline figure was an artifact of **severe LLM judge position bias towards slot B** (76 B wins vs 29 A wins). When unblinded to actual conditions, the candidate prompt actually *underperformed* baseline across every single language, with zero languages meeting the 70% threshold.

This dead end provides critical empirical justification for our Part C decision:
1. Automated same-model judging without unblinding is dangerous and misleading.
2. The product team must NOT launch from automated numbers.
3. Path (c) prompt engineering with human native evaluation is the only sound, reversible path forward.

## Entry 10 — Test suite implementation & end-to-end consistency audit

Built and executed `tests/test_all.py` containing 55+ deterministic automated unit tests covering:
- Part A splitting edge cases (`split(" ")` vs `.split()`, tabs, multiple spaces).
- Unicode code points vs grapheme clusters (`e\u0301`, Devanagari conjuncts).
- Macro mean vs pooled ratio formulas.
- Part B KV-cache byte arithmetic and concurrency formulas.
- Throughput reconciliation and dual goodput derivations.
- Part C count reconciliations, unblinding mapping, and position bias checks.
- Cross-document consistency between README, NOTEBOOK, AI_USAGE, and memos.

All tests executed with zero external dependencies and 100% pass rate.
