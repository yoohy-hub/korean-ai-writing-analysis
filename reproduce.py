"""Measure paper-scope features from separately authorized, pseudonymized text CSV.

The private CSV is not included in the release and is never modified. Only
numerical summaries are exported; learner text and morphology tokens are not.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import pandas as pd
from kiwipiepy import Kiwi
from paper_metrics import measure_text,form_source_metrics

VERSIONS=['A','B','C']

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input',type=Path,required=True,help='Authorized CSV with pseudonyms, genre and A_text/B_text/C_text')
    p.add_argument('--output',type=Path,required=True,help='New output directory')
    a=p.parse_args();source=a.input.resolve();out=a.output.resolve()
    if out.exists():p.error('--output must name a new directory')
    before=hashlib.sha256(source.read_bytes()).hexdigest()
    df=pd.read_csv(source,encoding='utf-8-sig')
    required={'participant_id','task_id','genre',*[v+'_text' for v in VERSIONS]}
    if required-set(df):p.error('Missing required input columns')
    if df['task_id'].duplicated().any():p.error('Task keys must be unique')
    if not df.participant_id.astype(str).str.fullmatch(r'P\d{3}').all():p.error('Use paper-scope pseudonymous participant keys')
    if not df.task_id.astype(str).str.fullmatch(r'T\d{3}').all():p.error('Use paper-scope pseudonymous task keys')
    kiwi=Kiwi(num_workers=-1);texts=[];sources=[]
    for _,r in df.iterrows():
        key={n:r[n] for n in ['participant_id','task_id','genre']};forms={}
        for v in VERSIONS:
            values,forms[v]=measure_text(r[v+'_text'],kiwi)
            e=r.get(v+'_manual_error_count')
            e=None if e is None or pd.isna(e) else int(e)
            rate=e/values['eojeols']*100 if e is not None and values['eojeols'] else None
            texts.append({**key,'version':v,**values,'manual_error_count':e,'manual_errors_per_100_eojeols':rate})
        sources.append({**key,**form_source_metrics(forms['A'],forms['B'],forms['C'])})
    if hashlib.sha256(source.read_bytes()).hexdigest()!=before:raise RuntimeError('Input changed')
    out.mkdir(parents=True)
    pd.DataFrame(texts).to_csv(out/'text_metrics.csv',index=False,encoding='utf-8-sig')
    pd.DataFrame(sources).to_csv(out/'source_metrics.csv',index=False,encoding='utf-8-sig')
    report={'input_sha256':before,'input_unchanged':True,'tasks':len(df),'texts':len(texts),
        'automated_F1_F3_measures':6,'text_included_in_output':False,'manual_coding_reclassified':False}
    (out/'measurement_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
