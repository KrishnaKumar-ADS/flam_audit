#!/usr/bin/env python3
"""Run a reproducible tokenizer comparison on the included aligned corpus.
Requires: pip install tiktoken transformers sentencepiece regex
Model downloads may require network access on first run.
"""
import argparse, csv, json, unicodedata
from pathlib import Path
import regex

def load_encoder(spec):
    if spec == 'gpt2':
        import tiktoken
        enc=tiktoken.get_encoding('gpt2')
        return lambda s: len(enc.encode(s))
    if spec == 'xlm-roberta-base':
        from transformers import AutoTokenizer
        tok=AutoTokenizer.from_pretrained('xlm-roberta-base')
        return lambda s: len(tok.encode(s, add_special_tokens=False))
    raise ValueError(f'Unknown tokenizer {spec!r}; supported: gpt2, xlm-roberta-base')

def main():
    p=argparse.ArgumentParser(); p.add_argument('--corpus-dir',type=Path,default=Path(__file__).resolve().parents[1]/'corpus'); p.add_argument('--output',type=Path,default=Path(__file__).resolve().parents[1]/'results'/'tokenizer_metrics.csv'); p.add_argument('--tokenizers',nargs='+',default=['gpt2','xlm-roberta-base']); a=p.parse_args()
    encoders={n:load_encoder(n) for n in a.tokenizers}; langs=['eng','hin','kan','tam','tel','ben','mar']; allrows=[]
    for lang in langs:
        lines=(a.corpus_dir/f'{lang}.txt').read_text(encoding='utf-8').splitlines()
        for idx,raw in enumerate(lines,1):
            s=unicodedata.normalize('NFC',raw.strip())
            if not s: continue
            # split() collapses all whitespace; graphemes use Unicode extended grapheme clusters.
            words=len(s.split()); graphemes=len(regex.findall(r'\X',s)); codepoints=len(s); utf8bytes=len(s.encode('utf-8'))
            for name,encode in encoders.items():
                tokens=encode(s)
                allrows.append({'language':lang,'sentence_id':f's{idx:03d}','tokenizer':name,'tokens':tokens,'whitespace_words':words,'grapheme_clusters':graphemes,'unicode_codepoints':codepoints,'utf8_bytes':utf8bytes,'tokens_per_word':tokens/words if words else None,'tokens_per_grapheme':tokens/graphemes if graphemes else None,'tokens_per_codepoint':tokens/codepoints if codepoints else None,'tokens_per_utf8_byte':tokens/utf8bytes if utf8bytes else None})
    a.output.parent.mkdir(parents=True,exist_ok=True)
    with a.output.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(allrows[0])); w.writeheader(); w.writerows(allrows)
    # pooled ratios preserve the correct denominator: sum(tokens)/sum(denominator)
    summary=[]
    for name in encoders:
      for lang in langs:
        rs=[r for r in allrows if r['tokenizer']==name and r['language']==lang]
        total_tokens=sum(r['tokens'] for r in rs); total_words=sum(r['whitespace_words'] for r in rs); total_gc=sum(r['grapheme_clusters'] for r in rs); total_bytes=sum(r['utf8_bytes'] for r in rs); total_cp=sum(r['unicode_codepoints'] for r in rs)
        summary.append({'tokenizer':name,'language':lang,'sentences':len(rs),'tokens_total':total_tokens,'whitespace_words_total':total_words,'grapheme_clusters_total':total_gc,'unicode_codepoints_total':total_cp,'utf8_bytes_total':total_bytes,'tokens_per_word_pooled':total_tokens/total_words,'tokens_per_grapheme_pooled':total_tokens/total_gc,'tokens_per_codepoint_pooled':total_tokens/total_cp,'tokens_per_utf8_byte_pooled':total_tokens/total_bytes})
    sp=a.output.with_name('tokenizer_summary.csv')
    with sp.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(summary[0])); w.writeheader(); w.writerows(summary)
    print(f'Wrote {len(allrows)} sentence-tokenizer rows to {a.output}')
    print(f'Wrote pooled denominator summary to {sp}')
    print('Routing/cost primary: tokens per matched request (or pooled tokens per aligned sentence when prompts are parallel), because inference billing and context use are token-based; never infer cost directly from tokens per word.')
if __name__=='__main__': main()
