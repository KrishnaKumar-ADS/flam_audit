#!/usr/bin/env python3
import csv, json
from pathlib import Path
spec={'layers':28,'kv_heads':8,'head_dim':128,'bytes_per_element':2,'max_model_len':4096,'gpu_gb':24,'gpu_utilization':0.92,'weights_params':4.2e9,'weight_bytes_per_param':2,'runtime_overhead_gb':1.6}
kv_bytes=2*spec['layers']*spec['kv_heads']*spec['head_dim']*spec['bytes_per_element']
seq_bytes=kv_bytes*spec['max_model_len']
usable_gb=spec['gpu_gb']*spec['gpu_utilization']-(spec['weights_params']*spec['weight_bytes_per_param']/1e9)-spec['runtime_overhead_gb']
max_seq=int((usable_gb*1e9)//seq_bytes)
path=Path(__file__).resolve().parents[2]/'starter_kit'/'bench'/'bench_log.csv'
# The benchmark log is copied alongside this script in the submission.
path=Path(__file__).resolve().parent/'bench_log.csv'
rows=list(csv.DictReader(path.open(encoding='utf-8')))
out=[]
for r in rows:
    b=int(r['batch_size']); p=int(r['prompt_len']); g=int(r['gen_len']); wall=float(r['wall_clock_s']); rep=float(r['reported_tok_s'])
    out.append({'batch_size':b,'prompt_len':p,'reported_tok_s':rep,'output_goodput_tok_s':b*g/wall,'combined_token_rate_recomputed':b*(p+g)/wall,'preempted_seqs':int(r['preempted_seqs']),'kv_cache_util':float(r['kv_cache_util'])})
print(json.dumps({'kv_bytes_per_token':kv_bytes,'kv_bytes_per_4096_token_sequence':seq_bytes,'kv_mib_per_sequence':seq_bytes/(1024**2),'estimated_usable_kv_gb':usable_gb,'estimated_max_4096_sequences':max_seq,'rows':out},indent=2))
