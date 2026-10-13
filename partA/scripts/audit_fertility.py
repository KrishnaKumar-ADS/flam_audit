#!/usr/bin/env python3
"""Controlled micro-experiments for starter fertility.py assumptions; no external tokenizer required."""
import json, regex

def starter_like(lines, encode):
    out=[]
    for line in lines:
        s=line.lower(); out.append({'fertility':len(encode(s))/len(s.split(' ')), 'tok_per_char':len(encode(s))/len(s)})
    return out

def corrected(lines, encode):
    out=[]
    for line in lines:
        s=line; out.append({'fertility':len(encode(s))/len(s.split()),'tok_per_codepoint':len(encode(s))/len(s),'tok_per_grapheme':len(encode(s))/len(regex.findall(r'\X',s))})
    return out

def main():
    # Deterministic mock encoder: one token per whitespace-separated non-empty word.
    enc=lambda s: [x for x in s.split() if x]
    repeated='alpha  beta'
    a=starter_like([repeated],enc)[0]; b=corrected([repeated],enc)[0]
    combining='e\u0301'
    grapheme={'text_codepoints':len(combining),'grapheme_clusters':len(regex.findall(r'\X',combining))}
    # Macro mean vs pooled ratio: unequal-length examples deliberately expose weighting.
    char_encoder=lambda s: [c for c in s if not c.isspace()]
    lines=['abcdefghij k','z']; counts=[len(char_encoder(x)) for x in lines]; words=[len(x.split()) for x in lines]
    macro=sum(t/w for t,w in zip(counts,words))/len(lines); pooled=sum(counts)/sum(words)
    print(json.dumps({'fixture':'synthetic controlled tests, not tokenizer benchmark','double_space':{'input':repeated,'starter_words':len(repeated.split(' ')),'correct_words':len(repeated.split()),'starter_fertility':a['fertility'],'corrected_fertility':b['fertility'],'absolute_delta':a['fertility']-b['fertility']},'unicode_denominator':grapheme,'weighting':{'per_line_ratios':[t/w for t,w in zip(counts,words)],'macro_mean':macro,'pooled_ratio':pooled,'delta':macro-pooled},'harmless_suspicious_code':'random.seed(1337) is unused; removing it does not change results because no random operation is used.'},indent=2,ensure_ascii=False))
if __name__=='__main__':main()
