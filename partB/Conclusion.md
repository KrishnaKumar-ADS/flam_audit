# Part B — Capacity and Throughput Reconciliation

## KV-cache arithmetic

The model has 28 transformer layers, 8 KV heads, head dimension 128, and an FP16 KV cache. Each token stores both a key and a value:

KV bytes/token = 2 × 28 × 8 × 128 × 2 = 114,688 bytes = 112 KiB.

At a maximum sequence length of 4,096 tokens, the cache requirement is 469,762,048 bytes, or 448 MiB per sequence.

Using decimal GB for the stated 24 GB GPU, the 92% utilization budget is 22.08 GB. Subtracting 8.4 GB for FP16 model weights and 1.6 GB for non-KV overhead leaves approximately 12.08 GB for KV cache. Dividing by 469,762,048 bytes per sequence gives an estimated capacity of 25.7, or approximately 25 full-length sequences. This is a theoretical estimate; actual capacity depends on allocator overhead and cache-block fragmentation.

## Throughput reconciliation

The reported throughput is consistent with counting both prompt and generated tokens:

reported tok/s ≈ num_requests × (prompt_len + gen_len) / wall_clock_s.

For batch 16 with short prompts, 16 × (512 + 256) / 13.91 ≈ 883.2 tok/s. For batch 16 with long prompts, 16 × (3584 + 512) / 49.97 ≈ 1,311.4 tok/s.

Therefore, the higher reported tok/s for long prompts does not establish that longer prompts improve decode throughput. The workloads process different numbers of prompt tokens, so their aggregate token-throughput figures are not directly comparable as a measure of generation speed.

## Saturation and operational recommendation

For short prompts, throughput increases across the tested batch sizes, reaching 2,267.3 tok/s at batch 64, while p95 latency rises to 24.32 seconds. For long prompts, throughput peaks at 1,607.4 tok/s at batch 24, where KV-cache utilization is 93%. At batch 32, throughput falls to 1,384.0 tok/s, KV-cache utilization reaches 97%, seven sequences are preempted, and p95 latency rises to 97.47 seconds. At batch 48, throughput falls further to 1,298.5 tok/s, 23 sequences are preempted, and p95 latency reaches 105.43 seconds.

The evidence contradicts the recommendation to assume linear throughput scaling or to use 3,200 tok/s at batch 48. Batch 24 is the observed long-prompt throughput peak in this test, but its high KV-cache utilization and 69.22-second p95 latency mean it should not automatically be treated as the production operating point. A production choice should consider latency targets, preemption, and workload mix, not throughput alone.