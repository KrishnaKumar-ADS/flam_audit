# Part B — Capacity reconciliation

## B1. KV cache arithmetic

For grouped-query attention, each token stores both keys and values for each layer and KV head:

`bytes/token = 2 (K,V) × 28 layers × 8 KV heads × 128 dimensions × 2 bytes (fp16) = 114,688 bytes = 112 KiB/token.`

At 4096 tokens: `114,688 × 4096 = 469,762,048 bytes = 448 MiB` per full sequence.

Approximate budget using decimal GB as the model spec does: GPU budget `24 × 0.92 = 22.08 GB`; fp16 weights `4.2B × 2 = 8.4 GB`; runtime overhead `1.6 GB`; residual KV budget `22.08 − 8.4 − 1.6 = 12.08 GB`. Divide by `0.469762 GB/sequence` gives about `25.7`, so roughly **25 full 4096-token sequences** before allocator/block fragmentation and other unmodelled overhead. The log is consistent: batch 24 at prompt 3584 uses 0.93 KV utilization; batch 32 reaches 0.97 and has 7 preempted sequences; batch 48 stays at 0.97 and has 23 preemptions. This is a rough capacity bound, not a guarantee.

## B2. Long-context throughput anomaly

The long-prompt reported rate rises through batch 24 (1607.4 at batch 24), then falls at batch 32 (1384.0) and batch 48 (1298.5), despite more requests. The corresponding `kv_cache_util` is 0.93, 0.97, 0.97, while `preempted_seqs` jumps from 0 to 7 to 23. This supports a KV-cache pressure / preemption hypothesis: the scheduler cannot keep all sequences resident and extra work is spent swapping/recomputing or otherwise handling preemptions rather than producing useful output. A quantitative deployment change is cap the long-context concurrency at 24 pending a controlled test; compared with batch 32/48, it avoids the observed preemptions in this log and the measured reported counter is 1607.4 vs 1384.0/1298.5. Validate by repeating the same load sweep and measuring preemption count, output-token goodput and p95 latency.

## B3. The column misread and honest goodput

`reported_tok_s` counts **prompt plus generated tokens**, not generated output tokens alone. For the batch-24, prompt-3584, generation-512 row: total combined tokens are `24 × (3584 + 512) = 98,304`; divided by 61.16 s gives `1607.45 combined tok/s`, matching the log. Actual output goodput is `24 × 512 / 61.16 = 200.92 generated tok/s`. Independently, `1607.4 × 512 / (3584 + 512) = 200.93 generated tok/s` (small difference from rounding). So the report's “long prompts give better throughput” compares unequal amounts of prompt work per second, and its linear extrapolation to batch 48 is contradicted by observed 1298.5 combined tok/s, preemptions, and cache saturation. It should report combined token rate separately from generated-token goodput and latency.

For comparison, short-prompt batch 16 output goodput is `16×256/13.91 = 294.5 generated tok/s`, while long-prompt batch 16 output goodput is `16×512/49.97 = 163.9 generated tok/s`. This reverses the naive claim when “throughput” means generated outputs.

## B4. Confirming metric

Pull the serving engine's per-request **KV-cache preemption / swap / recompute counter** during the repeated long-context sweep. If cache pressure is the mechanism, it should remain near zero through batch 24 and rise at batch 32 and 48, consistent with the log's 7 and 23 preempted sequences and 0.97 peak utilization. If the engine exposes only one counter, use preempted sequences; pair it with output-token goodput because `reported_tok_s` includes prefill tokens.
