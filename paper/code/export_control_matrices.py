"""Rebuild explicit LP matrices for every retained control solution."""
from pathlib import Path
from dataclasses import asdict
import argparse, hashlib, json, sys
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'model'))
from allocation import Scenario,build
from engineering import Engineering

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output',type=Path,default=ROOT/'reproduced/CONTROL_LP_MATRICES.json')
args=parser.parse_args()
records=json.loads((ROOT/'data/controls/FULL_CONTROL_SOLUTIONS.json').read_text())
summary=json.loads((ROOT/'data/controls/SUMMARY.json').read_text())
for file,expected in summary['frozen_model_hashes'].items():
    assert hashlib.sha256((ROOT/file).read_bytes()).hexdigest()==expected,file

out=[];max_violation=0.
for i,r in enumerate(records):
    sc=dict(r['scenario']);sc['engineering']=Engineering(**sc['engineering'])
    p=build(r['region'],Scenario(**sc))
    objective='private' if r['label'].startswith('calibrated_') else 'ghg'
    c=p['vectors']['private_increment' if objective=='private' else 'ghg_increment']
    A=p['A'].copy();b=p['b'].copy();constraints=list(p['constraint_names']);units=list(p['constraint_units'])
    if objective=='ghg':
        A=np.vstack([A,p['vectors']['gross_increment']])
        b=np.append(b,p['scenario']['budget_per_source_t']*p['fixed_source_t']/1e6)
        constraints.append('resource_budget');units.append('MUSD/year')
    bounds=list(p['bounds'])
    if r.get('storage_only',False):
        bounds=[bound if name.endswith('::storage') else (0.,0.) for name,bound in zip(p['names'],bounds)]
    x=np.array([r['metrics']['flows'][name]/1000 for name in p['names']])
    violation=max(0.,float(np.max(A@x-b)),float(np.max(-x)))
    for value,(lo,hi) in zip(x,bounds):
        violation=max(violation,max(0,lo-value) if lo is not None else 0,max(0,value-hi) if hi is not None else 0)
    assert violation<=1e-4
    max_violation=max(max_violation,violation)
    out.append(dict(solution_index=i,label=r['label'],region=r['region'],storage_only=r.get('storage_only',False),
        scenario=r['scenario'],names=p['names'],primary_objective_kind=objective,
        primary_objective_vector=c.tolist(),secondary_objective_vector=p['vectors']['gross_increment'].tolist(),
        A=A.tolist(),b=b.tolist(),bounds=bounds,constraint_names=constraints,constraint_units=units,
        variable_units='kt source CO2/y for route variables and ktH2/y for qualified_H2',
        objective_units='ktCO2e/y' if objective=='ghg' else 'MUSD/y',
        saved_refined_x=x.tolist(),saved_refined_objective=float(c@x),
        lexicographic_tolerance='1e-8 * max(1, abs(primary optimum)) in internal objective units',
        baseline_GHG_kt=p['baseline_GHG_kt'],baseline_resource_MUSD=p['baseline_resource_MUSD'],fixed_source_t=p['fixed_source_t']))
args.output.parent.mkdir(parents=True,exist_ok=True)
args.output.write_text(json.dumps(out,indent=2,allow_nan=False)+'\n')
print(json.dumps(dict(status='PASS',matrices=len(out),max_reconstructed_saved_primal_violation=max_violation),indent=2))

