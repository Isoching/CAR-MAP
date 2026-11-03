"""Replay deterministic examples from the archived LP matrix families."""
from pathlib import Path
import argparse,json
import numpy as np
from scipy.optimize import linprog

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--report',type=Path,default=ROOT/'reproduced/matrix_replay.json')
args=parser.parse_args();results=[]
families=[
 ('data/controls/CONTROL_LP_MATRICES.json','control'),
 ('data/main/Figure2/EXPORTED_LP_MODELS.json','ghg'),
 ('data/main/Figure2/PANEL_C_LP_MODELS.json','ghg'),
 ('data/main/Figure3/EXPORTED_LP_MODELS.json','ghg'),
 ('data/supplement/Figures_S1_S2/EXPORTED_JOINT_LP_EVIDENCE.json','joint'),
 ('data/main/Figure4/panel_a/ALL_POLICY_LP_MODELS.json','private'),
 ('data/main/Figure4/panel_b/ALL_POLICY_LP_MODELS.json','private'),
 ('data/main/Figure4/panel_c/PANEL_C_ALL_POLICY_LP_MODELS.json','private'),
]
for file,kind in families:
    data=json.loads((ROOT/file).read_text())
    indices=sorted(set([0,len(data)//4,len(data)//2,3*len(data)//4,len(data)-1]))
    for i in indices:
        r=data[i];p=r['model'] if kind=='joint' else r
        A=np.array(p['A']);b=np.array(p['b']);bounds=p['bounds']
        if kind=='control':c=np.array(p['primary_objective_vector'])
        else:c=np.array(p['vectors']['private_increment' if kind=='private' else 'ghg_increment'])
        if kind in ['ghg','joint'] and 'resource_budget' not in p['constraint_names']:
            allowance=r['extra_budget_MUSD'] if kind=='joint' else p['scenario']['budget_per_source_t']*p['fixed_source_t']/1e6
            A=np.vstack([A,p['vectors']['gross_increment']]);b=np.append(b,allowance)
        x=linprog(c,A_ub=A,b_ub=b,bounds=bounds,method='highs',
            options={'primal_feasibility_tolerance':1e-8,'dual_feasibility_tolerance':1e-8})
        assert x.success,(file,i,x.message)
        primal=max(0.,float(np.max(A@x.x-b)))
        entry=dict(file=file,index=i,records_in_family=len(data),primary_objective=float(x.fun),primal_violation=primal)
        assert primal<=1e-4
        if kind=='control':
            gap=p['saved_refined_objective']-x.fun
            tol=1.1e-8*max(1,abs(x.fun))+1e-7
            assert -tol<=gap<=tol,(file,i,gap,tol)
            entry.update(saved_refined_minus_replayed_primary=float(gap),allowed_lexicographic_gap=tol)
        if kind=='joint':
            gap=r['full_solution']['primary_objective']-x.fun
            assert abs(gap)<=1e-7*max(1,abs(x.fun))
            entry['saved_primary_minus_replayed_primary']=gap
        results.append(entry)
    del data
report=dict(status='PASS',scope='Five deterministic matrix examples per family, selected at the first, quarter, middle, three-quarter and last record.',
    matrix_examples=len(results),families=len(families),results=results)
args.report.parent.mkdir(parents=True,exist_ok=True);args.report.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
print('PASS:',len(results),'matrix examples across',len(families),'families')
