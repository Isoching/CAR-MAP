"""Compare a fresh control run with the full-precision submission record."""
from pathlib import Path
from collections import Counter
import argparse, hashlib, json, math

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--candidate',type=Path,default=ROOT/'reproduced/controls')
parser.add_argument('--report',type=Path,default=ROOT/'reproduced/control_comparison.json')
args=parser.parse_args()
candidate=args.candidate.resolve(); published=ROOT/'data/controls'
original=json.loads((published/'FULL_CONTROL_SOLUTIONS.json').read_text())
fresh=json.loads((candidate/'FULL_CONTROL_SOLUTIONS.json').read_text())
def key(r):return r['label'],r.get('storage_only',False)
saved={key(r):r for r in original};rerun={key(r):r for r in fresh}
assert len(original)==len(fresh)==1700
assert len(saved)==len(rerun)==1700 and saved.keys()==rerun.keys()
differences=[];maxima={};count=0
for k,row in saved.items():
    other=rerun[k]
    assert row['scenario']==other['scenario'] and row['region']==other['region']
    a,b=row['metrics'],other['metrics']
    assert a.keys()==b.keys()
    for field,x in a.items():
        y=b[field]
        if isinstance(x,(float,int)) and not isinstance(x,bool):
            assert math.isfinite(x) and math.isfinite(y)
            delta=abs(x-y);maxima[field]=max(maxima.get(field,0),delta);count+=1
            tol=1.0 if 'USD' in field else 0.05 if field.endswith(('_t','_tCO2e','_GJ')) else 1e-5
            if delta>tol+1e-9*max(abs(x),abs(y)):differences.append(dict(case=k,field=field,saved=x,rerun=y))
    assert a['feasible'] and b['feasible']
hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in candidate.iterdir() if p.is_file()}
identical=[p.name for p in published.iterdir() if p.is_file() and p.name in hashes
           and hashlib.sha256(p.read_bytes()).hexdigest()==hashes[p.name]]
report=dict(status='PASS' if not differences else 'FAIL',solutions_compared=1700,
    numeric_metric_comparisons=count,files_byte_identical=sorted(identical),
    maximum_metric_differences=maxima,differences_outside_tolerance=differences,
    tolerance='USD metrics: 1 USD absolute. Tonnes and service GJ: 0.05 absolute. Other scalar metrics: 1e-5 absolute. Relative allowance 1e-9.',
    note='Byte identity is additionally reported. These tolerances accommodate solver lexicographic and floating-point differences across platforms.')
args.report.parent.mkdir(parents=True,exist_ok=True)
args.report.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
print(json.dumps({k:v for k,v in report.items() if k not in ['maximum_metric_differences','differences_outside_tolerance']},indent=2))
assert not differences

