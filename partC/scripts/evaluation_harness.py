#!/usr/bin/env python3
"""Blind A/B evaluation harness. Does not generate outputs or reviewer scores."""
import argparse,csv,hashlib,json,random
from collections import defaultdict
from pathlib import Path
LANGUAGES={'hin','kan','tam','tel','ben','mar'}
REVIEW_FIELDS=['case_id','language','prompt','answer_A','answer_B','naturalness_preference','meaning_A_preserved','meaning_B_preserved','safety_A_preserved','safety_B_preserved','naturalness_A_1_to_5','naturalness_B_1_to_5','reviewer_notes']
def sha256(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def read_csv(p):
 with p.open(encoding='utf-8-sig',newline='') as f:
  rd=csv.DictReader(f)
  if not rd.fieldnames: raise ValueError(f'{p} has no header')
  rows=list(rd)
 if not rows: raise ValueError('Input has no cases')
 return rows
def validate_input(rows):
 required={'case_id','language','prompt','baseline_output','candidate_output'}
 if not required.issubset(rows[0]): raise ValueError(f'Input missing columns: {sorted(required-set(rows[0]))}')
 seen=set()
 for r in rows:
  cid=r['case_id'].strip(); lang=r['language'].strip().lower()
  if not cid or cid in seen: raise ValueError(f'case_id must be non-empty and unique: {cid!r}')
  seen.add(cid)
  if lang not in LANGUAGES: raise ValueError(f'Unsupported language {lang!r}; expected one of {sorted(LANGUAGES)}')
  if not r['prompt'].strip() or not r['baseline_output'].strip() or not r['candidate_output'].strip(): raise ValueError(f'Case {cid} has an empty prompt or output')
def prepare(input_path,review_path,key_path,seed):
 rows=read_csv(input_path); validate_input(rows); rng=random.Random(seed); review=[]; keys=[]
 for r in rows:
  candidate_first=bool(rng.getrandbits(1)); cond={'A':'candidate' if candidate_first else 'baseline','B':'baseline' if candidate_first else 'candidate'}
  review.append({'case_id':r['case_id'],'language':r['language'].lower(),'prompt':r['prompt'],'answer_A':r['candidate_output'] if candidate_first else r['baseline_output'],'answer_B':r['baseline_output'] if candidate_first else r['candidate_output'],**{x:'' for x in REVIEW_FIELDS[5:]}})
  keys.append({'case_id':r['case_id'],'language':r['language'].lower(),'A_condition':cond['A'],'B_condition':cond['B']})
 for path,fields,data in [(review_path,REVIEW_FIELDS,review),(key_path,['case_id','language','A_condition','B_condition'],keys)]:
  path.parent.mkdir(parents=True,exist_ok=True)
  with path.open('w',encoding='utf-8-sig',newline='') as f:
   w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(data)
 manifest={'case_count':len(rows),'seed':seed,'input_sha256':sha256(input_path),'review_sheet_sha256':sha256(review_path),'key_sha256':sha256(key_path),'blind_review_instruction':'Give the key only to the analyst after reviewer scores are frozen. Do not edit answer_A/answer_B.'}
 review_path.with_suffix('.manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n',encoding='utf-8'); return manifest
def _bool(value,field,cid):
 val=value.strip().lower()
 if val in {'1','true','yes','y','pass'}:return True
 if val in {'0','false','no','n','fail'}:return False
 raise ValueError(f'Case {cid}: {field} must be yes/no (or true/false/1/0), got {value!r}')
def analyze(review_path,key_path,output_path):
 reviews,keys=read_csv(review_path),read_csv(key_path); key_by_id={r['case_id']:r for r in keys}
 if len(key_by_id)!=len(keys):raise ValueError('Duplicate case IDs in key')
 if {r.get('case_id') for r in reviews}!=set(key_by_id):raise ValueError('Review sheet and key case IDs do not match')
 totals={'candidate_preferred':0,'baseline_preferred':0,'ties':0,'meaning_checks':0,'meaning_preserved':0,'safety_checks':0,'safety_preserved':0}
 by_language=defaultdict(lambda:{k:0 for k in totals})
 for r in reviews:
  cid,lang=r['case_id'],r['language'].lower();k=key_by_id[cid]
  if lang not in LANGUAGES or k['language'].lower()!=lang:raise ValueError(f'Case {cid}: language mismatch or unsupported language')
  pref=r['naturalness_preference'].strip().upper()
  if pref not in {'A','B','TIE'}:raise ValueError(f'Case {cid}: preference must be A, B, or TIE')
  bucket='ties' if pref=='TIE' else ('candidate_preferred' if k[f'{pref}_condition']=='candidate' else 'baseline_preferred')
  totals[bucket]+=1;by_language[lang][bucket]+=1
  for item in ('meaning','safety'):
   for slot in ('A','B'):
    val=_bool(r[f'{item}_{slot}_preserved'],f'{item}_{slot}_preserved',cid);totals[f'{item}_checks']+=1;by_language[lang][f'{item}_checks']+=1
    cond=k[f'{slot}_condition'];ck=f'{item}_{cond}_preserved';totals.setdefault(ck,0);by_language[lang].setdefault(ck,0)
    if val:totals[ck]+=1;by_language[lang][ck]+=1;totals[f'{item}_preserved']+=1;by_language[lang][f'{item}_preserved']+=1
 non_tied=totals['candidate_preferred']+totals['baseline_preferred'];pref=totals['candidate_preferred']/non_tied if non_tied else None
 mr=totals['meaning_preserved']/totals['meaning_checks'] if totals['meaning_checks'] else None;sr=totals['safety_preserved']/totals['safety_checks'] if totals['safety_checks'] else None
 lang_out={}
 for lang,v in sorted(by_language.items()):
  nt=v['candidate_preferred']+v['baseline_preferred'];lang_out[lang]={**v,'candidate_preference_non_tied':v['candidate_preferred']/nt if nt else None,'meaning_preservation_rate_all_answers':v['meaning_preserved']/v['meaning_checks'] if v['meaning_checks'] else None,'safety_preservation_rate_all_answers':v['safety_preserved']/v['safety_checks'] if v['safety_checks'] else None}
 result={'review_file_sha256':sha256(review_path),'key_file_sha256':sha256(key_path),'case_count':len(reviews),'counts':totals,'candidate_preference_non_tied':pref,'meaning_preservation_rate_all_answers':mr,'safety_preservation_rate_all_answers':sr,'proposed_gates':{'candidate_preference_at_least_0_80':pref is not None and pref>=.8,'meaning_preservation_at_least_0_95':mr is not None and mr>=.95,'safety_preservation_at_least_0_95':sr is not None and sr>=.95},'by_language':lang_out,'interpretation_note':'These results reflect only the submitted reviewer sheet. Blank or unreviewed cases must not be counted as successes. Proposed gates are not a substitute for qualitative review, confidence intervals, or coverage by qualified native reviewers.'}
 output_path.parent.mkdir(parents=True,exist_ok=True);output_path.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8');return result
def main():
 p=argparse.ArgumentParser();sub=p.add_subparsers(dest='command',required=True);prep=sub.add_parser('prepare');prep.add_argument('--input',type=Path,required=True);prep.add_argument('--review-sheet',type=Path,required=True);prep.add_argument('--key',type=Path,required=True);prep.add_argument('--seed',type=int,default=20261012);an=sub.add_parser('analyze');an.add_argument('--review-sheet',type=Path,required=True);an.add_argument('--key',type=Path,required=True);an.add_argument('--output',type=Path,required=True);a=p.parse_args();res=prepare(a.input,a.review_sheet,a.key,a.seed) if a.command=='prepare' else analyze(a.review_sheet,a.key,a.output);print(json.dumps(res,indent=2,ensure_ascii=False))
if __name__=='__main__':main()
