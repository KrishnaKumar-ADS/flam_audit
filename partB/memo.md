# Part B — Capacity and Throughput Reconciliation

## 1. Scope and evidence

This analysis uses the supplied `bench/model_spec.md` and `bench/bench_log.csv`. It is an analysis of the provided benchmark log, not a newly executed GPU benchmark.

## 2. KV-cache bytes per token

The model specification gives:
- Transformer layers: 28
- KV heads: 8
- Head dimension: 128
- KV-cache precision: FP16 = 2 bytes per element

Each token stores both a key and a value for every layer:

KV bytes/token = 2 × 28 × 8 × 128 × 2 = 114,688 bytes.

This equals 112 KiB per token.

For a 4,096-token sequence:

114,688 × 4,096 = 469,762,048 bytes = 448 MiB.

## 3. Approximate concurrency

Use decimal GB consistently with the specification's 24 GB GPU capacity and 1.6 GB runtime-overhead estimate.

- GPU memory budget: 24 × 0.92 = 22.08 GB.
- FP16 model weights: 4.2 billion parameters × 2 bytes = 8.4 GB.
- Non-KV runtime overhead: 1.6 GB.
- Estimated memory remaining for KV cache: 22.08 − 8.4 − 1.6 = 12.08 GB.
- KV cache per full-length sequence: 469,762,048 bytes = 0.469762048 GB.
- Estimated concurrency: 12.08 / 0.469762048 ≈ 25.7 sequences.

The approximate theoretical capacity is therefore 25 whole full-length sequences, before implementation-specific allocation overhead and fragmentation. At batch 24, 24 sequences require approximately 11.27 GB of KV cache. This is consistent with the logged 93% KV-cache utilization against an estimated 12.08 GB cache budget. The estimate is approximate because the actual serving allocator and its reserved cache capacity are not fully specified.

## 4. Throughput-counter reconciliation

The supplied rows are consistent with the harness counting prompt and generated tokens:

reported tok/s ≈ num_requests × (prompt_len + gen_len) / wall_clock_s.

Short-prompt batch 16:

16 × (512 + 256) / 13.91 ≈ 883.2 tok/s.

Long-prompt batch 16:

16 × (3584 + 512) / 49.97 ≈ 1,311.4 tok/s.

The calculations reproduce the reported figures to rounding precision. Therefore, the reported throughput includes prompt tokens as well as generated tokens. The short- and long-prompt results are not a controlled comparison of decode-only throughput.

## 5. Observed throughput and capacity pressure

For short prompts (512 input tokens, 256 generated tokens), reported throughput rises from 70.2 tok/s at batch 1 to 2,267.3 tok/s at batch 64. Over that range, p95 end-to-end latency rises from 12.86 seconds to 24.32 seconds.

For long prompts (3,584 input tokens, 512 generated tokens):
- Batch 16: 1,311.4 tok/s; KV utilization 0.62; no preempted sequences; p95 latency 54.60 seconds.
- Batch 24: 1,607.4 tok/s; KV utilization 0.93; no preempted sequences; p95 latency 69.22 seconds.
- Batch 32: 1,384.0 tok/s; KV utilization 0.97; 7 preempted sequences; p95 latency 97.47 seconds.
- Batch 48: 1,298.5 tok/s; KV utilization 0.97; 23 preempted sequences; p95 latency 105.43 seconds.

Long-prompt throughput peaks at batch 24 in the supplied runs. From batch 24 to batch 32, throughput falls by approximately 13.9%, while p95 latency rises by approximately 40.7%. At batch 48, throughput is approximately 19.2% below the batch-24 peak.

These measurements are consistent with capacity pressure at high long-prompt concurrency: KV utilization is already 93% at batch 24, rises to 97% at batch 32, and preemption appears at batches 32 and 48. They do not establish that KV-cache pressure is the sole cause of every throughput change.

## 6. Audit of the original recommendations

The recommendation to assume 3,200 tok/s at batch 48 is contradicted by the observed 1,298.5 tok/s. Linear extrapolation is not justified by these measurements.

The claim that longer prompts clearly improve GPU utilization is also not established by comparing aggregate token throughput alone. The workloads contain different numbers of input and generated tokens, and the counter includes both. A controlled decode-throughput comparison would require an appropriate measurement separating prompt processing from generation.

Batch 24 is the observed long-prompt throughput peak, not automatically the best production setting. Its 93% KV utilization and 69.22-second p95 latency warrant evaluating the service's latency target and workload mix before selecting an operating point.

## 7. Limitations

These conclusions apply to the supplied configuration and recorded runs. The concurrency estimate is theoretical and unit-dependent. The log does not establish performance on other hardware, models, prompt distributions, or serving configurations.


### Generated-output goodput

Aggregate throughput counts both input prompt tokens and generated tokens.
It must not be reported as generated-output goodput. For the long-prompt
batch-24 run, 24 requests generated 512 tokens each over approximately
61.16 seconds, giving generated-output goodput of:

24 × 512 / 61.16 ≈ 200.8 generated tokens/second.

This is a derived metric from the supplied run, not a separately measured
decode-only benchmark. It should not be compared directly with aggregate
throughput without accounting for the different token counts.
