"""Replay paper-scope statistics from pseudonymized numerical/categorical data.

The reported omnibus adjusted p-values are reference-only. This runner does
not recalculate them or claim they are independently reproduced.
"""
from __future__ import annotations
import argparse
from datetime import datetime,timezone
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import tempfile
import pandas as pd

HERE=Path(__file__).resolve().parent
DATA_FILES=['text_metrics.csv','source_metrics.csv','meaning_codes.csv']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--data',type=Path,default=HERE/'data')
    p.add_argument('--reference',type=Path,default=HERE/'reference'/'aggregates')
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();data=a.data.resolve();reference=a.reference.resolve();out=a.output.resolve()
    if out.exists():p.error('--output must name a new directory')
    for name in DATA_FILES:
        if not (data/name).is_file():p.error('Missing input: '+name)
    before={n:sha(data/n) for n in DATA_FILES};start=datetime.now(timezone.utc).isoformat()
    out.mkdir(parents=True);tables=out/'tables';tables.mkdir()
    os.environ.setdefault('MPLBACKEND','Agg')
    with tempfile.TemporaryDirectory(prefix='paper-scope-cache-') as cache:
        os.environ.setdefault('MPLCONFIGDIR',cache)
        from rq1_reproduce import reproduce_rq1,compare_rq1
        from rq2_reproduce import reproduce_rq2,compare_rq2,OUTPUT_FILES
        rq1=reproduce_rq1(data,tables);rq2=reproduce_rq2(data,tables)
        check1=compare_rq1(tables,reference);check2=compare_rq2(tables,reference)
    canonical=reference.parent/'public_replay'/OUTPUT_FILES[0]
    canonical_pass=None
    if canonical.is_file():
        try:
            pd.testing.assert_frame_equal(pd.read_csv(tables/OUTPUT_FILES[0]),pd.read_csv(canonical),check_dtype=False,check_exact=False,rtol=1e-8,atol=1e-9)
            canonical_pass=True
        except AssertionError:canonical_pass=False
    unchanged=all(sha(data/n)==h for n,h in before.items())
    ok=check1['passed'] and check2['deterministic_statistics_passed'] and unchanged and canonical_pass is not False
    status='PASS_SCOPED_REPLAY' if ok else 'FAIL'
    report={'status':status,'scope':'paper-scope public numerical statistical replay',
        'started_at_utc':start,'finished_at_utc':datetime.now(timezone.utc).isoformat(),
        'python':platform.python_version(),
        'packages':{n:importlib.metadata.version(n) for n in ['numpy','pandas','scipy','kiwipiepy','kiwipiepy-model']},
        'input_sha256':before,'input_files_unchanged':unchanged,
        'participants':28,'tasks':84,'text_metric_rows':252,'meaning_code_rows':802,
        'generated_tables':len(list(tables.glob('*.csv'))),'nlp_recomputed':False,'manual_coding_changed':False,
        'rq1':rq1,'rq2':rq2,'scoped_reference_comparison':{'rq1':check1,'rq2':check2},
        'canonical_public_bootstrap_validation':{'available':canonical.is_file(),'passed':canonical_pass},
        'limits':['Previously reported omnibus adjusted p-values are retained only in reference tables, excluded from recalculation and from independent-agreement claims.',
                  'Learner text is not distributed. Public numerical replay does not remeasure NLP features.',
                  'Computational agreement does not establish annotation validity or intercoder reliability.',
                  'Finite BCa confidence limits may differ from original references because public participant order is pseudonymized; the separate public-order reference is checked.']}
    (out/'validation_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'status':status,'generated_tables':report['generated_tables'],'rq1_scoped_passed':check1['passed'],
        'rq2_deterministic_passed':check2['deterministic_statistics_passed'],'canonical_public_bootstrap_passed':canonical_pass,
        'reported_omnibus_adjusted_p_recalculated':False,'input_files_unchanged':unchanged},indent=2))
    if not ok:raise SystemExit(1)
if __name__=='__main__':main()
